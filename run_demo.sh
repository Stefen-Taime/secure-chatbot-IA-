#!/bin/bash
# Script de démonstration du POC de Chatbot IA pour AssurSanté
# Ce script simule un scénario complet d'utilisation du chatbot

# Couleurs pour une meilleure lisibilité
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages avec un délai
print_message() {
  echo -e "${BLUE}[INFO]${NC} $1"
  sleep 1
}

# Fonction pour simuler une réponse du système
system_response() {
  echo -e "${GREEN}[SYSTÈME]${NC} $1"
  sleep 2
}

# Fonction pour simuler une entrée utilisateur
user_input() {
  echo -e "${YELLOW}[AGENT]${NC} $1"
  sleep 1.5
}

# Fonction pour simuler une erreur
error_message() {
  echo -e "${RED}[ERREUR]${NC} $1"
  sleep 1
}

# Vérification des prérequis
check_prerequisites() {
  print_message "Vérification des prérequis..."
  
  if ! command -v curl &> /dev/null; then
    error_message "curl n'est pas installé. Veuillez l'installer pour continuer."
    exit 1
  fi
  
  if ! command -v jq &> /dev/null; then
    error_message "jq n'est pas installé. Veuillez l'installer pour continuer."
    exit 1
  }
  
  print_message "Vérification de l'accès aux services..."
  if ! curl -s http://localhost:8080/health > /dev/null; then
    error_message "Impossible d'accéder à l'API Gateway. Assurez-vous que les services sont démarrés."
    exit 1
  fi
  
  system_response "Tous les prérequis sont satisfaits."
}

# Étape 1: Authentification de l'agent
authenticate_agent() {
  print_message "=== ÉTAPE 1: AUTHENTIFICATION DE L'AGENT ==="
  
  user_input "Connexion au système avec les identifiants agent_senior/password123"
  
  print_message "Envoi de la requête d'authentification à Keycloak..."
  
  # Simulation de la requête d'authentification
  TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJxME..."
  
  system_response "Authentification réussie. Token JWT obtenu."
  print_message "Vérification des rôles et permissions..."
  system_response "Rôle détecté: agent_senior"
  system_response "Permissions: recherche_client, création_ticket, consultation_réclamation, accès_base_connaissances"
  
  print_message "Configuration de l'en-tête d'autorisation pour les requêtes API..."
  system_response "En-tête configuré: Authorization: Bearer ${TOKEN}"
}

# Étape 2: Recherche d'informations client
search_client() {
  print_message "=== ÉTAPE 2: RECHERCHE D'INFORMATIONS CLIENT ==="
  
  user_input "Recherche du client 'Martin Sophie'"
  
  print_message "Envoi de la requête à la Look API..."
  print_message "GET /api/look/v1/clients/search?query=Martin%20Sophie"
  
  # Simulation de la réponse
  CLIENT_RESPONSE='{
    "status": "success",
    "count": 1,
    "total": 1,
    "data": [
      {
        "id": 42,
        "nom": "Martin",
        "prenom": "Sophie",
        "email": "sophie.martin@example.com",
        "telephone": "0123456789",
        "numero_securite_sociale": "2***********34",
        "contrats": [
          {
            "id": 123,
            "numero_contrat": "CONT-2023-042",
            "type_contrat": "Santé Famille",
            "niveau_couverture": "Premium",
            "statut": "Actif"
          }
        ]
      }
    ]
  }'
  
  system_response "Client trouvé: Martin Sophie (ID: 42)"
  system_response "Contrat: Santé Famille - Premium (Actif)"
  
  user_input "Recherche des réclamations récentes pour ce client"
  
  print_message "Envoi de la requête à la Look API..."
  print_message "GET /api/look/v1/claims/search?client_id=42&limit=2"
  
  # Simulation de la réponse
  CLAIMS_RESPONSE='{
    "status": "success",
    "count": 1,
    "total": 1,
    "data": [
      {
        "id": 789,
        "numero_reclamation": "REC-2024-123",
        "client_id": 42,
        "type_reclamation": "Remboursement",
        "statut": "En cours",
        "date_reclamation": "2024-03-15",
        "description": "Je n\'ai toujours pas reçu le remboursement de ma consultation chez l\'ophtalmologue du 01/03/2024.",
        "montant_demande": 95.00,
        "agent_traitement": "Dubois Pierre"
      }
    ]
  }'
  
  system_response "1 réclamation trouvée:"
  system_response "REC-2024-123: Remboursement (En cours) - 95.00€"
  system_response "Description: Je n'ai toujours pas reçu le remboursement de ma consultation chez l'ophtalmologue du 01/03/2024."
}

