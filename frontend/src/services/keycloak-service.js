import Keycloak from 'keycloak-js';

let keycloak = null;
let initialized = false;

/**
 * Initialise le client Keycloak
 * @returns {Promise} Une promesse qui se résout lorsque Keycloak est initialisé
 */
export function initKeycloak() {
  return new Promise((resolve, reject) => {
    if (initialized) {
      resolve();
      return;
    }

    keycloak = new Keycloak({
      url: 'http://localhost:8081',
      realm: 'assursante',
      clientId: 'chatbot-client'
    });

    keycloak.init({
      onLoad: 'check-sso',
      silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
      pkceMethod: 'S256'
    }).then(authenticated => {
      initialized = true;
      if (authenticated) {
        console.log('Utilisateur authentifié');
        // Rafraîchir le token périodiquement
        setInterval(() => {
          keycloak.updateToken(70).catch(() => {
            console.error('Échec du rafraîchissement du token');
          });
        }, 60000);
      } else {
        console.log('Utilisateur non authentifié');
      }
      resolve(authenticated);
    }).catch(error => {
      console.error('Erreur lors de l\'initialisation de Keycloak:', error);
      reject(error);
    });
  });
}

/**
 * Vérifie si l'utilisateur est authentifié
 * @returns {boolean} Vrai si l'utilisateur est authentifié
 */
export function isAuthenticated() {
  return keycloak && keycloak.authenticated;
}

/**
 * Récupère le token d'authentification
 * @returns {string} Le token d'authentification
 */
export function getToken() {
  return keycloak ? keycloak.token : null;
}

/**
 * Récupère les informations de l'utilisateur
 * @returns {Object} Les informations de l'utilisateur
 */
export function getUserInfo() {
  if (!keycloak || !keycloak.authenticated) {
    return null;
  }

  return {
    id: keycloak.subject,
    username: keycloak.tokenParsed.preferred_username,
    name: keycloak.tokenParsed.name,
    email: keycloak.tokenParsed.email,
    roles: keycloak.tokenParsed.realm_access.roles
  };
}

/**
 * Connecte l'utilisateur
 * @returns {Promise} Une promesse qui se résout lorsque l'utilisateur est connecté
 */
export function login() {
  return keycloak.login();
}

/**
 * Déconnecte l'utilisateur
 * @returns {Promise} Une promesse qui se résout lorsque l'utilisateur est déconnecté
 */
export function logout() {
  return keycloak.logout();
}

/**
 * Vérifie si l'utilisateur a un rôle spécifique
 * @param {string} role Le rôle à vérifier
 * @returns {boolean} Vrai si l'utilisateur a le rôle
 */
export function hasRole(role) {
  return keycloak && keycloak.hasRealmRole(role);
}
