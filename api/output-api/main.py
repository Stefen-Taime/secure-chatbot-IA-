from fastapi import FastAPI, Depends, HTTPException, Security, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import httpx
import os
import json
import logging
from datetime import datetime
import hvac
import jinja2
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [output-api] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Output API",
    description="API pour structurer les réponses en formats standardisés (JSON/XML)",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration de la sécurité
security = HTTPBearer()

# Variables d'environnement
KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST", "keycloak")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "assursante")
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_DEV_ROOT_TOKEN_ID", "vault_root_token_123")

# Connexion à Vault
def get_vault_client():
    try:
        client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
        return client
    except Exception as e:
        logger.error(f"Erreur de connexion à Vault: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de gestion des secrets indisponible"
        )

# Vérification du token JWT
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    
    try:
        # Vérification du token auprès de Keycloak
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://{KEYCLOAK_HOST}:8080/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalide ou expiré"
                )
            
            user_info = response.json()
            
            return user_info
    except httpx.RequestError:
        logger.error("Erreur de connexion au serveur d'authentification")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'authentification indisponible"
        )

# Modèles de données
class OutputFormat(BaseModel):
    format: str = Field(..., description="json, xml, text")
    template: Optional[str] = None
    pretty_print: bool = True

class OutputData(BaseModel):
    data: Dict[str, Any]
    format: OutputFormat
    metadata: Optional[Dict[str, Any]] = None

class StandardResponse(BaseModel):
    status: str
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

# Environnement Jinja2 pour les templates
template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    autoescape=jinja2.select_autoescape(["html", "xml"])
)

# Routes API
@app.get("/")
async def root():
    return {"message": "Output API pour structurer les réponses"}

# Middleware pour capturer les exceptions et les formater selon le standard
@app.middleware("http")
async def format_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        # Récupération du format préféré depuis les headers
        preferred_format = request.headers.get("Accept", "application/json")
        
        # Préparation de la réponse d'erreur
        error_response = StandardResponse(
            status="error",
            code=getattr(e, "status_code", 500),
            message=str(e),
            metadata={
                "timestamp": datetime.now().isoformat(),
                "path": request.url.path
            }
        )
        
        # Formatage selon le format préféré
        if "application/xml" in preferred_format:
            xml_content = dicttoxml(
                error_response.dict(exclude_none=True),
                custom_root="response",
                attr_type=False
            )
            pretty_xml = parseString(xml_content).toprettyxml()
            return Response(content=pretty_xml, media_type="application/xml")
        else:
            return JSONResponse(
                status_code=getattr(e, "status_code", 500),
                content=error_response.dict(exclude_none=True)
            )

