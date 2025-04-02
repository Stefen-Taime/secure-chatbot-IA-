# Documentation des API du POC de Chatbot IA pour AssurSanté

Ce document détaille les différentes API du POC de Chatbot IA pour AssurSanté, leurs endpoints, paramètres et réponses.

## Table des matières

1. [Look API](#look-api)
2. [Tools API](#tools-api)
3. [Memory API](#memory-api)
4. [Output API](#output-api)
5. [Authentification](#authentification)
6. [Codes d'erreur](#codes-derreur)
7. [Modèles de données](#modèles-de-données)

## Look API

La Look API est responsable de la recherche intelligente dans différentes sources de données.

### Base URL

```
https://api.assursante.example/look/v1
```

### Endpoints

#### Recherche client

```
GET /clients/search
```

Recherche des clients dans la base de données.

**Paramètres de requête**

| Paramètre | Type   | Requis | Description                                |
|-----------|--------|--------|--------------------------------------------|
| query     | string | Oui    | Terme de recherche (nom, prénom, numéro)   |
| limit     | int    | Non    | Nombre maximum de résultats (défaut: 10)   |
| offset    | int    | Non    | Offset pour la pagination (défaut: 0)      |

**Exemple de requête**

```
GET /clients/search?query=dupont&limit=5
```

**Exemple de réponse**

```json
{
  "status": "success",
  "count": 2,
  "total": 2,
  "data": [
    {
      "id": 42,
      "nom": "Dupont",
      "prenom": "Jean",
      "email": "jean.dupont@example.com",
      "telephone": "0123456789",
      "numero_securite_sociale": "1***********12",
      "contrats": [
        {
          "id": 123,
          "numero_contrat": "CONT-2023-042",
          "type_contrat": "Santé Famille",
          "niveau_couverture": "Premium",
          "statut": "Actif"
        }
      ]
    },
    {
      "id": 43,
      "nom": "Dupont",
      "prenom": "Marie",
      "email": "marie.dupont@example.com",
      "telephone": "0123456790",
      "numero_securite_sociale": "2***********34",
      "contrats": [
        {
          "id": 124,
          "numero_contrat": "CONT-2023-043",
          "type_contrat": "Santé Individuelle",
          "niveau_couverture": "Confort",
          "statut": "Actif"
        }
      ]
    }
  ]
}
```

#### Recherche de réclamations

```
GET /claims/search
```

Recherche des réclamations dans Elasticsearch.

**Paramètres de requête**

| Paramètre  | Type   | Requis | Description                                |
|------------|--------|--------|--------------------------------------------|
| query      | string | Oui    | Terme de recherche                         |
| client_id  | int    | Non    | Filtrer par ID client                      |
| status     | string | Non    | Filtrer par statut                         |
| date_from  | string | Non    | Date de début (format: YYYY-MM-DD)         |
| date_to    | string | Non    | Date de fin (format: YYYY-MM-DD)           |
| limit      | int    | Non    | Nombre maximum de résultats (défaut: 10)   |
| offset     | int    | Non    | Offset pour la pagination (défaut: 0)      |

**Exemple de requête**

```
GET /claims/search?query=remboursement&client_id=42&status=en_cours
```

**Exemple de réponse**

```json
{
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
      "description": "Je n'ai toujours pas reçu le remboursement de ma consultation chez le spécialiste du 01/03/2024.",
      "montant_demande": 75.00,
      "agent_traitement": "Martin Sophie"
    }
  ]
}
```

#### Recherche dans la base de connaissances

```
GET /knowledge/search
```

Recherche sémantique dans la base de connaissances vectorielle.

**Paramètres de requête**

| Paramètre  | Type   | Requis | Description                                |
|------------|--------|--------|--------------------------------------------|
| query      | string | Oui    | Question ou terme de recherche             |
| category   | string | Non    | Filtrer par catégorie                      |
| limit      | int    | Non    | Nombre maximum de résultats (défaut: 5)    |
| threshold  | float  | Non    | Seuil de similarité (défaut: 0.7)          |

**Exemple de requête**

```
GET /knowledge/search?query=remboursement%20lunettes&category=remboursements
```

**Exemple de réponse**

```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": "kb-123",
      "title": "Remboursement des lunettes et lentilles",
      "category": "Remboursements",
      "content": "Les lunettes et lentilles sont remboursées selon les conditions suivantes:\n- Contrat Essentiel: remboursement à 100% du tarif de convention\n- Contrat Confort: remboursement à 100% du tarif de convention + 100€ tous les 2 ans\n- Contrat Premium: remboursement à 100% du tarif de convention + 200€ tous les ans",
      "similarity_score": 0.92
    },
    {
      "id": "kb-124",
      "title": "Réforme 100% Santé et équipements optiques",
      "category": "Remboursements",
      "content": "La réforme 100% Santé garantit un remboursement intégral de certains équipements optiques. Les assurés peuvent choisir entre des équipements du panier 100% Santé (sans reste à charge) ou des équipements à tarifs libres (avec reste à charge selon le niveau de garantie).",
      "similarity_score": 0.85
    }
  ]
}
```

#### Recherche combinée

```
GET /combined-search
```

Recherche dans toutes les sources de données et combine les résultats.

**Paramètres de requête**

| Paramètre  | Type   | Requis | Description                                |
|------------|--------|--------|--------------------------------------------|
| query      | string | Oui    | Terme de recherche                         |
| client_id  | int    | Non    | Contexte client                            |
| limit      | int    | Non    | Nombre maximum de résultats (défaut: 10)   |

**Exemple de requête**

```
GET /combined-search?query=remboursement%20optique&client_id=42
```

**Exemple de réponse**

```json
{
  "status": "success",
  "client_context": {
    "id": 42,
    "nom": "Dupont",
    "prenom": "Jean",
    "contrats": [
      {
        "type_contrat": "Santé Famille",
        "niveau_couverture": "Premium"
      }
    ]
  },
  "knowledge_results": [
    {
      "id": "kb-123",
      "title": "Remboursement des lunettes et lentilles",
      "category": "Remboursements",
      "snippet": "Les lunettes et lentilles sont remboursées selon les conditions suivantes: [...] Contrat Premium: remboursement à 100% du tarif de convention + 200€ tous les ans",
      "similarity_score": 0.92
    }
  ],
  "claims_results": [
    {
      "id": 790,
      "numero_reclamation": "REC-2024-124",
      "type_reclamation": "Remboursement",
      "statut": "Traité",
      "description": "Demande de remboursement pour lunettes de vue",
      "date_reclamation": "2024-02-10"
    }
  ],
  "relevance_score": 0.89
}
```

## Tools API

La Tools API est responsable des actions métier comme la création de tickets, la gestion des réclamations, etc.

### Base URL

```
https://api.assursante.example/tools/v1
```

### Endpoints

#### Création de ticket

```
POST /tickets
```

Crée un nouveau ticket de support.

**Corps de la requête**

```json
{
  "client_id": 42,
  "sujet": "Demande d'information sur remboursement",
  "description": "Le client souhaite savoir pourquoi son remboursement optique est inférieur à ses attentes.",
  "priorite": "normale",
  "categorie": "remboursement",
  "tags": ["optique", "remboursement", "information"]
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "ticket_id": "TIC-2024-567",
    "client_id": 42,
    "sujet": "Demande d'information sur remboursement",
    "statut": "ouvert",
    "date_creation": "2024-04-01T14:30:45Z",
    "agent_assigne": "Martin Sophie",
    "priorite": "normale",
    "categorie": "remboursement",
    "tags": ["optique", "remboursement", "information"]
  }
}
```

#### Création de réclamation

```
POST /claims
```

Crée une nouvelle réclamation.

**Corps de la requête**

```json
{
  "client_id": 42,
  "type_reclamation": "Remboursement",
  "description": "Je n'ai pas reçu le remboursement pour ma consultation chez le dentiste du 15/03/2024.",
  "montant_demande": 120.50,
  "date_soins": "2024-03-15",
  "documents": ["facture.pdf", "decompte_secu.pdf"]
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "claim_id": "REC-2024-568",
    "client_id": 42,
    "type_reclamation": "Remboursement",
    "statut": "Enregistrée",
    "date_reclamation": "2024-04-01T14:32:10Z",
    "description": "Je n'ai pas reçu le remboursement pour ma consultation chez le dentiste du 15/03/2024.",
    "montant_demande": 120.50,
    "documents_recus": ["facture.pdf", "decompte_secu.pdf"],
    "delai_traitement_estime": "5 jours ouvrés"
  }
}
```

#### Mise à jour de réclamation

```
PUT /claims/{claim_id}
```

Met à jour une réclamation existante.

**Paramètres de chemin**

| Paramètre | Type   | Description                |
|-----------|--------|----------------------------|
| claim_id  | string | Identifiant de réclamation |

**Corps de la requête**

```json
{
  "statut": "En cours de traitement",
  "commentaire_interne": "Vérification des documents en cours",
  "agent_traitement": "Dubois Pierre"
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "claim_id": "REC-2024-568",
    "statut": "En cours de traitement",
    "date_mise_a_jour": "2024-04-01T14:35:22Z",
    "agent_traitement": "Dubois Pierre"
  }
}
```

#### Simulation d'envoi d'email

```
POST /emails/simulate
```

Simule l'envoi d'un email à un client.

**Corps de la requête**

```json
{
  "client_id": 42,
  "template": "confirmation_reclamation",
  "subject": "Confirmation de votre réclamation REC-2024-568",
  "variables": {
    "nom_client": "Dupont Jean",
    "numero_reclamation": "REC-2024-568",
    "type_reclamation": "Remboursement",
    "delai_traitement": "5 jours ouvrés"
  },
  "attachments": []
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "email_id": "EMAIL-2024-789",
    "client_id": 42,
    "email_to": "jean.dupont@example.com",
    "subject": "Confirmation de votre réclamation REC-2024-568",
    "template_used": "confirmation_reclamation",
    "simulation_only": true,
    "preview_text": "Bonjour Monsieur Dupont Jean, Nous confirmons la réception de votre réclamation REC-2024-568 concernant un Remboursement. Votre demande sera traitée dans un délai de 5 jours ouvrés..."
  }
}
```

## Memory API

La Memory API est responsable de la gestion du contexte des conversations.

### Base URL

```
https://api.assursante.example/memory/v1
```

### Endpoints

#### Création de session

```
POST /sessions
```

Crée une nouvelle session de conversation.

**Corps de la requête**

```json
{
  "agent_id": "agent-123",
  "client_id": 42,
  "metadata": {
    "source": "chat_web",
    "browser": "Chrome",
    "device": "desktop"
  }
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "session_id": "sess-2024-abc123",
    "agent_id": "agent-123",
    "client_id": 42,
    "created_at": "2024-04-01T14:40:15Z",
    "expires_at": "2024-04-01T15:40:15Z",
    "metadata": {
      "source": "chat_web",
      "browser": "Chrome",
      "device": "desktop"
    }
  }
}
```

#### Ajout de message

```
POST /sessions/{session_id}/messages
```

Ajoute un message à une session existante.

**Paramètres de chemin**

| Paramètre  | Type   | Description                |
|------------|--------|----------------------------|
| session_id | string | Identifiant de session     |

**Corps de la requête**

```json
{
  "role": "user",
  "content": "Bonjour, je souhaite savoir où en est ma demande de remboursement pour mes lunettes.",
  "timestamp": "2024-04-01T14:41:05Z"
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "message_id": "msg-2024-def456",
    "session_id": "sess-2024-abc123",
    "role": "user",
    "content": "Bonjour, je souhaite savoir où en est ma demande de remboursement pour mes lunettes.",
    "timestamp": "2024-04-01T14:41:05Z",
    "sequence": 1
  }
}
```

#### Récupération de l'historique

```
GET /sessions/{session_id}/messages
```

Récupère l'historique des messages d'une session.

**Paramètres de chemin**

| Paramètre  | Type   | Description                |
|------------|--------|----------------------------|
| session_id | string | Identifiant de session     |

**Paramètres de requête**

| Paramètre | Type   | Requis | Description                                |
|-----------|--------|--------|--------------------------------------------|
| limit     | int    | Non    | Nombre maximum de messages (défaut: 50)    |
| before    | string | Non    | Récupérer les messages avant cet ID        |

**Exemple de requête**

```
GET /sessions/sess-2024-abc123/messages?limit=10
```

**Exemple de réponse**

```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "message_id": "msg-2024-def456",
      "session_id": "sess-2024-abc123",
      "role": "user",
      "content": "Bonjour, je souhaite savoir où en est ma demande de remboursement pour mes lunettes.",
      "timestamp": "2024-04-01T14:41:05Z",
      "sequence": 1
    },
    {
      "message_id": "msg-2024-ghi789",
      "session_id": "sess-2024-abc123",
      "role": "assistant",
      "content": "Bonjour Monsieur Dupont, je vais vérifier l'état de votre demande de remboursement pour vos lunettes. Pouvez-vous me préciser la date approximative de votre achat ?",
      "timestamp": "2024-04-01T14:41:15Z",
      "sequence": 2
    }
  ]
}
```

#### Mise à jour du contexte

```
PUT /sessions/{session_id}/context
```

Met à jour le contexte d'une session.

**Paramètres de chemin**

| Paramètre  | Type   | Description                |
|------------|--------|----------------------------|
| session_id | string | Identifiant de session     |

**Corps de la requête**

```json
{
  "client_context": {
    "nom": "Dupont",
    "prenom": "Jean",
    "contrat": "Premium",
    "derniere_reclamation": "REC-2024-124"
  },
  "conversation_context": {
    "intent": "remboursement",
    "entities": {
      "type_soin": "optique",
      "date_achat": "2024-03-10"
    },
    "sentiment": "neutre"
  }
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "session_id": "sess-2024-abc123",
    "context_updated_at": "2024-04-01T14:42:30Z",
    "context_version": 2
  }
}
```

#### Récupération du contexte

```
GET /sessions/{session_id}/context
```

Récupère le contexte d'une session.

**Paramètres de chemin**

| Paramètre  | Type   | Description                |
|------------|--------|----------------------------|
| session_id | string | Identifiant de session     |

**Exemple de requête**

```
GET /sessions/sess-2024-abc123/context
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "session_id": "sess-2024-abc123",
    "client_context": {
      "nom": "Dupont",
      "prenom": "Jean",
      "contrat": "Premium",
      "derniere_reclamation": "REC-2024-124"
    },
    "conversation_context": {
      "intent": "remboursement",
      "entities": {
        "type_soin": "optique",
        "date_achat": "2024-03-10"
      },
      "sentiment": "neutre"
    },
    "context_updated_at": "2024-04-01T14:42:30Z",
    "context_version": 2
  }
}
```

## Output API

La Output API est responsable de la structuration et du formatage des réponses.

### Base URL

```
https://api.assursante.example/output/v1
```

### Endpoints

#### Génération de réponse structurée

```
POST /responses/generate
```

Génère une réponse structurée à partir d'un contenu brut.

**Corps de la requête**

```json
{
  "raw_content": "Le remboursement de vos lunettes a été traité le 25/03/2024 pour un montant de 185,50€. Le virement a été effectué sur votre compte et sera visible dans 2-3 jours ouvrés.",
  "format": "json",
  "template": "remboursement_info",
  "client_id": 42
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "structured_response": {
      "message_type": "remboursement_info",
      "client": {
        "id": 42,
        "nom": "Dupont",
        "prenom": "Jean"
      },
      "remboursement": {
        "type": "optique",
        "date_traitement": "2024-03-25",
        "montant": 185.50,
        "devise": "EUR",
        "methode_paiement": "virement",
        "delai_visibilite": "2-3 jours ouvrés"
      },
      "actions_possibles": [
        {
          "type": "suivi_virement",
          "label": "Suivre mon virement",
          "url": "/mon-espace/virements"
        },
        {
          "type": "contact",
          "label": "Contacter un conseiller",
          "url": "/contact"
        }
      ]
    },
    "format": "json"
  }
}
```

#### Conversion de format

```
POST /responses/convert
```

Convertit une réponse d'un format à un autre.

**Corps de la requête**

```json
{
  "content": {
    "message_type": "remboursement_info",
    "client": {
      "id": 42,
      "nom": "Dupont",
      "prenom": "Jean"
    },
    "remboursement": {
      "type": "optique",
      "date_traitement": "2024-03-25",
      "montant": 185.50,
      "devise": "EUR",
      "methode_paiement": "virement",
      "delai_visibilite": "2-3 jours ouvrés"
    }
  },
  "source_format": "json",
  "target_format": "xml"
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "converted_content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<response>\n  <message_type>remboursement_info</message_type>\n  <client>\n    <id>42</id>\n    <nom>Dupont</nom>\n    <prenom>Jean</prenom>\n  </client>\n  <remboursement>\n    <type>optique</type>\n    <date_traitement>2024-03-25</date_traitement>\n    <montant>185.50</montant>\n    <devise>EUR</devise>\n    <methode_paiement>virement</methode_paiement>\n    <delai_visibilite>2-3 jours ouvrés</delai_visibilite>\n  </remboursement>\n</response>",
    "source_format": "json",
    "target_format": "xml"
  }
}
```

#### Génération d'email à partir de template

```
POST /emails/render
```

Génère un email à partir d'un template et de variables.

**Corps de la requête**

```json
{
  "template": "confirmation_remboursement",
  "variables": {
    "nom_client": "Monsieur Dupont",
    "type_soin": "optique",
    "date_traitement": "25/03/2024",
    "montant": "185,50€",
    "methode_paiement": "virement",
    "delai_visibilite": "2-3 jours ouvrés"
  },
  "format": "html"
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "rendered_content": "<!DOCTYPE html>\n<html>\n<head>\n  <meta charset=\"UTF-8\">\n  <title>Confirmation de remboursement</title>\n</head>\n<body>\n  <h1>Confirmation de remboursement</h1>\n  <p>Bonjour Monsieur Dupont,</p>\n  <p>Nous vous confirmons que le remboursement de vos soins <strong>optique</strong> a été traité le <strong>25/03/2024</strong> pour un montant de <strong>185,50€</strong>.</p>\n  <p>Le paiement a été effectué par <strong>virement</strong> et sera visible sur votre compte dans un délai de <strong>2-3 jours ouvrés</strong>.</p>\n  <p>Pour toute question, n'hésitez pas à contacter notre service client.</p>\n  <p>Cordialement,<br>L'équipe AssurSanté</p>\n</body>\n</html>",
    "template": "confirmation_remboursement",
    "format": "html"
  }
}
```

#### Anonymisation de données sensibles

```
POST /anonymize
```

Anonymise les données sensibles dans un contenu.

**Corps de la requête**

```json
{
  "content": "Le patient Jean Dupont (numéro de sécurité sociale 175042789456712) a été diagnostiqué avec une hypertension artérielle. Son adresse est 15 rue des Lilas, 75001 Paris et son numéro de téléphone est 0123456789.",
  "anonymization_level": "strict",
  "preserve_format": true
}
```

**Exemple de réponse**

```json
{
  "status": "success",
  "data": {
    "anonymized_content": "Le patient J*** D***** (numéro de sécurité sociale 1***********12) a été diagnostiqué avec une h************* a*********. Son adresse est ** *** *** *****, ***** P**** et son numéro de téléphone est 01********.",
    "anonymization_level": "strict",
    "sensitive_data_found": {
      "personal_names": 1,
      "health_data": 1,
      "contact_info": 2,
      "id_numbers": 1
    }
  }
}
```

## Authentification

Toutes les API du POC utilisent l'authentification OAuth 2.0 via Keycloak.

### Obtention d'un token

```
POST /auth/realms/assursante/protocol/openid-connect/token
```

**Corps de la requête**

```
grant_type=password&client_id=chatbot-api&username=agent_user&password=agent_password
```

**Exemple de réponse**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJxME...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI...",
  "token_type": "bearer",
  "not-before-policy": 0,
  "session_state": "a856fb91-eabc-4158-afc0-cff21b013a5c",
  "scope": "profile email"
}
```

### Utilisation du token

Pour toutes les requêtes API, incluez le token dans l'en-tête Authorization :

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJxME...
```

## Codes d'erreur

| Code | Description                                      |
|------|--------------------------------------------------|
| 400  | Requête invalide                                 |
| 401  | Non authentifié                                  |
| 403  | Non autorisé                                     |
| 404  | Ressource non trouvée                            |
| 409  | Conflit                                          |
| 422  | Entité non traitable                             |
| 429  | Trop de requêtes                                 |
| 500  | Erreur serveur interne                           |
| 503  | Service indisponible                             |

### Format des erreurs

```json
{
  "status": "error",
  "code": 400,
  "message": "Paramètre 'query' requis",
  "details": {
    "missing_parameters": ["query"]
  },
  "request_id": "req-2024-abc123"
}
```

## Modèles de données

### Client

```json
{
  "id": 42,
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean.dupont@example.com",
  "telephone": "0123456789",
  "numero_securite_sociale": "1***********12",
  "date_naissance": "1975-04-02",
  "adresse": {
    "rue": "15 rue des Lilas",
    "code_postal": "75001",
    "ville": "Paris",
    "pays": "France"
  },
  "contrats": [
    {
      "id": 123,
      "numero_contrat": "CONT-2023-042",
      "type_contrat": "Santé Famille",
      "niveau_couverture": "Premium",
      "statut": "Actif",
      "date_debut": "2023-01-01",
      "date_fin": "2025-12-31",
      "montant_cotisation": 120.50,
      "beneficiaires": [
        {
          "id": 43,
          "nom": "Dupont",
          "prenom": "Marie",
          "relation": "Conjoint"
        },
        {
          "id": 44,
          "nom": "Dupont",
          "prenom": "Lucas",
          "relation": "Enfant"
        }
      ]
    }
  ]
}
```

### Réclamation

```json
{
  "id": 789,
  "numero_reclamation": "REC-2024-123",
  "client_id": 42,
  "type_reclamation": "Remboursement",
  "statut": "En cours",
  "date_reclamation": "2024-03-15",
  "date_traitement": null,
  "description": "Je n'ai toujours pas reçu le remboursement de ma consultation chez le spécialiste du 01/03/2024.",
  "montant_demande": 75.00,
  "documents": [
    {
      "id": "doc-456",
      "nom": "facture_consultation.pdf",
      "type": "facture",
      "date_upload": "2024-03-15T10:23:45Z"
    },
    {
      "id": "doc-457",
      "nom": "decompte_secu.pdf",
      "type": "decompte",
      "date_upload": "2024-03-15T10:24:12Z"
    }
  ],
  "commentaires": [
    {
      "id": "com-123",
      "auteur": "Système",
      "date": "2024-03-15T10:25:00Z",
      "contenu": "Réclamation créée",
      "visible_client": true
    },
    {
      "id": "com-124",
      "auteur": "Martin Sophie",
      "date": "2024-03-16T09:15:30Z",
      "contenu": "Vérification des documents en cours",
      "visible_client": false
    }
  ],
  "agent_traitement": "Martin Sophie",
  "priorite": "normale"
}
```

### Article de la base de connaissances

```json
{
  "id": "kb-123",
  "title": "Remboursement des lunettes et lentilles",
  "category": "Remboursements",
  "subcategory": "Optique",
  "content": "Les lunettes et lentilles sont remboursées selon les conditions suivantes:\n- Contrat Essentiel: remboursement à 100% du tarif de convention\n- Contrat Confort: remboursement à 100% du tarif de convention + 100€ tous les 2 ans\n- Contrat Premium: remboursement à 100% du tarif de convention + 200€ tous les ans",
  "tags": ["optique", "lunettes", "lentilles", "remboursement"],
  "date_creation": "2023-05-10T14:30:00Z",
  "date_mise_a_jour": "2024-01-15T10:45:00Z",
  "auteur": "Legrand Julie",
  "statut": "publié",
  "vector_id": "vec-123456"
}
```

### Session de conversation

```json
{
  "session_id": "sess-2024-abc123",
  "agent_id": "agent-123",
  "client_id": 42,
  "created_at": "2024-04-01T14:40:15Z",
  "updated_at": "2024-04-01T14:45:30Z",
  "expires_at": "2024-04-01T15:40:15Z",
  "status": "active",
  "messages": [
    {
      "message_id": "msg-2024-def456",
      "role": "user",
      "content": "Bonjour, je souhaite savoir où en est ma demande de remboursement pour mes lunettes.",
      "timestamp": "2024-04-01T14:41:05Z",
      "sequence": 1
    },
    {
      "message_id": "msg-2024-ghi789",
      "role": "assistant",
      "content": "Bonjour Monsieur Dupont, je vais vérifier l'état de votre demande de remboursement pour vos lunettes. Pouvez-vous me préciser la date approximative de votre achat ?",
      "timestamp": "2024-04-01T14:41:15Z",
      "sequence": 2
    }
  ],
  "context": {
    "client_context": {
      "nom": "Dupont",
      "prenom": "Jean",
      "contrat": "Premium"
    },
    "conversation_context": {
      "intent": "remboursement",
      "entities": {
        "type_soin": "optique"
      },
      "sentiment": "neutre"
    }
  },
  "metadata": {
    "source": "chat_web",
    "browser": "Chrome",
    "device": "desktop",
    "ip_anonymized": "192.168.x.x"
  }
}
```
