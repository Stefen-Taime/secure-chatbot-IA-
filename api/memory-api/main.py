from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import os
import json
import logging
from datetime import datetime, timedelta
import uuid
import redis
import hvac

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [memory-api] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Memory API",
    description="API pour gérer le contexte des conversations et l'historique",
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
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "redis_password_123")
KEYCLOAK_HOST = os.getenv("KEYCLOAK_HOST", "keycloak")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "assursante")
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_DEV_ROOT_TOKEN_ID", "vault_root_token_123")

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

# Modèles de données
class ConversationMessage(BaseModel):
    role: str = Field(..., description="user, assistant, system")
    content: str
    timestamp: Optional[datetime] = None

class ConversationCreate(BaseModel):
    client_id: Optional[int] = None
    initial_context: Optional[Dict[str, Any]] = None
    initial_messages: Optional[List[ConversationMessage]] = None

class ConversationUpdate(BaseModel):
    messages: List[ConversationMessage]
    context_updates: Optional[Dict[str, Any]] = None

class ContextItem(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None  # Durée de vie en secondes

# Routes API
@app.get("/")
async def root():
    return {"message": "Memory API pour la gestion du contexte et de l'historique"}

# Endpoint pour créer une nouvelle conversation
@app.post("/conversations")
async def create_conversation(
    conversation: ConversationCreate,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Création d'une nouvelle conversation")
    
    # Génération d'un ID unique pour la conversation
    conversation_id = str(uuid.uuid4())
    
    # Préparation des données de la conversation
    conversation_data = {
        "id": conversation_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "client_id": conversation.client_id,
        "agent_id": user_info.get("sub"),
        "agent_username": user_info.get("preferred_username"),
        "messages": [],
        "context": conversation.initial_context or {}
    }
    
    # Ajout des messages initiaux s'ils existent
    if conversation.initial_messages:
        for msg in conversation.initial_messages:
            message_data = msg.dict()
            if not message_data.get("timestamp"):
                message_data["timestamp"] = datetime.now().isoformat()
            conversation_data["messages"].append(message_data)
    
    # Stockage de la conversation dans Redis
    redis_client = get_redis_client()
    redis_client.set(f"conversation:{conversation_id}", json.dumps(conversation_data))
    
    # Par défaut, les conversations expirent après 30 jours
    redis_client.expire(f"conversation:{conversation_id}", 60 * 60 * 24 * 30)
    
    # Si un client_id est fourni, ajouter cette conversation à la liste des conversations du client
    if conversation.client_id:
        redis_client.sadd(f"client:{conversation.client_id}:conversations", conversation_id)
    
    # Ajouter cette conversation à la liste des conversations de l'agent
    redis_client.sadd(f"agent:{user_info.get('sub')}:conversations", conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "created_at": conversation_data["created_at"],
        "message": "Conversation créée avec succès"
    }

# Endpoint pour récupérer une conversation
@app.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Récupération de la conversation {conversation_id}")
    
    # Récupération de la conversation depuis Redis
    redis_client = get_redis_client()
    conversation_data = redis_client.get(f"conversation:{conversation_id}")
    
    if not conversation_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation non trouvée"
        )
    
    conversation = json.loads(conversation_data)
    
    # Vérification que l'agent a accès à cette conversation
    if conversation.get("agent_id") != user_info.get("sub"):
        # Vérifier si l'utilisateur est un superviseur
        if "superviseur" not in user_info.get("realmRoles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé à cette conversation"
            )
    
    return conversation

# Endpoint pour mettre à jour une conversation
@app.put("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    update: ConversationUpdate,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Mise à jour de la conversation {conversation_id}")
    
    # Récupération de la conversation depuis Redis
    redis_client = get_redis_client()
    conversation_data = redis_client.get(f"conversation:{conversation_id}")
    
    if not conversation_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation non trouvée"
        )
    
    conversation = json.loads(conversation_data)
    
    # Vérification que l'agent a accès à cette conversation
    if conversation.get("agent_id") != user_info.get("sub"):
        # Vérifier si l'utilisateur est un superviseur
        if "superviseur" not in user_info.get("realmRoles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé à cette conversation"
            )
    
    # Mise à jour des messages
    for msg in update.messages:
        message_data = msg.dict()
        if not message_data.get("timestamp"):
            message_data["timestamp"] = datetime.now().isoformat()
        conversation["messages"].append(message_data)
    
    # Mise à jour du contexte si fourni
    if update.context_updates:
        for key, value in update.context_updates.items():
            conversation["context"][key] = value
    
    # Mise à jour de la date de dernière modification
    conversation["updated_at"] = datetime.now().isoformat()
    
    # Stockage de la conversation mise à jour dans Redis
    redis_client.set(f"conversation:{conversation_id}", json.dumps(conversation))
    
    # Réinitialisation de l'expiration (30 jours)
    redis_client.expire(f"conversation:{conversation_id}", 60 * 60 * 24 * 30)
    
    return {
        "conversation_id": conversation_id,
        "updated_at": conversation["updated_at"],
        "message": "Conversation mise à jour avec succès",
        "message_count": len(conversation["messages"])
    }

