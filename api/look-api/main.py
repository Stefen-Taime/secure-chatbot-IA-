from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import os
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import redis
import hvac

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [look-api] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Look API",
    description="API pour la recherche intelligente dans les bases de données et la base vectorielle",
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
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER", "elastic")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTIC_PASSWORD", "elastic_password_123")
VECTOR_DB_HOST = os.getenv("VECTOR_DB_HOST", "qdrant")
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

# Connexion à Elasticsearch
def get_elasticsearch_client():
    try:
        es = Elasticsearch(
            f"http://{ELASTICSEARCH_HOST}:9200",
            basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD)
        )
        return es
    except Exception as e:
        logger.error(f"Erreur de connexion à Elasticsearch: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de recherche indisponible"
        )

# Connexion à Qdrant
def get_qdrant_client():
    try:
        client = QdrantClient(host=VECTOR_DB_HOST, port=6333)
        return client
    except Exception as e:
        logger.error(f"Erreur de connexion à Qdrant: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de base vectorielle indisponible"
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
            
            # Vérification des rôles (à adapter selon votre structure de rôles)
            # Cette partie peut être étendue pour vérifier des rôles spécifiques
            
            return user_info
    except httpx.RequestError:
        logger.error("Erreur de connexion au serveur d'authentification")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'authentification indisponible"
        )