# Étape 3: Consultation de la base de connaissances
search_knowledge() {
  print_message "=== ÉTAPE 3: CONSULTATION DE LA BASE DE CONNAISSANCES ==="
  
  user_input "Recherche d'informations sur le remboursement des consultations ophtalmologiques pour un contrat Premium"
  
  print_message "Envoi de la requête à la Look API..."
  print_message "GET /api/look/v1/knowledge/search?query=remboursement%20ophtalmologue%20premium&limit=2"
  
  # Simulation de la réponse
  KNOWLEDGE_RESPONSE='{
    "status": "success",
    "count": 2,
    "data": [
      {
        "id": "kb-123",
        "title": "Remboursement des consultations spécialistes",
        "category": "Remboursements",
        "content": "Les consultations chez un médecin spécialiste sont remboursées selon les conditions suivantes:\n- Contrat Essentiel: remboursement à 100% du tarif de convention\n- Contrat Confort: remboursement à 100% du tarif de convention + dépassements jusqu\'à 100% du TC\n- Contrat Premium: remboursement à 100% du tarif de convention + dépassements jusqu\'à 300% du TC",
        "similarity_score": 0.92
      },
      {
        "id": "kb-124",
        "title": "Délais de remboursement standard",
        "category": "Procédures",
        "content": "Les délais de remboursement standard sont les suivants:\n- Télétransmission Carte Vitale: 3-5 jours ouvrés\n- Envoi papier avec décompte Sécurité Sociale: 5-7 jours ouvrés\n- Envoi papier sans décompte Sécurité Sociale: 2-3 semaines (délai de traitement par la Sécurité Sociale inclus)",
        "similarity_score": 0.85
      }
    ]
  }'
  
  system_response "2 articles trouvés dans la base de connaissances:"
  system_response "1. Remboursement des consultations spécialistes (Score: 0.92)"
  system_response "   Contrat Premium: remboursement à 100% du tarif de convention + dépassements jusqu'à 300% du TC"
  system_response "2. Délais de remboursement standard (Score: 0.85)"
  system_response "   Télétransmission Carte Vitale: 3-5 jours ouvrés"
}

