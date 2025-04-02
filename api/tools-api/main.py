from fastapi import FastAPI, Depends, HTTPException, Security, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import httpx
import os
import json
import logging
from datetime import datetime
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import hvac
import jinja2

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [tools-api] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Tools API",
    description="API pour exécuter des actions (création de tickets, simulation d'emails)",
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
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "assursante")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secure_password_123")
POSTGRES_DB = os.getenv("POSTGRES_DB", "assursante_db")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "redis_password_123")
KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST", "keycloak")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "assursante")
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_DEV_ROOT_TOKEN_ID", "vault_root_token_123")

# Connexion à PostgreSQL
def get_postgres_connection():
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Erreur de connexion à PostgreSQL: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de base de données indisponible"
        )

# Connexion à Redis
def get_redis_client():
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=6379,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        return r
    except Exception as e:
        logger.error(f"Erreur de connexion à Redis: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de cache indisponible"
        )

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

# Vérification des autorisations
def check_permission(user_info: dict, required_permission: str):
    client_roles = user_info.get("clientRoles", {}).get("chatbot-client", [])
    
    if required_permission not in client_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Accès non autorisé: permission {required_permission} requise"
        )

# Modèles de données
class TicketCreate(BaseModel):
    client_id: int
    sujet: str
    description: str
    priorite: str = Field(..., description="Haute, Moyenne, Basse")
    canal_communication: str = Field(..., description="Email, Téléphone, Formulaire web")

class EmailSimulation(BaseModel):
    destinataire: EmailStr
    sujet: str
    contenu: str
    client_id: Optional[int] = None
    ticket_id: Optional[int] = None
    reclamation_id: Optional[int] = None

class ReclamationCreate(BaseModel):
    client_id: int
    contrat_id: int
    type_reclamation: str
    description: str
    montant_demande: Optional[float] = None

class ReclamationUpdate(BaseModel):
    statut: Optional[str] = None
    commentaires: Optional[str] = None
    date_traitement: Optional[str] = None
    agent_traitement: Optional[str] = None

# Routes API
@app.get("/")
async def root():
    return {"message": "Tools API pour l'exécution d'actions"}

# Endpoint pour créer un ticket
@app.post("/tickets")
async def create_ticket(
    ticket: TicketCreate,
    background_tasks: BackgroundTasks,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Création d'un ticket pour le client {ticket.client_id}")
    
    # Vérification des autorisations
    check_permission(user_info, "create_tickets")
    
    # Génération d'un numéro de ticket unique
    numero_ticket = f"TIC-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:8]}"
    
    # Insertion du ticket dans la base de données
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Vérification que le client existe
            cursor.execute("SELECT id FROM clients WHERE id = %s", (ticket.client_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Client avec ID {ticket.client_id} non trouvé"
                )
            
            # Insertion du ticket
            cursor.execute(
                """
                INSERT INTO tickets 
                (client_id, numero_ticket, sujet, description, priorite, statut, agent_assignation, canal_communication)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, numero_ticket, date_creation
                """,
                (
                    ticket.client_id,
                    numero_ticket,
                    ticket.sujet,
                    ticket.description,
                    ticket.priorite,
                    "Nouveau",
                    user_info.get("preferred_username"),
                    ticket.canal_communication
                )
            )
            
            result = cursor.fetchone()
            conn.commit()
            
            # Journalisation de l'action
            cursor.execute(
                """
                INSERT INTO audit_logs
                (utilisateur, action, entite_affectee, identifiant_entite, details, adresse_ip)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_info.get("preferred_username"),
                    "Création de ticket",
                    "tickets",
                    result["id"],
                    json.dumps(ticket.dict()),
                    "127.0.0.1"  # Dans un environnement réel, récupérer l'IP du client
                )
            )
            conn.commit()
            
            # Ajout d'une tâche en arrière-plan pour simuler l'envoi d'un email de confirmation
            background_tasks.add_task(
                simulate_email,
                EmailSimulation(
                    destinataire="client@example.com",  # Dans un cas réel, récupérer l'email du client
                    sujet=f"Confirmation de création du ticket {numero_ticket}",
                    contenu=f"Votre ticket a été créé avec succès. Numéro de référence: {numero_ticket}",
                    client_id=ticket.client_id,
                    ticket_id=result["id"]
                ),
                user_info
            )
            
            return {
                "id": result["id"],
                "numero_ticket": result["numero_ticket"],
                "date_creation": result["date_creation"],
                "message": "Ticket créé avec succès"
            }
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur lors de la création du ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du ticket"
        )
    finally:
        conn.close()

# Endpoint pour créer une réclamation
@app.post("/reclamations")
async def create_reclamation(
    reclamation: ReclamationCreate,
    background_tasks: BackgroundTasks,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Création d'une réclamation pour le client {reclamation.client_id}")
    
    # Vérification des autorisations
    check_permission(user_info, "create_tickets")
    
    # Génération d'un numéro de réclamation unique
    numero_reclamation = f"REC-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:8]}"
    
    # Insertion de la réclamation dans la base de données
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Vérification que le client existe
            cursor.execute("SELECT id FROM clients WHERE id = %s", (reclamation.client_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Client avec ID {reclamation.client_id} non trouvé"
                )
            
            # Vérification que le contrat existe
            cursor.execute(
                "SELECT id FROM contrats WHERE id = %s AND client_id = %s", 
                (reclamation.contrat_id, reclamation.client_id)
            )
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contrat avec ID {reclamation.contrat_id} non trouvé pour ce client"
                )
            
            # Insertion de la réclamation
            cursor.execute(
                """
                INSERT INTO reclamations 
                (client_id, contrat_id, numero_reclamation, date_reclamation, type_reclamation, 
                description, montant_demande, statut)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, numero_reclamation, date_creation
                """,
                (
                    reclamation.client_id,
                    reclamation.contrat_id,
                    numero_reclamation,
                    datetime.now().strftime('%Y-%m-%d'),
                    reclamation.type_reclamation,
                    reclamation.description,
                    reclamation.montant_demande,
                    "Nouveau"
                )
            )
            
            result = cursor.fetchone()
            conn.commit()
            
            # Journalisation de l'action
            cursor.execute(
                """
                INSERT INTO audit_logs
                (utilisateur, action, entite_affectee, identifiant_entite, details, adresse_ip)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_info.get("preferred_username"),
                    "Création de réclamation",
                    "reclamations",
                    result["id"],
                    json.dumps(reclamation.dict()),
                    "127.0.0.1"
                )
            )
            conn.commit()
            
            # Ajout d'une tâche en arrière-plan pour simuler l'envoi d'un email de confirmation
            background_tasks.add_task(
                simulate_email,
                EmailSimulation(
                    destinataire="client@example.com",
                    sujet=f"Confirmation de création de la réclamation {numero_reclamation}",
                    contenu=f"Votre réclamation a été créée avec succès. Numéro de référence: {numero_reclamation}",
                    client_id=reclamation.client_id,
                    reclamation_id=result["id"]
                ),
                user_info
            )
            
            return {
                "id": result["id"],
                "numero_reclamation": result["numero_reclamation"],
                "date_creation": result["date_creation"],
                "message": "Réclamation créée avec succès"
            }
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur lors de la création de la réclamation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création de la réclamation"
        )
    finally:
        conn.close()

