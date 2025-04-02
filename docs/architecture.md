# Architecture du POC de Chatbot IA pour AssurSanté

## Vue d'ensemble

Le POC de Chatbot IA pour AssurSanté est conçu selon une architecture API-First modulaire et légère, permettant une grande flexibilité et une maintenance facilitée. Cette architecture est composée de plusieurs couches distinctes qui interagissent entre elles pour fournir une expérience utilisateur optimale tout en garantissant la sécurité et la confidentialité des données.

## Architecture globale

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway (NGINX)                       │
└───────────────┬─────────────────┬─────────────────┬─────────────┘
                │                 │                 │
    ┌───────────▼───────┐ ┌──────▼───────┐ ┌───────▼──────┐
    │    Keycloak MFA   │ │  HashiCorp   │ │     ELK      │
    │  Authentication   │ │    Vault     │ │    Stack     │
    └───────────────────┘ └──────────────┘ └──────────────┘
                │                 │                 │
┌───────────────┴─────────────────┴─────────────────┴─────────────┐
│                       Service Bus / API Layer                    │
└───────────┬─────────────┬────────────┬────────────┬─────────────┘
            │             │            │            │
    ┌───────▼─────┐ ┌─────▼─────┐ ┌────▼─────┐ ┌────▼─────┐
    │  Look API   │ │ Tools API │ │Memory API│ │Output API│
    └───────┬─────┘ └─────┬─────┘ └────┬─────┘ └────┬─────┘
            │             │            │            │
