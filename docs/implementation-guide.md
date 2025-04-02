# Guide d'implémentation pas à pas du POC de Chatbot IA pour AssurSanté

Ce guide détaille les étapes nécessaires pour implémenter et déployer le POC de Chatbot IA pour AssurSanté. Il est destiné aux développeurs et administrateurs système qui souhaitent comprendre, installer et étendre le système.

## Table des matières

1. [Préparation de l'environnement](#1-préparation-de-lenvironnement)
2. [Installation des composants](#2-installation-des-composants)
3. [Configuration des services](#3-configuration-des-services)
4. [Génération des données de test](#4-génération-des-données-de-test)
5. [Intégration avec l'API Groq](#5-intégration-avec-lapi-groq)
6. [Configuration de la sécurité](#6-configuration-de-la-sécurité)
7. [Déploiement des API](#7-déploiement-des-api)
8. [Tests et validation](#8-tests-et-validation)
9. [Personnalisation et extension](#9-personnalisation-et-extension)
10. [Résolution des problèmes courants](#10-résolution-des-problèmes-courants)

## 1. Préparation de l'environnement

### 1.1 Prérequis système

Assurez-vous que votre système dispose des éléments suivants :

- Docker Engine 20.10.x ou supérieur
- Docker Compose 2.x ou supérieur
- 8 Go de RAM minimum
- 20 Go d'espace disque disponible
- Connexion Internet stable

### 1.2 Clonage du dépôt

```bash
git clone https://github.com/assursante/chatbot-poc.git
cd chatbot-poc
```

### 1.3 Configuration des variables d'environnement

```bash
cp docker/.env.example docker/.env
```

Éditez le fichier `.env` pour configurer les variables suivantes :

```
# Configuration générale
COMPOSE_PROJECT_NAME=chatbot-poc
DOMAIN_NAME=localhost

# Ports externes
NGINX_PORT=8080
KEYCLOAK_PORT=8081
KIBANA_PORT=5601

# Credentials (à modifier impérativement)
POSTGRES_PASSWORD=changeme
KEYCLOAK_ADMIN_PASSWORD=changeme
ELASTIC_PASSWORD=changeme
REDIS_PASSWORD=changeme
VAULT_TOKEN=changeme

# API Groq
GROQ_API_KEY=votre-clé-api-groq
GROQ_MODEL=llama3-70b-8192
```

## 2. Installation des composants

### 2.1 Lancement des services de base

```bash
cd docker
docker-compose up -d postgres elasticsearch redis keycloak vault
```

Attendez que ces services soient complètement démarrés avant de continuer :

```bash
docker-compose logs -f
```

### 2.2 Initialisation des bases de données

```bash
# Attendre que PostgreSQL soit prêt
docker-compose exec postgres pg_isready

# Vérifier l'initialisation des schémas
docker-compose exec postgres psql -U postgres -c "\dt"
```

### 2.3 Lancement des services ELK

```bash
docker-compose up -d elasticsearch logstash kibana filebeat
```

### 2.4 Vérification de l'état des services

```bash
docker-compose ps
```

Tous les services doivent être à l'état "Up".

## 3. Configuration des services

### 3.1 Configuration de Keycloak

1. Accédez à l'interface d'administration de Keycloak : `http://localhost:8081/admin`
2. Connectez-vous avec les identifiants admin (définis dans le fichier .env)
3. Vérifiez que le realm "assursante" a été correctement importé
4. Vérifiez les rôles et les utilisateurs de test

Si le realm n'a pas été importé automatiquement :

```bash
docker-compose exec keycloak /opt/keycloak/bin/kc.sh import --file /opt/keycloak/data/import/realm-export.json
```

### 3.2 Configuration d'Elasticsearch

Vérifiez que les index nécessaires ont été créés :

```bash
curl -X GET "http://localhost:9200/_cat/indices?v" -u elastic:votre_mot_de_passe
```

Si les index ne sont pas présents, créez-les manuellement :

```bash
# Index pour les réclamations
curl -X PUT "http://localhost:9200/claims" -H "Content-Type: application/json" -d @data/elasticsearch/claims_mapping.json -u elastic:votre_mot_de_passe

# Index pour la base de connaissances
curl -X PUT "http://localhost:9200/knowledge" -H "Content-Type: application/json" -d @data/elasticsearch/knowledge_mapping.json -u elastic:votre_mot_de_passe
```

### 3.3 Configuration de Qdrant

Vérifiez que Qdrant est accessible :

```bash
curl -X GET "http://localhost:6333/collections"
```

Créez la collection pour les embeddings de la base de connaissances :

```bash
curl -X PUT "http://localhost:6333/collections/knowledge" -H "Content-Type: application/json" -d @data/qdrant/knowledge_collection.json
```

### 3.4 Configuration de NGINX

Le fichier de configuration NGINX est déjà préparé dans `docker/services/nginx/conf.d/default.conf`. Vérifiez qu'il correspond à votre environnement et modifiez-le si nécessaire.

## 4. Génération des données de test

### 4.1 Génération des profils clients

```bash
cd data
python3 generate_clients.py --count 100 --output clients.json
```

### 4.2 Génération des réclamations

```bash
python3 generate_claims.py --clients clients.json --count 200 --output claims.json
```

### 4.3 Vectorisation de la base de connaissances

```bash
python3 vectorize_knowledge.py --input knowledge_base.md --output knowledge_vectors.json
```

### 4.4 Chargement des données dans les bases

```bash
# Chargement dans PostgreSQL
python3 load_to_postgres.py --clients clients.json --claims claims.json

# Chargement dans Elasticsearch
python3 load_to_elasticsearch.py --claims claims.json --knowledge knowledge_base.md

# Chargement dans Qdrant
python3 load_to_qdrant.py --vectors knowledge_vectors.json
```

## 5. Intégration avec l'API Groq

### 5.1 Configuration de la clé API

Assurez-vous que la variable `GROQ_API_KEY` est correctement définie dans le fichier `.env`.

### 5.2 Test de l'intégration

```bash
cd core/utils
python3 groq_integration.py
```

Vous devriez voir une réponse de test de l'API Groq.

### 5.3 Configuration des prompts

Les templates de prompts sont définis dans `core/utils/prompt_templates.py`. Vous pouvez les personnaliser selon vos besoins spécifiques.

## 6. Configuration de la sécurité

### 6.1 Configuration de HashiCorp Vault

Initialisez Vault si ce n'est pas déjà fait :

```bash
docker-compose exec vault vault operator init
```

Déverrouillez Vault :

```bash
docker-compose exec vault vault operator unseal
```

Stockez vos secrets dans Vault :

```bash
docker-compose exec vault vault kv put secret/api/groq api_key=votre-clé-api-groq
docker-compose exec vault vault kv put secret/api/database username=postgres password=votre-mot-de-passe
```

### 6.2 Configuration du RBAC

Les rôles et permissions sont définis dans Keycloak. Vérifiez que les rôles suivants existent :

- `agent_standard`
- `agent_senior`
- `superviseur`

Et que les permissions appropriées sont attribuées à chaque rôle.

### 6.3 Test de l'authentification

```bash
# Obtention d'un token
curl -X POST "http://localhost:8081/realms/assursante/protocol/openid-connect/token" \
  -d "client_id=chatbot-api" \
  -d "username=agent_test" \
  -d "password=password" \
  -d "grant_type=password"

# Test avec le token
curl -X GET "http://localhost:8080/api/look/v1/clients/search?query=dupont" \
  -H "Authorization: Bearer votre-token"
```

## 7. Déploiement des API

### 7.1 Construction des images Docker

```bash
cd api/look-api
docker build -t assursante/look-api:latest .

cd ../tools-api
docker build -t assursante/tools-api:latest .

cd ../memory-api
docker build -t assursante/memory-api:latest .

cd ../output-api
docker build -t assursante/output-api:latest .
```

### 7.2 Démarrage des API

```bash
cd ../../docker
docker-compose up -d look-api tools-api memory-api output-api
```

### 7.3 Vérification des API

```bash
# Look API
curl -X GET "http://localhost:8080/api/look/v1/health"

# Tools API
curl -X GET "http://localhost:8080/api/tools/v1/health"

# Memory API
curl -X GET "http://localhost:8080/api/memory/v1/health"

# Output API
curl -X GET "http://localhost:8080/api/output/v1/health"
```

## 8. Tests et validation

### 8.1 Tests unitaires

```bash
cd api/look-api
python -m unittest discover tests

# Répétez pour chaque API
```

### 8.2 Tests d'intégration

```bash
cd tests/integration
python -m pytest
```

### 8.3 Test du workflow complet

Exécutez le scénario de démonstration :

```bash
cd chatbot-poc
./run_demo.sh
```

## 9. Personnalisation et extension

### 9.1 Ajout de nouvelles fonctionnalités

Pour ajouter un nouvel endpoint à une API existante :

1. Créez un nouveau fichier dans le répertoire `routes` de l'API concernée
2. Implémentez la logique métier dans le répertoire `services`
3. Enregistrez la route dans le fichier `main.py`

### 9.2 Intégration avec d'autres modèles LLM

Pour utiliser un autre modèle LLM que Groq :

1. Créez une nouvelle classe d'intégration dans `core/utils/`
2. Implémentez les méthodes nécessaires pour l'API du modèle
3. Mettez à jour la configuration pour utiliser cette nouvelle classe

### 9.3 Personnalisation des prompts

Les templates de prompts peuvent être personnalisés dans `core/utils/prompt_templates.py` :

1. Ajoutez de nouveaux templates pour des cas d'usage spécifiques
2. Modifiez les templates existants pour améliorer les réponses
3. Ajoutez des exemples few-shot pour des domaines particuliers

## 10. Résolution des problèmes courants

### 10.1 Problèmes de connexion aux bases de données

Si vous rencontrez des problèmes de connexion aux bases de données :

```bash
# Vérifiez les logs
docker-compose logs postgres
docker-compose logs elasticsearch
docker-compose logs redis

# Vérifiez les connexions réseau
docker-compose exec postgres pg_isready
curl -X GET "http://localhost:9200/_cluster/health" -u elastic:votre_mot_de_passe
docker-compose exec redis redis-cli -a votre_mot_de_passe ping
```

### 10.2 Problèmes d'authentification

Si vous rencontrez des problèmes d'authentification :

```bash
# Vérifiez les logs de Keycloak
docker-compose logs keycloak

# Vérifiez la configuration du client dans Keycloak
# Accédez à http://localhost:8081/admin
# Vérifiez les paramètres du client "chatbot-api"
```

### 10.3 Problèmes avec l'API Groq

Si l'API Groq ne répond pas correctement :

1. Vérifiez que votre clé API est valide
2. Vérifiez que vous avez accès au modèle spécifié
3. Vérifiez les quotas et limites de votre compte Groq

```bash
# Test simple de l'API Groq
curl -X POST "https://api.groq.com/openai/v1/chat/completions" \
  -H "Authorization: Bearer votre-clé-api" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3-70b-8192",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### 10.4 Redémarrage complet du système

En cas de problèmes persistants, vous pouvez redémarrer complètement le système :

```bash
cd docker
docker-compose down
docker-compose up -d
```

## Conclusion

Ce guide vous a présenté les étapes nécessaires pour implémenter et déployer le POC de Chatbot IA pour AssurSanté. Pour toute question ou problème non couvert dans ce guide, veuillez contacter l'équipe de développement.
