# POC de Chatbot IA pour AssurSanté

Ce projet est un Proof of Concept (POC) de chatbot IA sécurisé destiné aux agents de service client d'AssurSanté. Il implémente une architecture API-First légère et modulaire avec des composants spécialisés pour la recherche intelligente, les actions métier, la gestion du contexte et la structuration des réponses, ainsi qu'une interface utilisateur moderne en Vue.js.

## Caractéristiques principales

- **Architecture API-First modulaire** avec 4 API spécialisées
- **Interface utilisateur intuitive** développée en Vue.js et Vuetify
- **Sécurité complète** avec Keycloak MFA et contrôle d'accès RBAC
- **Intégration LLM** avec l'API Groq pour la génération de réponses
- **Workflows avancés** incluant chaînage de prompts, gating, routage humain et évaluation
- **Données de test** générées automatiquement pour simuler un environnement réaliste
- **Conteneurisation complète** avec Docker pour un déploiement simplifié

## Architecture

Le POC est construit autour de deux composants principaux :

### Backend API-First

Quatre API modulaires spécialisées :

1. **Look API** : Recherche intelligente dans PostgreSQL, Elasticsearch et Qdrant
2. **Tools API** : Actions métier comme la création de tickets et la gestion des réclamations
3. **Memory API** : Gestion du contexte des conversations avec Redis
4. **Output API** : Structuration des réponses en différents formats

### Frontend Vue.js

Interface utilisateur moderne et intuitive :

1. **Interface agent** : Tableau de bord, recherche clients, détails clients
2. **Interface de chat** : Conversation avec le chatbot IA, suggestions contextuelles
3. **Historique** : Consultation des conversations passées et des réclamations

L'ensemble est sécurisé par Keycloak pour l'authentification MFA et HashiCorp Vault pour la gestion des secrets.

![Architecture](docs/diagrams/architecture_diagram.txt)

## Prérequis

- Docker et Docker Compose
- 8 Go de RAM minimum
- 20 Go d'espace disque
- Connexion Internet (pour l'accès à l'API Groq)

## Installation rapide

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/assursante/chatbot-poc.git
   cd chatbot-poc
   ```

2. Configurez les variables d'environnement :
   ```bash
   cp docker/.env.example docker/.env
   # Éditez le fichier .env avec vos paramètres
   ```

3. Lancez les conteneurs :
   ```bash
   cd docker
   docker-compose up -d
   ```

4. Accédez à l'interface utilisateur :
   ```
   http://localhost:80
   ```

5. Accédez à l'API Gateway (pour les développeurs) :
   ```
   http://localhost:8080/api
   ```

## Structure du projet

```
chatbot-poc/
├── api/                    # Code source des API
│   ├── look-api/           # API de recherche intelligente
│   ├── tools-api/          # API d'actions métier
│   ├── memory-api/         # API de gestion du contexte
│   └── output-api/         # API de structuration des réponses
├── core/                   # Composants centraux
│   ├── auth/               # Authentification et autorisation
│   ├── security/           # Sécurité et chiffrement
│   └── utils/              # Utilitaires partagés
├── data/                   # Scripts de génération de données
├── docker/                 # Configuration Docker
│   ├── services/           # Configuration des services
│   └── docker-compose.yml  # Orchestration des conteneurs
├── frontend/               # Interface utilisateur Vue.js
│   ├── public/             # Fichiers statiques
│   ├── src/                # Code source frontend
│   │   ├── components/     # Composants réutilisables
│   │   ├── views/          # Vues principales
│   │   ├── services/       # Services d'API et d'authentification
│   │   └── store/          # Store Vuex pour la gestion d'état
│   └── Dockerfile          # Configuration pour la conteneurisation
└── docs/                   # Documentation
    ├── diagrams/           # Diagrammes d'architecture
    ├── architecture.md     # Documentation d'architecture
    ├── api-reference.md    # Référence des API
    └── frontend-architecture.md # Documentation du frontend
```

## Workflows et patterns

Le POC implémente plusieurs patterns avancés :

- **Chaînage de prompts** : Décomposition des requêtes complexes en sous-tâches
- **Système de gating** : Vérification de conformité des réponses
- **Routage vers des spécialistes humains** : Détection des cas nécessitant une intervention humaine
- **Évaluateur-optimiseur** : Amélioration de la qualité des réponses

Pour plus de détails, consultez le [diagramme de workflow](docs/diagrams/workflow_diagram.md).

## Documentation

- [Architecture détaillée](docs/architecture.md)
- [Référence des API](docs/api-reference.md)
- [Architecture du Frontend](docs/frontend-architecture.md)
- [Guide d'implémentation](docs/implementation-guide.md)
- [Diagramme de séquence](docs/diagrams/sequence_diagram.md)

## Scénario de démonstration

Un scénario de démonstration complet est disponible pour tester les fonctionnalités du POC :

1. Authentification de l'agent
2. Recherche d'informations client
3. Consultation de la base de connaissances
4. Génération d'une réponse
5. Journalisation de l'interaction

Pour exécuter le scénario de démonstration :

```bash
cd chatbot-poc
./run_demo.sh
```

## Licence

Ce projet est un POC interne à AssurSanté et n'est pas destiné à une distribution publique.

## Contact

Pour toute question concernant ce POC, veuillez contacter l'équipe Innovation Digitale d'AssurSanté.
# secure-chatbot-IA-