# Modèles de données
class ClientSearchParams(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    numero_securite_sociale: Optional[str] = None
    numero_contrat: Optional[str] = None

class ReclamationSearchParams(BaseModel):
    client_id: Optional[int] = None
    numero_reclamation: Optional[str] = None
    statut: Optional[str] = None
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None
    type_reclamation: Optional[str] = None

class KnowledgeSearchParams(BaseModel):
    query: str
    top_k: int = 5

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int
    page: int = 1
    page_size: int = 10

# Routes API
@app.get("/")
async def root():
    return {"message": "Look API pour la recherche intelligente"}

# Endpoint de recherche dans PostgreSQL
@app.post("/clients/search", response_model=SearchResponse)
async def search_clients(
    params: ClientSearchParams,
    page: int = 1,
    page_size: int = 10,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Recherche de clients avec paramètres: {params}")
    
    # Vérification des autorisations
    if "view_client_data" not in user_info.get("clientRoles", {}).get("chatbot-client", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé aux données clients"
        )
    
    # Construction de la requête SQL
    query = "SELECT * FROM clients WHERE 1=1"
    params_dict = params.dict(exclude_none=True)
    values = []
    
    for i, (key, value) in enumerate(params_dict.items()):
        query += f" AND {key} ILIKE %s"
        values.append(f"%{value}%")
    
    # Ajout de la pagination
    offset = (page - 1) * page_size
    query += f" LIMIT {page_size} OFFSET {offset}"
    
    # Exécution de la requête
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Requête pour le nombre total
            count_query = "SELECT COUNT(*) FROM clients WHERE 1=1"
            for i, (key, value) in enumerate(params_dict.items()):
                count_query += f" AND {key} ILIKE %s"
            
            cursor.execute(count_query, values)
            total = cursor.fetchone()["count"]
            
            # Requête principale
            cursor.execute(query, values)
            results = cursor.fetchall()
            
            # Anonymisation des données sensibles
            for result in results:
                if "numero_securite_sociale" in result:
                    result["numero_securite_sociale"] = result["numero_securite_sociale"][:3] + "***********"
            
            return SearchResponse(
                results=list(results),
                total=total,
                page=page,
                page_size=page_size
            )
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de clients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recherche de clients"
        )
    finally:
        conn.close()

# Endpoint de recherche dans Elasticsearch
@app.post("/reclamations/search", response_model=SearchResponse)
async def search_reclamations(
    params: ReclamationSearchParams,
    page: int = 1,
    page_size: int = 10,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Recherche de réclamations avec paramètres: {params}")
    
    # Vérification des autorisations
    if "view_claims" not in user_info.get("clientRoles", {}).get("chatbot-client", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé aux réclamations"
        )
    
    # Construction de la requête Elasticsearch
    es = get_elasticsearch_client()
    
    query_body = {
        "query": {
            "bool": {
                "must": []
            }
        },
        "from": (page - 1) * page_size,
        "size": page_size
    }
    
    params_dict = params.dict(exclude_none=True)
    
    for key, value in params_dict.items():
        if key in ["date_debut", "date_fin"]:
            continue
        
        query_body["query"]["bool"]["must"].append({
            "match": {
                key: value
            }
        })
    
    # Ajout de la plage de dates si spécifiée
    if params.date_debut and params.date_fin:
        query_body["query"]["bool"]["must"].append({
            "range": {
                "date_reclamation": {
                    "gte": params.date_debut,
                    "lte": params.date_fin
                }
            }
        })
    
    try:
        # Vérification si l'index existe, sinon le créer
        if not es.indices.exists(index="reclamations"):
            # Création de l'index avec un mapping de base
            es.indices.create(
                index="reclamations",
                body={
                    "mappings": {
                        "properties": {
                            "client_id": {"type": "integer"},
                            "contrat_id": {"type": "integer"},
                            "numero_reclamation": {"type": "keyword"},
                            "date_reclamation": {"type": "date"},
                            "type_reclamation": {"type": "keyword"},
                            "description": {"type": "text", "analyzer": "french"},
                            "montant_demande": {"type": "float"},
                            "statut": {"type": "keyword"},
                            "date_traitement": {"type": "date"},
                            "agent_traitement": {"type": "keyword"},
                            "commentaires": {"type": "text", "analyzer": "french"}
                        }
                    }
                }
            )
            logger.info("Index 'reclamations' créé dans Elasticsearch")
        
        # Exécution de la recherche
        response = es.search(index="reclamations", body=query_body)
        
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        
        results = [hit["_source"] for hit in hits]
        
        return SearchResponse(
            results=results,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Erreur lors de la recherche de réclamations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recherche de réclamations"
        )

# Endpoint de recherche dans la base vectorielle
@app.post("/knowledge/search", response_model=SearchResponse)
async def search_knowledge(
    params: KnowledgeSearchParams,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Recherche dans la base de connaissances: {params.query}")
    
    # Connexion à Qdrant
    qdrant = get_qdrant_client()
    
    try:
        # Vérification si la collection existe
        collections = qdrant.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if "knowledge_base" not in collection_names:
            # Création de la collection si elle n'existe pas
            qdrant.create_collection(
                collection_name="knowledge_base",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            logger.info("Collection 'knowledge_base' créée dans Qdrant")
            
            # Comme la collection vient d'être créée, il n'y a pas encore de données
            return SearchResponse(
                results=[],
                total=0
            )
        
        # Simulation de recherche vectorielle
        # Dans un cas réel, il faudrait d'abord vectoriser la requête avec un modèle d'embedding
        # Ici, nous simulons des résultats pour le POC
        
        # Récupération des résultats depuis Redis (cache)
        redis_client = get_redis_client()
        cache_key = f"knowledge_search:{params.query}"
        cached_results = redis_client.get(cache_key)
        
        if cached_results:
            logger.info(f"Résultats trouvés dans le cache pour la requête: {params.query}")
            results = json.loads(cached_results)
            return SearchResponse(
                results=results,
                total=len(results)
            )
        
        # Simulation de résultats pour le POC
        # Dans un cas réel, ces résultats viendraient de la recherche vectorielle
        simulated_results = []
        
        if "remboursement" in params.query.lower():
            simulated_results = [
                {
                    "id": 1,
                    "title": "Procédure de remboursement standard",
                    "content": "Les remboursements standards sont traités dans un délai de 5 jours ouvrés...",
                    "similarity": 0.92
                },
                {
                    "id": 2,
                    "title": "Justificatifs nécessaires pour remboursement",
                    "content": "Pour obtenir un remboursement, le client doit fournir les justificatifs suivants...",
                    "similarity": 0.85
                }
            ]
        elif "contrat" in params.query.lower():
            simulated_results = [
                {
                    "id": 3,
                    "title": "Modification de contrat",
                    "content": "La procédure de modification de contrat nécessite les étapes suivantes...",
                    "similarity": 0.88
                },
                {
                    "id": 4,
                    "title": "Résiliation de contrat",
                    "content": "Les conditions de résiliation de contrat sont les suivantes...",
                    "similarity": 0.82
                }
            ]
        else:
            simulated_results = [
                {
                    "id": 5,
                    "title": "Politique générale d'AssurSanté",
                    "content": "AssurSanté s'engage à traiter toutes les demandes clients dans un délai de...",
                    "similarity": 0.75
                }
            ]
        
        # Stockage des résultats dans Redis (cache)
        redis_client.setex(
            cache_key,
            3600,  # TTL de 1 heure
            json.dumps(simulated_results)
        )
        
        return SearchResponse(
            results=simulated_results,
            total=len(simulated_results)
        )
    except Exception as e:
        logger.error(f"Erreur lors de la recherche dans la base de connaissances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recherche dans la base de connaissances"
        )

# Endpoint de recherche combinée
@app.post("/search/combined")
async def combined_search(
    query: str,
    client_id: Optional[int] = None,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Recherche combinée: {query}, client_id: {client_id}")
    
    results = {
        "client_info": None,
        "reclamations": [],
        "knowledge": []
    }
    
    # Si un client_id est fourni, récupérer ses informations
    if client_id:
        conn = get_postgres_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
                client = cursor.fetchone()
                
                if client:
                    # Anonymisation des données sensibles
                    if "numero_securite_sociale" in client:
                        client["numero_securite_sociale"] = client["numero_securite_sociale"][:3] + "***********"
                    
                    results["client_info"] = client
                    
                    # Récupération des contrats du client
                    cursor.execute("SELECT * FROM contrats WHERE client_id = %s", (client_id,))
                    contrats = cursor.fetchall()
                    results["client_info"]["contrats"] = list(contrats)
        finally:
            conn.close()
    
    # Recherche dans les réclamations via Elasticsearch
    es = get_elasticsearch_client()
    
    try:
        query_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["description", "commentaires", "type_reclamation"]
                            }
                        }
                    ]
                }
            },
            "size": 5
        }
        
        if client_id:
            query_body["query"]["bool"]["must"].append({
                "term": {
                    "client_id": client_id
                }
            })
        
        # Vérification si l'index existe
        if es.indices.exists(index="reclamations"):
            response = es.search(index="reclamations", body=query_body)
            hits = response["hits"]["hits"]
            results["reclamations"] = [hit["_source"] for hit in hits]
    except Exception as e:
        logger.error(f"Erreur lors de la recherche Elasticsearch: {e}")
    
    # Recherche dans la base de connaissances
    try:
        knowledge_results = await search_knowledge(
            KnowledgeSearchParams(query=query, top_k=3),
            user_info=user_info
        )
        results["knowledge"] = knowledge_results.results
    except Exception as e:
        logger.error(f"Erreur lors de la recherche dans la base de connaissances: {e}")
    
    # Journalisation de l'action
    logger.info(f"Recherche combinée effectuée par {user_info.get('preferred_username', 'utilisateur inconnu')}")
    
    return results

# Démarrage de l'application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
