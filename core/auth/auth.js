// Fichier d'implémentation du client frontend pour l'authentification Keycloak
// Ce fichier contient le code nécessaire pour gérer l'authentification et les tokens

// auth.js - Module d'authentification pour le frontend

/**
 * Configuration de Keycloak
 */
const keycloakConfig = {
  url: 'http://keycloak:8081',
  realm: 'assursante',
  clientId: 'chatbot-client'
};

/**
 * Classe de gestion de l'authentification
 */
class AuthService {
  constructor() {
    this.accessToken = localStorage.getItem('access_token') || null;
    this.refreshToken = localStorage.getItem('refresh_token') || null;
    this.tokenExpiry = localStorage.getItem('token_expiry') || null;
    this.refreshExpiry = localStorage.getItem('refresh_expiry') || null;
    this.userInfo = JSON.parse(localStorage.getItem('user_info') || 'null');
  }

  /**
   * Initialise le processus de login
   */
  login() {
    // Construction de l'URL de redirection vers Keycloak
    const redirectUri = encodeURIComponent(window.location.origin + '/callback');
    const authUrl = `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/auth?client_id=${keycloakConfig.clientId}&redirect_uri=${redirectUri}&response_type=code&scope=openid`;
    
    // Redirection vers Keycloak
    window.location.href = authUrl;
  }

  /**
   * Traite le code d'autorisation reçu après authentification
   * @param {string} code - Code d'autorisation
   * @returns {Promise<boolean>} - Succès de l'authentification
   */
  async processAuthCode(code) {
    try {
      const redirectUri = encodeURIComponent(window.location.origin + '/callback');
      const tokenUrl = `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/token`;
      
      const response = await fetch(tokenUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          'grant_type': 'authorization_code',
          'client_id': keycloakConfig.clientId,
          'code': code,
          'redirect_uri': decodeURIComponent(redirectUri)
        }),
      });
      
      if (!response.ok) {
        throw new Error('Échec de l\'échange du code d\'autorisation');
      }
      
      const tokens = await response.json();
      this.setTokens(tokens);
      
      // Récupération des informations utilisateur
      await this.fetchUserInfo();
      
      return true;
    } catch (error) {
      console.error('Erreur lors du processus d\'authentification:', error);
      return false;
    }
  }

  /**
   * Récupère les informations de l'utilisateur
   * @returns {Promise<object|null>} - Informations utilisateur
   */
  async fetchUserInfo() {
    try {
      if (!this.accessToken) {
        return null;
      }
      
      const userInfoUrl = `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/userinfo`;
      
      const response = await fetch(userInfoUrl, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Échec de récupération des informations utilisateur');
      }
      
      const userInfo = await response.json();
      this.userInfo = userInfo;
      localStorage.setItem('user_info', JSON.stringify(userInfo));
      
      return userInfo;
    } catch (error) {
      console.error('Erreur lors de la récupération des informations utilisateur:', error);
      return null;
    }
  }

  /**
   * Enregistre les tokens et leurs dates d'expiration
   * @param {object} tokens - Tokens d'authentification
   */
  setTokens(tokens) {
    this.accessToken = tokens.access_token;
    this.refreshToken = tokens.refresh_token;
    
    // Calcul des dates d'expiration
    const now = Math.floor(Date.now() / 1000);
    this.tokenExpiry = now + tokens.expires_in;
    this.refreshExpiry = now + tokens.refresh_expires_in;
    
    // Stockage dans le localStorage
    localStorage.setItem('access_token', this.accessToken);
    localStorage.setItem('refresh_token', this.refreshToken);
    localStorage.setItem('token_expiry', this.tokenExpiry);
    localStorage.setItem('refresh_expiry', this.refreshExpiry);
  }

  /**
   * Vérifie si l'utilisateur est authentifié
   * @returns {boolean} - Statut d'authentification
   */
  isAuthenticated() {
    if (!this.accessToken || !this.tokenExpiry) {
      return false;
    }
    
    const now = Math.floor(Date.now() / 1000);
    return now < this.tokenExpiry;
  }

  /**
   * Vérifie si le token de rafraîchissement est valide
   * @returns {boolean} - Validité du token de rafraîchissement
   */
  canRefresh() {
    if (!this.refreshToken || !this.refreshExpiry) {
      return false;
    }
    
    const now = Math.floor(Date.now() / 1000);
    return now < this.refreshExpiry;
  }

  /**
   * Rafraîchit le token d'accès
   * @returns {Promise<boolean>} - Succès du rafraîchissement
   */
  async refreshAccessToken() {
    try {
      if (!this.canRefresh()) {
        return false;
      }
      
      const tokenUrl = `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/token`;
      
      const response = await fetch(tokenUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          'grant_type': 'refresh_token',
          'client_id': keycloakConfig.clientId,
          'refresh_token': this.refreshToken
        }),
      });
      
      if (!response.ok) {
        throw new Error('Échec du rafraîchissement du token');
      }
      
      const tokens = await response.json();
      this.setTokens(tokens);
      
      return true;
    } catch (error) {
      console.error('Erreur lors du rafraîchissement du token:', error);
      return false;
    }
  }

  /**
   * Obtient un token d'accès valide (rafraîchit si nécessaire)
   * @returns {Promise<string|null>} - Token d'accès valide
   */
  async getValidToken() {
    if (this.isAuthenticated()) {
      return this.accessToken;
    }
    
    if (await this.refreshAccessToken()) {
      return this.accessToken;
    }
    
    return null;
  }

  /**
   * Vérifie si l'utilisateur a un rôle spécifique
   * @param {string} role - Rôle à vérifier
   * @returns {boolean} - Possession du rôle
   */
  hasRole(role) {
    if (!this.userInfo || !this.userInfo.realm_access || !this.userInfo.realm_access.roles) {
      return false;
    }
    
    return this.userInfo.realm_access.roles.includes(role);
  }

  /**
   * Vérifie si l'utilisateur a une permission spécifique
   * @param {string} permission - Permission à vérifier
   * @returns {boolean} - Possession de la permission
   */
  hasPermission(permission) {
    if (!this.userInfo || !this.userInfo.resource_access || 
        !this.userInfo.resource_access['chatbot-client'] || 
        !this.userInfo.resource_access['chatbot-client'].roles) {
      return false;
    }
    
    return this.userInfo.resource_access['chatbot-client'].roles.includes(permission);
  }

  /**
   * Déconnecte l'utilisateur
   */
  logout() {
    // Suppression des tokens et informations utilisateur
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expiry');
    localStorage.removeItem('refresh_expiry');
    localStorage.removeItem('user_info');
    
    this.accessToken = null;
    this.refreshToken = null;
    this.tokenExpiry = null;
    this.refreshExpiry = null;
    this.userInfo = null;
    
    // Redirection vers la page de déconnexion de Keycloak
    const redirectUri = encodeURIComponent(window.location.origin);
    const logoutUrl = `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/logout?redirect_uri=${redirectUri}`;
    
    window.location.href = logoutUrl;
  }
}

