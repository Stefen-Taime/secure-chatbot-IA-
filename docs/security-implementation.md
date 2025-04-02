// Fichier de documentation sur l'implémentation de la sécurité avec Keycloak
// Ce fichier détaille le flux d'authentification MFA, la gestion des tokens JWT et le contrôle d'accès

# Implémentation de la sécurité avec Keycloak

## Vue d'ensemble

L'architecture de sécurité du chatbot IA d'AssurSanté repose sur Keycloak comme fournisseur d'identité central. Cette documentation détaille l'implémentation complète du flux d'authentification, de la gestion des tokens et du contrôle d'accès basé sur les rôles (RBAC).

## Flux d'authentification complet

### 1. Processus de login agent

```
┌─────────┐      ┌─────────┐      ┌──────────┐      ┌───────────┐
│  Agent  │      │ Frontend│      │ Keycloak │      │API Gateway│
└────┬────┘      └────┬────┘      └─────┬────┘      └─────┬─────┘
     │                │                 │                  │
     │ 1. Identifiants│                 │                  │
     │───────────────>│                 │                  │
     │                │ 2. Redirection  │                  │
     │                │────────────────>│                  │
     │                │                 │                  │
     │                │ 3. Page de login│                  │
     │<───────────────┼─────────────────                  │
     │                │                 │                  │
     │ 4. Saisie identifiants          │                  │
     │───────────────>│                 │                  │
     │                │ 5. Authentification               │
     │                │────────────────>│                  │
     │                │                 │                  │
     │                │ 6. Demande MFA  │                  │
     │<───────────────┼─────────────────                  │
     │                │                 │                  │
     │ 7. Code TOTP   │                 │                  │
     │───────────────>│                 │                  │
     │                │ 8. Vérification MFA               │
     │                │────────────────>│                  │
     │                │                 │                  │
     │                │ 9. Tokens JWT   │                  │
     │                │<────────────────│                  │
     │                │                 │                  │
     │ 10. Tokens JWT │                 │                  │
     │<───────────────│                 │                  │
     │                │                 │                  │
     │ 11. Requête API avec token       │                  │
     │────────────────────────────────────────────────────>│
     │                │                 │                  │
     │                │                 │ 12. Validation   │
     │                │                 │<─────────────────│
     │                │                 │                  │
     │                │                 │ 13. Token valide │
     │                │                 │─────────────────>│
     │                │                 │                  │
     │ 14. Réponse API│                 │                  │
     │<────────────────────────────────────────────────────│
     │                │                 │                  │
```

### 2. Détail des étapes

1. L'agent accède à l'interface du chatbot
2. Le frontend détecte l'absence de session et redirige vers Keycloak
3. Keycloak affiche la page de login
4. L'agent saisit ses identifiants (nom d'utilisateur/mot de passe)
5. Keycloak vérifie les identifiants dans la base de données
6. Si les identifiants sont valides, Keycloak demande le second facteur d'authentification (TOTP)
7. L'agent saisit le code généré par son application d'authentification
8. Keycloak vérifie le code TOTP
9. Si le code est valide, Keycloak génère les tokens JWT (access_token et refresh_token)
10. Les tokens sont transmis au frontend qui les stocke en mémoire (localStorage/sessionStorage)
11. Pour chaque requête API, le frontend inclut l'access_token dans l'en-tête Authorization
12. L'API Gateway (NGINX) valide le token auprès de Keycloak
13. Si le token est valide, Keycloak confirme l'identité et les rôles de l'agent
14. L'API Gateway autorise la requête et transmet la réponse à l'agent

## Structure des tokens JWT

### Access Token

