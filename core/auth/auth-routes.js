// Implémentation du flux d'authentification MFA avec Keycloak
// Ce fichier contient le code pour gérer le flux complet d'authentification

const express = require('express');
const router = express.Router();
const axios = require('axios');
const { getSecret, logSecurityEvent } = require('../security/utils');

// Variables d'environnement
const KEYCLOAK_HOST = process.env.KEYCLOAK_HOST || 'keycloak';
const KEYCLOAK_REALM = process.env.KEYCLOAK_REALM || 'assursante';
const KEYCLOAK_CLIENT_ID = process.env.KEYCLOAK_CLIENT_ID || 'chatbot-client';
const KEYCLOAK_CLIENT_SECRET = process.env.KEYCLOAK_CLIENT_SECRET || 'chatbot-client-secret';

/**
 * Initialise le flux d'authentification
 */
router.get('/login', (req, res) => {
  // Construction de l'URL de redirection vers Keycloak
  const redirectUri = encodeURIComponent(`${req.protocol}://${req.get('host')}/auth/callback`);
  const authUrl = `http://${KEYCLOAK_HOST}:8080/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth?client_id=${KEYCLOAK_CLIENT_ID}&redirect_uri=${redirectUri}&response_type=code&scope=openid`;
  
  // Redirection vers Keycloak
  res.redirect(authUrl);
});

/**
 * Traite le callback après authentification
 */
router.get('/callback', async (req, res) => {
  try {
    const { code } = req.query;
    
    if (!code) {
      return res.status(400).json({
        status: 'error',
        message: 'Code d\'autorisation manquant'
      });
    }
    
    // Échange du code d'autorisation contre des tokens
    const redirectUri = `${req.protocol}://${req.get('host')}/auth/callback`;
    const tokenUrl = `http://${KEYCLOAK_HOST}:8080/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token`;
    
    const response = await axios.post(tokenUrl, 
      new URLSearchParams({
        'grant_type': 'authorization_code',
        'client_id': KEYCLOAK_CLIENT_ID,
        'client_secret': KEYCLOAK_CLIENT_SECRET,
        'code': code,
        'redirect_uri': redirectUri
      }).toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );
    
    // Récupération des tokens
    const { access_token, refresh_token, expires_in } = response.data;
    
    // Stockage des tokens dans la session
    req.session.accessToken = access_token;
    req.session.refreshToken = refresh_token;
    req.session.tokenExpiry = Date.now() + (expires_in * 1000);
    
    // Récupération des informations utilisateur
    const userInfoUrl = `http://${KEYCLOAK_HOST}:8080/realms/${KEYCLOAK_REALM}/protocol/openid-connect/userinfo`;
    const userInfoResponse = await axios.get(userInfoUrl, {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    });
    
    // Stockage des informations utilisateur dans la session
    req.session.userInfo = userInfoResponse.data;
    
    // Journalisation de la connexion réussie
    logSecurityEvent({
      type: 'authentication',
      action: 'login',
      status: 'success',
      user: userInfoResponse.data.preferred_username,
      ip: req.ip
    });
    
    // Redirection vers la page d'accueil
    res.redirect('/');
    
  } catch (error) {
    console.error('Erreur lors du traitement du callback:', error);
    
    // Journalisation de l'échec de connexion
    logSecurityEvent({
      type: 'authentication',
      action: 'login',
      status: 'failure',
      error: error.message,
      ip: req.ip
    });
    
    res.status(500).json({
      status: 'error',
      message: 'Erreur lors de l\'authentification'
    });
  }
});

/**
 * Rafraîchit le token d'accès
 */
router.post('/refresh-token', async (req, res) => {
  try {
    const { refreshToken } = req.body;
    
    if (!refreshToken) {
      return res.status(400).json({
        status: 'error',
        message: 'Token de rafraîchissement manquant'
      });
    }
    
    // Échange du token de rafraîchissement contre un nouveau token d'accès
    const tokenUrl = `http://${KEYCLOAK_HOST}:8080/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token`;
    
    const response = await axios.post(tokenUrl, 
      new URLSearchParams({
        'grant_type': 'refresh_token',
        'client_id': KEYCLOAK_CLIENT_ID,
        'client_secret': KEYCLOAK_CLIENT_SECRET,
        'refresh_token': refreshToken
      }).toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );
    
    // Récupération des nouveaux tokens
    const { access_token, refresh_token, expires_in } = response.data;
    
    // Journalisation du rafraîchissement réussi
    logSecurityEvent({
      type: 'authentication',
      action: 'token_refresh',
      status: 'success',
      ip: req.ip
    });
    
    // Retour des nouveaux tokens
    res.json({
      status: 'success',
      access_token,
      refresh_token,
      expires_in
    });
    
  } catch (error) {
    console.error('Erreur lors du rafraîchissement du token:', error);
    
    // Journalisation de l'échec de rafraîchissement
    logSecurityEvent({
      type: 'authentication',
      action: 'token_refresh',
      status: 'failure',
      error: error.message,
      ip: req.ip
    });
    
    res.status(401).json({
      status: 'error',
      message: 'Échec du rafraîchissement du token'
    });
  }
});

/**
 * Déconnecte l'utilisateur
 */
router.get('/logout', (req, res) => {
  // Récupération du token de la session
  const accessToken = req.session.accessToken;
  
  // Journalisation de la déconnexion
  if (req.session.userInfo) {
    logSecurityEvent({
      type: 'authentication',
      action: 'logout',
      status: 'success',
      user: req.session.userInfo.preferred_username,
      ip: req.ip
    });
  }
  
  // Destruction de la session
  req.session.destroy();
  
  // Construction de l'URL de déconnexion Keycloak
  const redirectUri = encodeURIComponent(`${req.protocol}://${req.get('host')}`);
  const logoutUrl = `http://${KEYCLOAK_HOST}:8080/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout?redirect_uri=${redirectUri}`;
  
  // Si un token est disponible, l'inclure dans la déconnexion
  if (accessToken) {
    res.redirect(`${logoutUrl}&id_token_hint=${accessToken}`);
  } else {
    res.redirect(logoutUrl);
  }
});

/**
 * Vérifie l'état de l'authentification
 */
router.get('/status', (req, res) => {
  // Vérification de l'existence d'un token valide
  if (req.session.accessToken && req.session.tokenExpiry && req.session.tokenExpiry > Date.now()) {
    return res.json({
      status: 'success',
      authenticated: true,
      user: req.session.userInfo
    });
  }
  
  res.json({
    status: 'success',
    authenticated: false
  });
});

module.exports = router;