# Endpoint pour mettre à jour une réclamation
@app.put("/reclamations/{reclamation_id}")
async def update_reclamation(
    reclamation_id: int,
    update_data: ReclamationUpdate,
    background_tasks: BackgroundTasks,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Mise à jour de la réclamation {reclamation_id}")
    
    # Vérification des autorisations
    check_permission(user_info, "modify_claims")
    
    # Mise à jour de la réclamation dans la base de données
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Vérification que la réclamation existe
            cursor.execute("SELECT * FROM reclamations WHERE id = %s", (reclamation_id,))
            reclamation = cursor.fetchone()
            
            if not reclamation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Réclamation avec ID {reclamation_id} non trouvée"
                )
            
            # Construction de la requête de mise à jour
            update_fields = []
            update_values = []
            
            if update_data.statut:
                update_fields.append("statut = %s")
                update_values.append(update_data.statut)
            
            if update_data.commentaires:
                update_fields.append("commentaires = %s")
                update_values.append(update_data.commentaires)
            
            if update_data.date_traitement:
                update_fields.append("date_traitement = %s")
                update_values.append(update_data.date_traitement)
            
            if update_data.agent_traitement:
                update_fields.append("agent_traitement = %s")
                update_values.append(update_data.agent_traitement)
            
            if not update_fields:
                return {
                    "message": "Aucune modification effectuée"
                }
            
            # Exécution de la mise à jour
            query = f"UPDATE reclamations SET {', '.join(update_fields)} WHERE id = %s RETURNING *"
            update_values.append(reclamation_id)
            
            cursor.execute(query, update_values)
            updated_reclamation = cursor.fetchone()
            conn.commit()
            
            # Journalisation de l'action
            cursor.execute(
                """
                INSERT INTO audit_logs
                (utilisateur, action, entite_affectee, identifiant_entite, details, adresse_ip)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_info.get("preferred_username"),
                    "Mise à jour de réclamation",
                    "reclamations",
                    reclamation_id,
                    json.dumps(update_data.dict(exclude_none=True)),
                    "127.0.0.1"
                )
            )
            conn.commit()
            
            # Si le statut a été mis à jour à "Traitée", envoyer un email de notification
            if update_data.statut == "Traitée":
                # Récupération des informations du client
                cursor.execute("SELECT * FROM clients WHERE id = %s", (reclamation["client_id"],))
                client = cursor.fetchone()
                
                if client:
                    background_tasks.add_task(
                        simulate_email,
                        EmailSimulation(
                            destinataire=client["email"],
                            sujet=f"Mise à jour de votre réclamation {reclamation['numero_reclamation']}",
                            contenu=f"Votre réclamation a été traitée. Statut: {update_data.statut}",
                            client_id=client["id"],
                            reclamation_id=reclamation_id
                        ),
                        user_info
                    )
            
            return {
                "message": "Réclamation mise à jour avec succès",
                "reclamation": updated_reclamation
            }
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur lors de la mise à jour de la réclamation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de la réclamation"
        )
    finally:
        conn.close()

# Endpoint pour simuler l'envoi d'un email
@app.post("/emails/simulate")
async def simulate_email_endpoint(
    email: EmailSimulation,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Simulation d'envoi d'email à {email.destinataire}")
    
    # Vérification des autorisations
    check_permission(user_info, "send_emails")
    
    # Appel à la fonction de simulation d'email
    result = await simulate_email(email, user_info)
    
    return result

# Fonction pour simuler l'envoi d'un email (utilisée directement ou en tâche de fond)
async def simulate_email(email: EmailSimulation, user_info: dict):
    logger.info(f"Simulation d'envoi d'email à {email.destinataire}")
    
    # Génération d'un ID unique pour l'email
    email_id = str(uuid.uuid4())
    
    # Stockage de l'email simulé dans Redis
    redis_client = get_redis_client()
    
    email_data = {
        "id": email_id,
        "timestamp": datetime.now().isoformat(),
        "from": "noreply@assursante.example",
        "to": email.destinataire,
        "subject": email.sujet,
        "content": email.contenu,
        "client_id": email.client_id,
        "ticket_id": email.ticket_id,
        "reclamation_id": email.reclamation_id,
        "sent_by": user_info.get("preferred_username")
    }
    
    redis_client.set(f"email:{email_id}", json.dumps(email_data))
    redis_client.expire(f"email:{email_id}", 86400 * 7)  # TTL de 7 jours
    
    # Journalisation de l'action dans la base de données
    conn = get_postgres_connection()
    try:
        with conn.cursor() as cursor:
            # Insertion dans la table communications si un ticket est associé
            if email.ticket_id:
                cursor.execute(
                    """
                    INSERT INTO communications
                    (ticket_id, client_id, type_communication, contenu, expediteur, destinataire)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        email.ticket_id,
                        email.client_id,
                        "Email",
                        email.contenu,
                        "noreply@assursante.example",
                        email.destinataire
                    )
                )
            
            # Journalisation dans audit_logs
            cursor.execute(
                """
                INSERT INTO audit_logs
                (utilisateur, action, entite_affectee, identifiant_entite, details, adresse_ip)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_info.get("preferred_username"),
                    "Simulation d'email",
                    "emails",
                    email_id,
                    json.dumps({
                        "destinataire": email.destinataire,
                        "sujet": email.sujet,
                        "client_id": email.client_id,
                        "ticket_id": email.ticket_id,
                        "reclamation_id": email.reclamation_id
                    }),
                    "127.0.0.1"
                )
            )
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Erreur lors de la journalisation de l'email: {e}")
    finally:
        conn.close()
    
    return {
        "message": "Email simulé avec succès",
        "email_id": email_id,
        "timestamp": email_data["timestamp"]
    }

# Endpoint pour récupérer les emails simulés
@app.get("/emails/simulated")
async def get_simulated_emails(
    client_id: Optional[int] = None,
    ticket_id: Optional[int] = None,
    reclamation_id: Optional[int] = None,
    user_info: dict = Depends(verify_token)
):
    logger.info("Récupération des emails simulés")
    
    # Vérification des autorisations
    check_permission(user_info, "view_client_data")
    
    # Récupération des emails depuis Redis
    redis_client = get_redis_client()
    
    # Récupération de toutes les clés d'emails
    email_keys = redis_client.keys("email:*")
    emails = []
    
    for key in email_keys:
        email_data = json.loads(redis_client.get(key))
        
        # Filtrage selon les paramètres
        if client_id and email_data.get("client_id") != client_id:
            continue
        
        if ticket_id and email_data.get("ticket_id") != ticket_id:
            continue
        
        if reclamation_id and email_data.get("reclamation_id") != reclamation_id:
            continue
        
        emails.append(email_data)
    
    # Tri par date (du plus récent au plus ancien)
    emails.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "emails": emails,
        "count": len(emails)
    }

# Démarrage de l'application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