┌───────────┴─────────────┴────────────┴────────────┴─────────────┐
│                       Data Storage Layer                         │
├─────────────┬─────────────┬────────────┬────────────────────────┤
│ PostgreSQL  │ Elasticsearch│  Qdrant   │        Redis           │
│  (RDBMS)    │  (Search)    │ (Vector DB)│      (Cache)          │
└─────────────┴─────────────┴────────────┴────────────────────────┘
```

## Composants principaux

### 1. API Gateway (NGINX)

L'API Gateway sert de point d'entrée unique pour toutes les requêtes adressées au système. Elle est responsable de :
- Routage des requêtes vers les services appropriés
- Validation des tokens JWT
- Terminaison SSL
- Rate limiting et protection contre les attaques
- Logging des requêtes

### 2. Couche d'authentification et sécurité

#### Keycloak MFA
- Gestion de l'authentification multi-facteurs
- Émission et validation des tokens JWT
- Gestion des sessions et des utilisateurs
- Implémentation du contrôle d'accès basé sur les rôles (RBAC)

#### HashiCorp Vault
- Stockage sécurisé des secrets (clés API, mots de passe)
- Gestion des certificats
- Chiffrement/déchiffrement des données sensibles

### 3. Couche de monitoring et logging

#### ELK Stack (Elasticsearch, Logstash, Kibana)
- Collecte centralisée des logs
- Analyse et visualisation des données de performance
- Alerting sur les événements critiques
- Anonymisation des données sensibles dans les logs

### 4. Couche de services API

#### Look API
- Recherche intelligente dans les données structurées (PostgreSQL)
- Recherche full-text dans les documents (Elasticsearch)
- Recherche sémantique dans la base de connaissances vectorielle (Qdrant)
- Fusion des résultats multi-sources

#### Tools API
- Création et gestion des tickets de support
- Traitement des réclamations
- Génération d'emails et de notifications
- Actions métier spécifiques au domaine de l'assurance santé

#### Memory API
- Gestion du contexte des conversations
- Stockage de l'historique des échanges
- Persistance des sessions utilisateur
- Isolation des contextes par agent

#### Output API
- Structuration des réponses (JSON, XML)
- Formatage des réponses selon des templates prédéfinis
- Personnalisation des réponses selon le profil utilisateur
- Anonymisation des données sensibles dans les réponses

### 5. Couche de stockage de données

#### PostgreSQL
- Stockage des données structurées (clients, contrats, réclamations)
- Gestion des relations entre entités
- Transactions ACID
- Historisation des modifications

#### Elasticsearch
- Indexation et recherche full-text
- Stockage des documents non structurés
- Analyse et agrégation de données

#### Qdrant
- Base de données vectorielle pour la recherche sémantique
- Stockage des embeddings de la base de connaissances
- Recherche par similarité

#### Redis
- Cache pour les données fréquemment accédées
- Stockage temporaire des sessions
- Pub/Sub pour la communication entre services
- Rate limiting

## Workflows et patterns

### 1. Chaînage de prompts
Le pattern de chaînage de prompts permet de décomposer des requêtes complexes en sous-tâches et de les traiter séquentiellement. Ce pattern est implémenté dans le module `prompt_chaining.py` et suit le workflow suivant :

1. Décomposition de la requête en sous-tâches
2. Identification des dépendances entre sous-tâches
3. Exécution séquentielle des sous-tâches
4. Synthèse des résultats intermédiaires
5. Génération de la réponse finale

### 2. Système de gating
Le système de gating vérifie la conformité des réponses avant leur envoi à l'utilisateur. Ce pattern est implémenté dans le module `gating_system.py` et suit le workflow suivant :

1. Génération d'une réponse initiale
2. Évaluation de la conformité selon plusieurs critères
3. Identification des problèmes potentiels
4. Correction automatique des problèmes détectés
5. Validation finale de la réponse

### 3. Routage vers des spécialistes humains
Le mécanisme de routage détecte quand une requête doit être transmise à un agent humain. Ce pattern est implémenté dans le module `human_routing.py` et suit le workflow suivant :

1. Évaluation de la complexité, sensibilité et urgence de la requête
2. Détection du besoin d'escalade
3. Détermination du spécialiste le plus approprié
4. Génération d'un message de transfert
5. Transmission de la requête au spécialiste

### 4. Évaluateur-optimiseur de réponses
L'évaluateur-optimiseur améliore la qualité des réponses générées. Ce pattern est implémenté dans le module `response_evaluator.py` et suit le workflow suivant :

1. Évaluation de la réponse selon plusieurs critères
2. Calcul d'un score global
3. Identification des forces et faiblesses
4. Génération de suggestions d'amélioration
5. Optimisation de la réponse

## Intégration avec Groq API

L'intégration avec l'API Groq est gérée par les modules suivants :

### 1. Client Groq
Le module `groq_integration.py` fournit une interface pour interagir avec l'API Groq, avec les fonctionnalités suivantes :
- Gestion des requêtes synchrones et en streaming
- Support des embeddings pour la recherche sémantique
- Gestion des erreurs et des timeouts

### 2. Orchestrateur de conversation
Le module `chatbot_orchestrator.py` coordonne les interactions avec l'API Groq et les différents composants du système :
- Détection des intentions utilisateur
- Gestion du contexte de conversation
- Traitement des messages avec historique
- Support du mode streaming

### 3. Templates de prompts
Le module `prompt_templates.py` fournit des templates spécifiques au domaine de l'assurance santé :
- Templates par intention (remboursement, réclamation, contrat...)
- Exemples few-shot pour améliorer la qualité des réponses
- Formatage contextuel des données client

## Sécurité et conformité

### 1. Authentification et autorisation
- Authentification multi-facteurs via Keycloak
- Validation des tokens JWT à chaque requête
- Contrôle d'accès basé sur les rôles (RBAC)
- Gestion fine des permissions par API et par endpoint

### 2. Protection des données
- Chiffrement des données sensibles au repos et en transit
- Anonymisation automatique des données personnelles
- Masquage des numéros de sécurité sociale et informations médicales
- Journalisation des accès aux données sensibles

### 3. Conformité réglementaire
- Respect des principes RGPD
- Traçabilité complète des actions
- Mécanismes de consentement explicite
- Procédures de suppression des données

## Extensibilité et évolutivité

L'architecture modulaire du POC permet une extensibilité et une évolutivité optimales :

### 1. Ajout de nouvelles fonctionnalités
- Développement de nouvelles API spécialisées
- Intégration de nouveaux modèles de langage
- Ajout de sources de données supplémentaires

### 2. Mise à l'échelle
- Conteneurisation de tous les composants
- Orchestration via Docker Compose (extensible à Kubernetes)
- Scaling horizontal des services API
- Réplication des bases de données

### 3. Intégration avec les systèmes existants
- API RESTful standardisées
- Support de formats d'échange courants (JSON, XML)
- Webhooks pour les notifications événementielles
- Adaptateurs pour les systèmes legacy
