// Implémentation du contrôle d'accès basé sur les rôles (RBAC)
// Ce fichier contient les fonctions pour gérer les autorisations basées sur les rôles

const { logSecurityEvent } = require('../security/utils');

/**
 * Matrice des permissions par rôle
 */
const rolePermissions = {
  // Rôles du realm
  'agent_standard': [
    'view_client_data',
    'view_claims',
    'create_tickets',
    'send_emails'
  ],
  'agent_senior': [
    'view_client_data',
    'view_claims',
    'create_tickets',
    'send_emails',
    'modify_claims'
  ],
  'superviseur': [
    'view_client_data',
    'view_claims',
    'create_tickets',
    'send_emails',
    'modify_claims',
    'view_agent_conversations',
    'manage_users'
  ]
};

/**
 * Vérifie si un utilisateur a un rôle spécifique
 * @param {object} userInfo - Informations utilisateur de Keycloak
 * @param {string} role - Rôle à vérifier
 * @returns {boolean} - Possession du rôle
 */
function hasRole(userInfo, role) {
  if (!userInfo || !userInfo.realm_access || !userInfo.realm_access.roles) {
    return false;
  }
  
  return userInfo.realm_access.roles.includes(role);
}

/**
 * Vérifie si un utilisateur a une permission spécifique
 * @param {object} userInfo - Informations utilisateur de Keycloak
 * @param {string} permission - Permission à vérifier
 * @returns {boolean} - Possession de la permission
 */
function hasPermission(userInfo, permission) {
  // Vérification directe des permissions client
  if (userInfo && 
      userInfo.resource_access && 
      userInfo.resource_access['chatbot-client'] && 
      userInfo.resource_access['chatbot-client'].roles) {
    
    if (userInfo.resource_access['chatbot-client'].roles.includes(permission)) {
      return true;
    }
  }
  
  // Vérification des permissions via les rôles
  if (userInfo && userInfo.realm_access && userInfo.realm_access.roles) {
    for (const role of userInfo.realm_access.roles) {
      if (rolePermissions[role] && rolePermissions[role].includes(permission)) {
        return true;
      }
    }
  }
  
  return false;
}

/**
 * Middleware Express pour vérifier les rôles
 * @param {string|string[]} requiredRoles - Rôle(s) requis
 * @returns {Function} - Middleware Express
 */
function requireRole(requiredRoles) {
  // Conversion en tableau si nécessaire
  const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
  
  return (req, res, next) => {
    // Vérification que l'utilisateur est authentifié
    if (!req.session || !req.session.userInfo) {
      return res.status(401).json({
        status: 'error',
        message: 'Authentification requise'
      });
    }
    
    // Vérification des rôles
    const userHasRole = roles.some(role => hasRole(req.session.userInfo, role));
    
    if (!userHasRole) {
      // Journalisation de la tentative d'accès non autorisé
      logSecurityEvent({
        type: 'authorization',
        action: 'role_check',
        status: 'failure',
        user: req.session.userInfo.preferred_username,
        requiredRoles: roles,
        ip: req.ip
      });
      
      return res.status(403).json({
        status: 'error',
        message: 'Accès non autorisé: rôle requis'
      });
    }
    
    // Utilisateur autorisé
    next();
  };
}

/**
 * Middleware Express pour vérifier les permissions
 * @param {string|string[]} requiredPermissions - Permission(s) requise(s)
 * @returns {Function} - Middleware Express
 */
function requirePermission(requiredPermissions) {
  // Conversion en tableau si nécessaire
  const permissions = Array.isArray(requiredPermissions) ? requiredPermissions : [requiredPermissions];
  
  return (req, res, next) => {
    // Vérification que l'utilisateur est authentifié
    if (!req.session || !req.session.userInfo) {
      return res.status(401).json({
        status: 'error',
        message: 'Authentification requise'
      });
    }
    
    // Vérification des permissions
    const missingPermissions = permissions.filter(
      permission => !hasPermission(req.session.userInfo, permission)
    );
    
    if (missingPermissions.length > 0) {
      // Journalisation de la tentative d'accès non autorisé
      logSecurityEvent({
        type: 'authorization',
        action: 'permission_check',
        status: 'failure',
        user: req.session.userInfo.preferred_username,
        requiredPermissions: permissions,
        missingPermissions: missingPermissions,
        ip: req.ip
      });
      
      return res.status(403).json({
        status: 'error',
        message: 'Accès non autorisé: permissions requises',
        missingPermissions: missingPermissions
      });
    }
    
    // Utilisateur autorisé
    next();
  };
}

/**
 * Récupère toutes les permissions d'un utilisateur
 * @param {object} userInfo - Informations utilisateur de Keycloak
 * @returns {string[]} - Liste des permissions
 */
function getUserPermissions(userInfo) {
  const permissions = new Set();
  
  // Ajout des permissions directes
  if (userInfo && 
      userInfo.resource_access && 
      userInfo.resource_access['chatbot-client'] && 
      userInfo.resource_access['chatbot-client'].roles) {
    
    for (const permission of userInfo.resource_access['chatbot-client'].roles) {
      permissions.add(permission);
    }
  }
  
  // Ajout des permissions via les rôles
  if (userInfo && userInfo.realm_access && userInfo.realm_access.roles) {
    for (const role of userInfo.realm_access.roles) {
      if (rolePermissions[role]) {
        for (const permission of rolePermissions[role]) {
          permissions.add(permission);
        }
      }
    }
  }
  
  return Array.from(permissions);
}

module.exports = {
  hasRole,
  hasPermission,
  requireRole,
  requirePermission,
  getUserPermissions,
  rolePermissions
};