# Étape 4: Génération d'une réponse
generate_response() {
  print_message "=== ÉTAPE 4: GÉNÉRATION D'UNE RÉPONSE ==="
  
  user_input "Génération d'une réponse pour la cliente concernant sa réclamation de remboursement"
  
  print_message "Création d'une session de conversation..."
  print_message "POST /api/memory/v1/sessions"
  
  # Simulation de la réponse
  SESSION_RESPONSE='{
    "status": "success",
    "data": {
      "session_id": "sess-2024-abc123",
      "agent_id": "agent-senior-001",
      "client_id": 42,
      "created_at": "2024-04-01T14:40:15Z"
    }
  }'
  
  system_response "Session créée: sess-2024-abc123"
  
  print_message "Mise à jour du contexte de conversation..."
  print_message "PUT /api/memory/v1/sessions/sess-2024-abc123/context"
  
  system_response "Contexte mis à jour avec les informations client et la réclamation"
  
  user_input "Requête: Pouvez-vous me dire où en est ma demande de remboursement pour ma consultation chez l'ophtalmologue?"
  
  print_message "Ajout du message utilisateur à la session..."
  print_message "POST /api/memory/v1/sessions/sess-2024-abc123/messages"
  
  print_message "Chaînage de prompts en cours..."
  print_message "1. Décomposition de la requête en sous-tâches"
  print_message "2. Recherche des informations pertinentes"
  print_message "3. Analyse du statut de la réclamation"
  print_message "4. Génération de la réponse initiale"
  
  # Simulation de la réponse du LLM
  LLM_RESPONSE="Bonjour Madame Martin,\n\nJ'ai consulté votre dossier concernant votre demande de remboursement pour votre consultation chez l'ophtalmologue du 1er mars 2024.\n\nVotre réclamation (référence REC-2024-123) est actuellement en cours de traitement par notre service de gestion. Le montant demandé de 95€ correspond bien à une consultation chez un spécialiste.\n\nAvec votre contrat Premium, vous bénéficiez d'un remboursement à 100% du tarif de convention plus les dépassements d'honoraires jusqu'à 300% du tarif conventionnel.\n\nLe délai standard de traitement est de 5-7 jours ouvrés à compter de la réception complète des documents. Votre réclamation ayant été enregistrée le 15 mars, le remboursement devrait être effectué d'ici la fin de cette semaine.\n\nSouhaitez-vous que je vous communique plus de détails sur cette réclamation?"
  
  print_message "Vérification de la conformité de la réponse..."
  print_message "Exécution du système de gating..."
  
  system_response "Vérification de conformité réussie"
  system_response "Scores: Exactitude (0.95), Protection des données (1.0), Conformité légale (1.0), Ton (0.92)"
  
  print_message "Évaluation et optimisation de la réponse..."
  
  system_response "Réponse finale générée:"
  echo -e "${GREEN}---DÉBUT DE LA RÉPONSE---${NC}"
  echo -e "$LLM_RESPONSE"
  echo -e "${GREEN}---FIN DE LA RÉPONSE---${NC}"
}

# Étape 5: Journalisation de l'interaction
log_interaction() {
  print_message "=== ÉTAPE 5: JOURNALISATION DE L'INTERACTION ==="
  
  print_message "Enregistrement de l'interaction dans les logs..."
  print_message "POST /api/tools/v1/logs"
  
  system_response "Interaction enregistrée avec succès"
  print_message "Détails de l'interaction:"
  system_response "- Agent: agent-senior-001"
  system_response "- Client: Martin Sophie (ID: 42)"
  system_response "- Session: sess-2024-abc123"
  system_response "- Type: Réclamation remboursement"
  system_response "- Durée: 2m15s"
  system_response "- Évaluation qualité: 0.94/1.0"
  
  print_message "Mise à jour du statut de la réclamation..."
  print_message "PUT /api/tools/v1/claims/789"
  
  system_response "Statut de la réclamation mis à jour: En cours de traitement → Informations fournies"
  
  print_message "Envoi d'une notification par email au client..."
  print_message "POST /api/tools/v1/emails/simulate"
  
  system_response "Email de suivi envoyé à sophie.martin@example.com"
  system_response "Objet: Suivi de votre réclamation REC-2024-123"
}

# Exécution du scénario de démonstration
main() {
  clear
  echo -e "${BLUE}==================================================${NC}"
  echo -e "${BLUE}  SCÉNARIO DE DÉMONSTRATION - CHATBOT IA ASSURSANTÉ${NC}"
  echo -e "${BLUE}==================================================${NC}"
  echo ""
  
  # Vérification des prérequis
  check_prerequisites
  
  # Étape 1: Authentification de l'agent
  authenticate_agent
  
  # Étape 2: Recherche d'informations client
  search_client
  
  # Étape 3: Consultation de la base de connaissances
  search_knowledge
  
  # Étape 4: Génération d'une réponse
  generate_response
  
  # Étape 5: Journalisation de l'interaction
  log_interaction
  
  echo ""
  echo -e "${BLUE}==================================================${NC}"
  echo -e "${GREEN}  DÉMONSTRATION TERMINÉE AVEC SUCCÈS${NC}"
  echo -e "${BLUE}==================================================${NC}"
}

# Lancement du scénario
main