# Endpoint pour formater une réponse
@app.post("/format")
async def format_output(
    output_data: OutputData,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Formatage de la réponse en {output_data.format.format}")
    
    # Préparation des métadonnées standard
    if not output_data.metadata:
        output_data.metadata = {}
    
    output_data.metadata.update({
        "timestamp": datetime.now().isoformat(),
        "formatted_by": user_info.get("preferred_username"),
        "format": output_data.format.format
    })
    
    # Préparation de la réponse standard
    standard_response = StandardResponse(
        status="success",
        code=200,
        message="Réponse formatée avec succès",
        data=output_data.data,
        metadata=output_data.metadata
    )
    
    # Formatage selon le format demandé
    if output_data.format.format.lower() == "xml":
        # Conversion en XML
        xml_content = dicttoxml(
            standard_response.dict(exclude_none=True),
            custom_root="response",
            attr_type=False
        )
        
        # Pretty print si demandé
        if output_data.format.pretty_print:
            xml_content = parseString(xml_content).toprettyxml()
        
        return Response(content=xml_content, media_type="application/xml")
    
    elif output_data.format.format.lower() == "text":
        # Si un template est spécifié, utiliser Jinja2 pour le rendu
        if output_data.format.template:
            try:
                template = template_env.get_template(output_data.format.template)
                text_content = template.render(**output_data.data)
                return Response(content=text_content, media_type="text/plain")
            except jinja2.exceptions.TemplateNotFound:
                # Si le template n'existe pas, utiliser un template par défaut
                text_content = f"Réponse formatée en texte:\n\n"
                for key, value in output_data.data.items():
                    text_content += f"{key}: {value}\n"
                return Response(content=text_content, media_type="text/plain")
        else:
            # Sans template, formater simplement en texte
            text_content = f"Réponse formatée en texte:\n\n"
            for key, value in output_data.data.items():
                text_content += f"{key}: {value}\n"
            return Response(content=text_content, media_type="text/plain")
    
    else:  # Par défaut, JSON
        # Pretty print si demandé
        if output_data.format.pretty_print:
            return JSONResponse(
                content=standard_response.dict(exclude_none=True),
                media_type="application/json"
            )
        else:
            return JSONResponse(
                content=standard_response.dict(exclude_none=True),
                media_type="application/json"
            )

# Endpoint pour formater une réponse client
@app.post("/format/client-response")
async def format_client_response(
    client_data: Dict[str, Any],
    format: str = "json",
    pretty_print: bool = True,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Formatage d'une réponse client en {format}")
    
    # Anonymisation des données sensibles
    if "numero_securite_sociale" in client_data:
        client_data["numero_securite_sociale"] = client_data["numero_securite_sociale"][:3] + "***********"
    
    # Préparation de la réponse
    response_data = {
        "client": client_data,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "formatted_by": user_info.get("preferred_username")
        }
    }
    
    # Utilisation de l'endpoint de formatage général
    output_data = OutputData(
        data=response_data,
        format=OutputFormat(
            format=format,
            pretty_print=pretty_print
        )
    )
    
    return await format_output(output_data, user_info)

# Endpoint pour formater une réponse de réclamation
@app.post("/format/claim-response")
async def format_claim_response(
    claim_data: Dict[str, Any],
    format: str = "json",
    pretty_print: bool = True,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Formatage d'une réponse de réclamation en {format}")
    
    # Préparation de la réponse
    response_data = {
        "claim": claim_data,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "formatted_by": user_info.get("preferred_username")
        }
    }
    
    # Utilisation de l'endpoint de formatage général
    output_data = OutputData(
        data=response_data,
        format=OutputFormat(
            format=format,
            pretty_print=pretty_print
        )
    )
    
    return await format_output(output_data, user_info)

# Endpoint pour formater une réponse d'email
@app.post("/format/email-template")
async def format_email_template(
    email_data: Dict[str, Any],
    template_name: str,
    format: str = "text",
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Formatage d'un template d'email avec {template_name}")
    
    # Vérification que le template existe
    template_path = f"templates/{template_name}.j2"
    if not os.path.exists(template_path):
        # Créer un template par défaut si celui demandé n'existe pas
        os.makedirs("templates", exist_ok=True)
        with open(template_path, "w") as f:
            f.write("""
Bonjour {{ destinataire_nom }},

{{ contenu }}

Cordialement,
{{ expediteur_nom }}
AssurSanté
            """.strip())
    
    # Utilisation de l'endpoint de formatage général
    output_data = OutputData(
        data=email_data,
        format=OutputFormat(
            format=format,
            template=f"{template_name}.j2",
            pretty_print=True
        )
    )
    
    return await format_output(output_data, user_info)

# Endpoint pour lister les templates disponibles
@app.get("/templates")
async def list_templates(
    user_info: dict = Depends(verify_token)
):
    logger.info("Listage des templates disponibles")
    
    # Vérification que le dossier templates existe
    os.makedirs("templates", exist_ok=True)
    
    # Récupération de la liste des templates
    templates = []
    for filename in os.listdir("templates"):
        if filename.endswith(".j2"):
            templates.append(filename[:-3])  # Enlever l'extension .j2
    
    return {
        "templates": templates,
        "count": len(templates)
    }

# Endpoint pour créer ou mettre à jour un template
@app.post("/templates/{template_name}")
async def create_update_template(
    template_name: str,
    template_content: str,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Création/mise à jour du template {template_name}")
    
    # Vérification que le dossier templates existe
    os.makedirs("templates", exist_ok=True)
    
    # Écriture du template
    template_path = f"templates/{template_name}.j2"
    with open(template_path, "w") as f:
        f.write(template_content)
    
    return {
        "message": f"Template {template_name} créé/mis à jour avec succès",
        "template_name": template_name
    }

# Démarrage de l'application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
