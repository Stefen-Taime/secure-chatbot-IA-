# Architecture du Frontend Vue.js

Ce document décrit l'architecture et les composants du frontend Vue.js développé pour le POC de chatbot IA d'AssurSanté.

## Vue d'ensemble

Le frontend est une application Vue.js 3 qui utilise Vuetify comme framework UI, Vuex pour la gestion d'état, et Vue Router pour la navigation. L'application s'intègre avec Keycloak pour l'authentification et communique avec les API backend via des services dédiés.

## Structure du projet

```
frontend/
├── public/                 # Fichiers statiques
├── src/
│   ├── assets/             # Images et ressources
│   ├── components/         # Composants réutilisables
│   ├── filters/            # Filtres globaux
│   ├── plugins/            # Plugins Vue.js
│   ├── services/           # Services d'API et d'authentification
│   ├── store/              # Store Vuex pour la gestion d'état
│   ├── views/              # Vues principales de l'application
│   ├── App.vue             # Composant racine
│   ├── main.js             # Point d'entrée de l'application
│   └── router.js           # Configuration des routes
├── Dockerfile              # Configuration pour la conteneurisation
├── nginx.conf              # Configuration Nginx pour le déploiement
└── package.json            # Dépendances et scripts
```

## Composants principaux

### Vues

1. **LoginView** - Page de connexion avec intégration Keycloak
2. **HomeView** - Tableau de bord principal pour les agents
3. **ClientSearchView** - Recherche et liste des clients
4. **ClientDetailView** - Détails d'un client spécifique
5. **ChatView** - Interface de conversation avec le chatbot
6. **HistoryView** - Historique des conversations

### Composants réutilisables

1. **ChatBubble** - Affichage des messages dans l'interface de chat
2. **ClientCard** - Carte d'information client pour la liste des résultats
3. **LoadingOverlay** - Indicateur de chargement
4. **NotificationSnackbar** - Notifications système

### Services

1. **keycloak-service.js** - Gestion de l'authentification avec Keycloak
2. **api-service.js** - Communication avec les API backend
   - lookService - Recherche et accès aux informations
   - toolsService - Actions et opérations
   - memoryService - Gestion du contexte et de l'historique
   - outputService - Formatage des réponses

## Flux d'authentification

1. L'utilisateur accède à l'application
2. Le service Keycloak vérifie si l'utilisateur est déjà authentifié
3. Si non, redirection vers la page de login
4. Après authentification réussie, l'utilisateur est redirigé vers le tableau de bord
5. Les tokens JWT sont stockés et automatiquement rafraîchis

## Flux de conversation

1. L'agent recherche un client
2. L'agent sélectionne un client et démarre une conversation
3. Le système crée une nouvelle session via la Memory API
4. L'agent envoie un message qui est traité par la Look API
5. La réponse est formatée par l'Output API et affichée dans l'interface
6. L'historique de conversation est mis à jour via la Memory API

## Intégration avec le backend

Le frontend communique avec les quatre API modulaires :

1. **Look API** - Pour la recherche d'informations et l'interaction avec le chatbot
2. **Tools API** - Pour les actions comme la création de tickets ou de réclamations
3. **Memory API** - Pour la gestion des sessions et de l'historique des conversations
4. **Output API** - Pour le formatage des réponses

## Sécurité

- Authentification via Keycloak avec support MFA
- Contrôle d'accès basé sur les rôles (RBAC)
- Tokens JWT pour l'autorisation des requêtes API
- Rafraîchissement automatique des tokens
- Protection CSRF et XSS via les en-têtes de sécurité Nginx

## Déploiement

Le frontend est conteneurisé via Docker et servi par Nginx. La configuration Nginx gère :

1. Le routage des requêtes vers l'application Vue.js (SPA)
2. Le proxy des requêtes API vers les services backend
3. La compression des ressources statiques
4. Les en-têtes de sécurité

## Extensibilité

L'architecture modulaire permet d'ajouter facilement de nouvelles fonctionnalités :

1. Créer de nouveaux composants Vue.js
2. Ajouter des routes dans router.js
3. Étendre le store Vuex avec de nouvelles actions et mutations
4. Ajouter des services API pour de nouvelles fonctionnalités backend