# Endpoint pour récupérer les conversations d'un client
@app.get("/clients/{client_id}/conversations")
async def get_client_conversations(
    client_id: int,
    limit: int = 10,
    offset: int = 0,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Récupération des conversations du client {client_id}")
    
    # Récupération des IDs de conversation du client depuis Redis
    redis_client = get_redis_client()
    conversation_ids = redis_client.smembers(f"client:{client_id}:conversations")
    
    if not conversation_ids:
        return {
            "conversations": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
    
    # Conversion en liste et tri (les plus récentes d'abord)
    conversation_ids = list(conversation_ids)
    conversations = []
    
    # Récupération des données de conversation
    for conv_id in conversation_ids:
        conv_data = redis_client.get(f"conversation:{conv_id}")
        if conv_data:
            conv = json.loads(conv_data)
            conversations.append(conv)
    
    # Tri par date de mise à jour (les plus récentes d'abord)
    conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    # Application de la pagination
    paginated_conversations = conversations[offset:offset+limit]
    
    return {
        "conversations": paginated_conversations,
        "total": len(conversations),
        "limit": limit,
        "offset": offset
    }

# Endpoint pour récupérer les conversations d'un agent
@app.get("/agents/me/conversations")
async def get_agent_conversations(
    limit: int = 10,
    offset: int = 0,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Récupération des conversations de l'agent {user_info.get('preferred_username')}")
    
    # Récupération des IDs de conversation de l'agent depuis Redis
    redis_client = get_redis_client()
    conversation_ids = redis_client.smembers(f"agent:{user_info.get('sub')}:conversations")
    
    if not conversation_ids:
        return {
            "conversations": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
    
    # Conversion en liste
    conversation_ids = list(conversation_ids)
    conversations = []
    
    # Récupération des données de conversation
    for conv_id in conversation_ids:
        conv_data = redis_client.get(f"conversation:{conv_id}")
        if conv_data:
            conv = json.loads(conv_data)
            conversations.append(conv)
    
    # Tri par date de mise à jour (les plus récentes d'abord)
    conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    # Application de la pagination
    paginated_conversations = conversations[offset:offset+limit]
    
    return {
        "conversations": paginated_conversations,
        "total": len(conversations),
        "limit": limit,
        "offset": offset
    }

# Endpoint pour stocker un élément de contexte
@app.post("/context")
async def store_context(
    context_item: ContextItem,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Stockage d'un élément de contexte: {context_item.key}")
    
    # Stockage de l'élément de contexte dans Redis
    redis_client = get_redis_client()
    
    # Préfixe avec l'ID de l'agent pour isoler les contextes par agent
    key = f"context:{user_info.get('sub')}:{context_item.key}"
    
    # Stockage de la valeur
    redis_client.set(key, json.dumps(context_item.value))
    
    # Application du TTL si spécifié
    if context_item.ttl:
        redis_client.expire(key, context_item.ttl)
    
    return {
        "message": "Élément de contexte stocké avec succès",
        "key": context_item.key,
        "ttl": context_item.ttl
    }

# Endpoint pour récupérer un élément de contexte
@app.get("/context/{key}")
async def get_context(
    key: str,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Récupération de l'élément de contexte: {key}")
    
    # Récupération de l'élément de contexte depuis Redis
    redis_client = get_redis_client()
    
    # Préfixe avec l'ID de l'agent pour isoler les contextes par agent
    redis_key = f"context:{user_info.get('sub')}:{key}"
    
    value = redis_client.get(redis_key)
    
    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Élément de contexte '{key}' non trouvé"
        )
    
    # Récupération du TTL restant
    ttl = redis_client.ttl(redis_key)
    
    return {
        "key": key,
        "value": json.loads(value),
        "ttl_remaining": ttl if ttl > 0 else None
    }

# Endpoint pour supprimer un élément de contexte
@app.delete("/context/{key}")
async def delete_context(
    key: str,
    user_info: dict = Depends(verify_token)
):
    logger.info(f"Suppression de l'élément de contexte: {key}")
    
    # Suppression de l'élément de contexte depuis Redis
    redis_client = get_redis_client()
    
    # Préfixe avec l'ID de l'agent pour isoler les contextes par agent
    redis_key = f"context:{user_info.get('sub')}:{key}"
    
    # Vérification que la clé existe
    if not redis_client.exists(redis_key):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Élément de contexte '{key}' non trouvé"
        )
    
    # Suppression de la clé
    redis_client.delete(redis_key)
    
    return {
        "message": f"Élément de contexte '{key}' supprimé avec succès"
    }

# Démarrage de l'application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