```json
{
  "exp": 1617293982,
  "iat": 1617293682,
  "jti": "4c75fbd2-9d0f-4b9a-8a06-1234567890ab",
  "iss": "http://keycloak:8080/realms/assursante",
  "aud": "account",
  "sub": "f:12345:jean.dupont",
  "typ": "Bearer",
  "azp": "chatbot-client",
  "session_state": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "acr": "1",
  "realm_access": {
    "roles": [
      "agent_standard"
    ]
  },
  "resource_access": {
    "chatbot-client": {
      "roles": [
        "view_client_data",
        "view_claims",
        "create_tickets",
        "send_emails"
      ]
    }
  },
  "scope": "openid profile email",
  "email_verified": true,
  "name": "Jean Dupont",
  "preferred_username": "jean.dupont",
  "given_name": "Jean",
  "family_name": "Dupont",
  "email": "jean.dupont@assursante.example"
}
```

### Refresh Token

```json
{
  "exp": 1617380082,
  "iat": 1617293682,
  "jti": "5d86fce3-0e1f-5c0a-9b17-2345678901cd",
  "iss": "http://keycloak:8080/realms/assursante",
  "aud": "http://keycloak:8080/realms/assursante",
  "sub": "f:12345:jean.dupont",
  "typ": "Refresh",
  "azp": "chatbot-client",
  "session_state": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
  "scope": "openid profile email"
}
```

## Validation des tokens

### 1. Validation par l'API Gateway (NGINX)

```nginx
# Extrait de la configuration NGINX
location /api/ {
    auth_request /auth/validate;
    # ... autres directives ...
}

location = /auth/validate {
    internal;
    proxy_pass http://keycloak:8080/realms/assursante/protocol/openid-connect/userinfo;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Authorization $http_authorization;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
}
```

### 2. Validation par les API individuelles

Chaque API implémente également sa propre validation de token pour une sécurité en profondeur :

```python
# Extrait du code de validation dans les API
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
```

## Gestion de l'expiration des sessions

### 1. Configuration des durées de vie des tokens

Dans la configuration du client Keycloak (`realm-export.json`), les durées de vie des tokens sont définies comme suit :

```json
"attributes": {
  "access.token.lifespan": "900",
  "refresh.token.lifespan": "1800"
}
```

- Access Token : 15 minutes (900 secondes)
- Refresh Token : 30 minutes (1800 secondes)

### 2. Processus de rafraîchissement des tokens

```
┌─────────┐      ┌─────────┐      ┌──────────┐
│  Agent  │      │ Frontend│      │ Keycloak │
└────┬────┘      └────┬────┘      └─────┬────┘
     │                │                 │
     │                │ 1. Détection token expiré
     │                │─────┐           │
     │                │     │           │
     │                │<────┘           │
     │                │                 │
     │                │ 2. Demande de rafraîchissement
     │                │────────────────>│
     │                │                 │
     │                │ 3. Nouveaux tokens
     │                │<────────────────│
     │                │                 │
     │                │ 4. Mise à jour des tokens
     │                │─────┐           │
     │                │     │           │
     │                │<────┘           │
     │                │                 │
```

### 3. Implémentation côté frontend

```javascript
// Extrait du code de rafraîchissement des tokens
async function refreshTokens() {
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
      // Redirection vers la page de login
      window.location.href = '/login';
      return;
    }
    
    const response = await fetch('http://keycloak:8080/realms/assursante/protocol/openid-connect/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        'grant_type': 'refresh_token',
        'client_id': 'chatbot-client',
        'refresh_token': refreshToken,
      }),
    });
    
    if (response.ok) {
      const tokens = await response.json();
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      return tokens.access_token;
    } else {
      // Redirection vers la page de login en cas d'échec
      window.location.href = '/login';
    }
  } catch (error) {
    console.error('Erreur lors du rafraîchissement des tokens:', error);
    // Redirection vers la page de login en cas d'erreur
    window.location.href = '/login';
  }
}
```

## Contrôle d'accès basé sur les rôles (RBAC)

### 1. Hiérarchie des rôles

```
┌─────────────────┐
│   superviseur   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   agent_senior  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ agent_standard  │
└─────────────────┘
```

### 2. Permissions par rôle

| Rôle | Permissions |
|------|-------------|
| agent_standard | view_client_data, view_claims, create_tickets, send_emails |
| agent_senior | view_client_data, view_claims, create_tickets, send_emails, modify_claims |
| superviseur | Toutes les permissions + accès aux conversations des autres agents |

