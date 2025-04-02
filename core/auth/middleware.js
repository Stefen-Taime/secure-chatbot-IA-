// Middleware d'authentification pour les API
// Ce fichier contient les fonctions de vérification des tokens JWT et des permissions

const httpx = require('httpx');
const { FastifyRequest, FastifyReply } = require('fastify');

// Variables d'environnement
const KEYCLOAK_HOST = process.env.KEYCLOAK_HOST || 'keycloak';
const KEYCLOAK_REALM = process.env.KEYCLOAK_REALM || 'assursante';

/**
 * Middleware de vérification du token JWT
 * @param {FastifyRequest} request - Requête Fastify
 * @param {FastifyReply} reply - Réponse Fastify
 */
async function verifyToken(request, reply) {
  try {
    // Récupération du token depuis l'en-tête Authorization
    const authHeader = request.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return reply.code(401).send({
        status: 'error',
        code: 401,
        message: 'Token d\'authentification manquant ou invalide'
      });
    }
    
    const token = authHeader.substring(7);
    
    // Vérification du token auprès de Keycloak
    const response = await httpx.get(
      `http://${KEYCLOAK_HOST}:8080/realms/${KEYCLOAK_REALM}/protocol/openid-connect/userinfo`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (response.statusCode !== 200) {
      return reply.code(401).send({
        status: 'error',
        code: 401,
        message: 'Token invalide ou expiré'
      });
    }
    
    // Extraction des informations utilisateur
    const userInfo = JSON.parse(response.data);
    
    // Ajout des informations utilisateur à la requête
    request.user = userInfo;
    
  } catch (error) {
    console.error('Erreur lors de la vérification du token:', error);
    
    return reply.code(503).send({
      status: 'error',
      code: 503,
      message: 'Service d\'authentification indisponible'
    });
  }
}

/**
 * Middleware de vérification des rôles
 * @param {string[]} requiredRoles - Rôles requis
 * @returns {Function} - Middleware Fastify
 */
function requireRoles(requiredRoles) {
  return async (request, reply) => {
    // Vérification que l'utilisateur est authentifié
    if (!request.user) {
      return reply.code(401).send({
        status: 'error',
        code: 401,
        message: 'Utilisateur non authentifié'
      });
    }
    
    // Récupération des rôles de l'utilisateur
    const userRoles = request.user.realm_access?.roles || [];
    
    // Vérification que l'utilisateur possède au moins un des rôles requis
    const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));
    
    if (!hasRequiredRole) {
      return reply.code(403).send({
        status: 'error',
        code: 403,
        message: 'Accès non autorisé: rôle requis'
      });
    }
  };
}

/**
 * Middleware de vérification des permissions
 * @param {string[]} requiredPermissions - Permissions requises
 * @returns {Function} - Middleware Fastify
 */
function requirePermissions(requiredPermissions) {
  return async (request, reply) => {
    // Vérification que l'utilisateur est authentifié
    if (!request.user) {
      return reply.code(401).send({
        status: 'error',
        code: 401,
        message: 'Utilisateur non authentifié'
      });
    }
    
    // Récupération des permissions de l'utilisateur
    const userPermissions = request.user.resource_access?.['chatbot-client']?.roles || [];
    
    // Vérification que l'utilisateur possède toutes les permissions requises
    const hasAllPermissions = requiredPermissions.every(permission => 
      userPermissions.includes(permission)
    );
    
    if (!hasAllPermissions) {
      return reply.code(403).send({
        status: 'error',
        code: 403,
        message: 'Accès non autorisé: permission requise'
      });
    }
  };
}

/**
 * Fonction d'anonymisation des données sensibles
 * @param {object} data - Données à anonymiser
 * @returns {object} - Données anonymisées
 */
function anonymizeSensitiveData(data) {
  if (!data) return data;
  
  if (typeof data === 'object' && data !== null) {
    if (Array.isArray(data)) {
      // Traitement des tableaux
      return data.map(item => anonymizeSensitiveData(item));
    } else {
      // Traitement des objets
      const result = { ...data };
      
      // Anonymisation des numéros de sécurité sociale
      if (result.numero_securite_sociale) {
        result.numero_securite_sociale = result.numero_securite_sociale.substring(0, 3) + '***********';
      }
      
      // Anonymisation des emails
      if (result.email && typeof result.email === 'string' && result.email.includes('@')) {
        const [localPart, domain] = result.email.split('@');
        result.email = localPart.substring(0, 3) + '***@' + domain;
      }
      
      // Traitement récursif des propriétés
      Object.keys(result).forEach(key => {
        if (typeof result[key] === 'object' && result[key] !== null) {
          result[key] = anonymizeSensitiveData(result[key]);
        }
      });
      
      return result;
    }
  }
  
  return data;
}

module.exports = {
  verifyToken,
  requireRoles,
  requirePermissions,
  anonymizeSensitiveData
};