// Création d'une instance unique du service d'authentification
const authService = new AuthService();

/**
 * Intercepteur HTTP pour ajouter le token d'authentification aux requêtes
 * @param {string} url - URL de la requête
 * @param {object} options - Options de la requête
 * @returns {Promise<Response>} - Réponse de la requête
 */
async function authenticatedFetch(url, options = {}) {
  // Vérification de l'authentification
  const token = await authService.getValidToken();
  
  if (!token) {
    // Redirection vers la page de login si non authentifié
    authService.login();
    throw new Error('Non authentifié');
  }
  
  // Ajout du token aux en-têtes
  const headers = options.headers || {};
  headers['Authorization'] = `Bearer ${token}`;
  
  // Exécution de la requête
  const response = await fetch(url, {
    ...options,
    headers
  });
  
  // Gestion des erreurs d'authentification
  if (response.status === 401) {
    // Tentative de rafraîchissement du token
    const refreshSuccess = await authService.refreshAccessToken();
    
    if (refreshSuccess) {
      // Nouvelle tentative avec le token rafraîchi
      headers['Authorization'] = `Bearer ${authService.accessToken}`;
      return fetch(url, {
        ...options,
        headers
      });
    } else {
      // Redirection vers la page de login si le rafraîchissement échoue
      authService.login();
      throw new Error('Session expirée');
    }
  }
  
  return response;
}

// Export des fonctionnalités
export { authService, authenticatedFetch };