### 3. Vérification des permissions dans les API

```python
# Extrait du code de vérification des permissions
def check_permission(user_info: dict, required_permission: str):
    client_roles = user_info.get("clientRoles", {}).get("chatbot-client", [])
    
    if required_permission not in client_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Accès non autorisé: permission {required_permission} requise"
        )
```

## Chiffrement des communications

### 1. Configuration TLS/SSL

Dans un environnement de production, toutes les communications sont chiffrées via TLS/SSL :

- HTTPS pour toutes les communications externes
- Certificats auto-signés pour les communications internes entre services

### 2. Configuration NGINX pour HTTPS

```nginx
server {
    listen 443 ssl;
    server_name chatbot.assursante.example;

    ssl_certificate /etc/nginx/ssl/assursante.crt;
    ssl_certificate_key /etc/nginx/ssl/assursante.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # ... autres directives ...
}
```

## Anonymisation des données sensibles

### 1. Mécanisme d'anonymisation

L'anonymisation des données sensibles est implémentée à plusieurs niveaux :

1. **Au niveau des API** : Masquage des numéros de sécurité sociale et autres données sensibles avant de les renvoyer au client
2. **Au niveau des logs** : Filtrage des données sensibles dans les logs via Logstash et Filebeat
3. **Au niveau de la base de données** : Chiffrement des données sensibles au repos

### 2. Exemple d'anonymisation dans l'API

```python
# Extrait du code d'anonymisation
def anonymize_sensitive_data(data):
    if isinstance(data, dict):
        if "numero_securite_sociale" in data:
            data["numero_securite_sociale"] = data["numero_securite_sociale"][:3] + "***********"
        
        # Traitement récursif pour les dictionnaires imbriqués
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                data[key] = anonymize_sensitive_data(value)
    
    elif isinstance(data, list):
        # Traitement récursif pour les listes
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                data[i] = anonymize_sensitive_data(item)
    
    return data
```

## Journalisation des accès et actions

### 1. Structure de la table d'audit

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    utilisateur VARCHAR(100) NOT NULL,
    action VARCHAR(255) NOT NULL,
    entite_affectee VARCHAR(50) NOT NULL,
    identifiant_entite INTEGER NOT NULL,
    details TEXT,
    adresse_ip VARCHAR(45) NOT NULL,
    date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Exemple de journalisation dans l'API

```python
# Extrait du code de journalisation
def log_action(conn, user_info, action, entity, entity_id, details, ip_address):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO audit_logs
                (utilisateur, action, entite_affectee, identifiant_entite, details, adresse_ip)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_info.get("preferred_username"),
                    action,
                    entity,
                    entity_id,
                    json.dumps(details),
                    ip_address
                )
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Erreur lors de la journalisation: {e}")
        conn.rollback()
```

## Gestion des secrets avec HashiCorp Vault

### 1. Stockage des secrets

Les secrets sensibles (mots de passe, clés API, etc.) sont stockés dans HashiCorp Vault plutôt que directement dans les variables d'environnement ou les fichiers de configuration.

### 2. Exemple d'accès aux secrets dans l'API

```python
# Extrait du code d'accès aux secrets
def get_secret(secret_path):
    try:
        vault_client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
        
        if not vault_client.is_authenticated():
            logger.error("Échec d'authentification à Vault")
            raise Exception("Échec d'authentification à Vault")
        
        secret_response = vault_client.secrets.kv.v2.read_secret_version(
            path=secret_path
        )
        
        return secret_response["data"]["data"]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du secret {secret_path}: {e}")
        raise
```

## Conclusion

Cette implémentation de sécurité avec Keycloak fournit une solution robuste et complète pour l'authentification MFA, la gestion des tokens JWT et le contrôle d'accès basé sur les rôles. Elle répond aux exigences de sécurité d'une application manipulant des données sensibles dans le domaine de l'assurance santé.
