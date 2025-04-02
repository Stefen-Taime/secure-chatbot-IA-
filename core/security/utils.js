// Utilitaires de sécurité pour le chatbot IA
// Ce fichier contient des fonctions pour le chiffrement, la gestion des secrets et la journalisation

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const hvac = require('hvac');

// Variables d'environnement
const VAULT_ADDR = process.env.VAULT_ADDR || 'http://vault:8200';
const VAULT_TOKEN = process.env.VAULT_DEV_ROOT_TOKEN_ID || 'vault_root_token_123';

/**
 * Client Vault pour la gestion des secrets
 */
const vaultClient = hvac.Client({
  url: VAULT_ADDR,
  token: VAULT_TOKEN
});

/**
 * Récupère un secret depuis Vault
 * @param {string} secretPath - Chemin du secret dans Vault
 * @returns {Promise<object>} - Données du secret
 */
async function getSecret(secretPath) {
  try {
    if (!vaultClient.isAuthenticated()) {
      throw new Error('Échec d\'authentification à Vault');
    }
    
    const secretResponse = await vaultClient.secrets.kv.v2.readSecretVersion({
      path: secretPath
    });
    
    return secretResponse.data.data;
  } catch (error) {
    console.error(`Erreur lors de la récupération du secret ${secretPath}:`, error);
    throw error;
  }
}

/**
 * Stocke un secret dans Vault
 * @param {string} secretPath - Chemin du secret dans Vault
 * @param {object} secretData - Données du secret
 * @returns {Promise<boolean>} - Succès de l'opération
 */
async function storeSecret(secretPath, secretData) {
  try {
    if (!vaultClient.isAuthenticated()) {
      throw new Error('Échec d\'authentification à Vault');
    }
    
    await vaultClient.secrets.kv.v2.createOrUpdateSecret({
      path: secretPath,
      data: secretData
    });
    
    return true;
  } catch (error) {
    console.error(`Erreur lors du stockage du secret ${secretPath}:`, error);
    throw error;
  }
}

/**
 * Chiffre une donnée sensible
 * @param {string} data - Donnée à chiffrer
 * @param {string} key - Clé de chiffrement
 * @returns {string} - Donnée chiffrée (format: iv:encrypted)
 */
function encryptData(data, key) {
  // Génération d'un vecteur d'initialisation aléatoire
  const iv = crypto.randomBytes(16);
  
  // Création du chiffreur
  const cipher = crypto.createCipheriv('aes-256-gcm', Buffer.from(key, 'hex'), iv);
  
  // Chiffrement des données
  let encrypted = cipher.update(data, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  // Récupération du tag d'authentification
  const authTag = cipher.getAuthTag().toString('hex');
  
  // Retour du résultat au format iv:encrypted:authTag
  return `${iv.toString('hex')}:${encrypted}:${authTag}`;
}

/**
 * Déchiffre une donnée sensible
 * @param {string} encryptedData - Donnée chiffrée (format: iv:encrypted:authTag)
 * @param {string} key - Clé de chiffrement
 * @returns {string} - Donnée déchiffrée
 */
function decryptData(encryptedData, key) {
  // Séparation des composants
  const [ivHex, encrypted, authTagHex] = encryptedData.split(':');
  
  // Conversion des composants
  const iv = Buffer.from(ivHex, 'hex');
  const authTag = Buffer.from(authTagHex, 'hex');
  
  // Création du déchiffreur
  const decipher = crypto.createDecipheriv('aes-256-gcm', Buffer.from(key, 'hex'), iv);
  decipher.setAuthTag(authTag);
  
  // Déchiffrement des données
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
}

/**
 * Génère une clé de chiffrement aléatoire
 * @returns {string} - Clé de chiffrement en hexadécimal
 */
function generateEncryptionKey() {
  return crypto.randomBytes(32).toString('hex');
}

/**
 * Journalise une action de sécurité
 * @param {object} logData - Données à journaliser
 * @returns {Promise<void>}
 */
async function logSecurityEvent(logData) {
  try {
    // Ajout de l'horodatage
    const logEntry = {
      ...logData,
      timestamp: new Date().toISOString()
    };
    
    // Formatage du log
    const logString = JSON.stringify(logEntry);
    
    // Écriture dans le fichier de log
    const logDir = path.join(__dirname, '../../logs');
    
    // Création du répertoire de logs s'il n'existe pas
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    const logFile = path.join(logDir, 'security.log');
    
    fs.appendFileSync(logFile, logString + '\n');
    
    // En production, on pourrait envoyer les logs à Elasticsearch via Logstash
    // Cette partie serait implémentée ici
    
  } catch (error) {
    console.error('Erreur lors de la journalisation de l\'événement de sécurité:', error);
  }
}

/**
 * Vérifie la complexité d'un mot de passe
 * @param {string} password - Mot de passe à vérifier
 * @returns {object} - Résultat de la vérification
 */
function checkPasswordStrength(password) {
  const result = {
    isStrong: false,
    score: 0,
    feedback: []
  };
  
  // Vérification de la longueur
  if (password.length < 8) {
    result.feedback.push('Le mot de passe doit contenir au moins 8 caractères');
  } else {
    result.score += 1;
  }
  
  // Vérification des lettres minuscules
  if (!/[a-z]/.test(password)) {
    result.feedback.push('Le mot de passe doit contenir au moins une lettre minuscule');
  } else {
    result.score += 1;
  }
  
  // Vérification des lettres majuscules
  if (!/[A-Z]/.test(password)) {
    result.feedback.push('Le mot de passe doit contenir au moins une lettre majuscule');
  } else {
    result.score += 1;
  }
  
  // Vérification des chiffres
  if (!/[0-9]/.test(password)) {
    result.feedback.push('Le mot de passe doit contenir au moins un chiffre');
  } else {
    result.score += 1;
  }
  
  // Vérification des caractères spéciaux
  if (!/[^A-Za-z0-9]/.test(password)) {
    result.feedback.push('Le mot de passe doit contenir au moins un caractère spécial');
  } else {
    result.score += 1;
  }
  
  // Détermination de la force du mot de passe
  result.isStrong = result.score >= 4;
  
  return result;
}

/**
 * Génère un hash sécurisé d'un mot de passe
 * @param {string} password - Mot de passe à hasher
 * @returns {Promise<string>} - Hash du mot de passe
 */
async function hashPassword(password) {
  return new Promise((resolve, reject) => {
    // Génération d'un sel aléatoire
    crypto.randomBytes(16, (err, salt) => {
      if (err) {
        return reject(err);
      }
      
      // Hachage du mot de passe avec PBKDF2
      crypto.pbkdf2(password, salt, 10000, 64, 'sha512', (err, derivedKey) => {
        if (err) {
          return reject(err);
        }
        
        // Format: iterations:salt:hash
        resolve(`10000:${salt.toString('hex')}:${derivedKey.toString('hex')}`);
      });
    });
  });
}

/**
 * Vérifie un mot de passe par rapport à son hash
 * @param {string} password - Mot de passe à vérifier
 * @param {string} hashedPassword - Hash du mot de passe
 * @returns {Promise<boolean>} - Validité du mot de passe
 */
async function verifyPassword(password, hashedPassword) {
  return new Promise((resolve, reject) => {
    // Extraction des composants du hash
    const [iterations, saltHex, hashHex] = hashedPassword.split(':');
    const salt = Buffer.from(saltHex, 'hex');
    
    // Hachage du mot de passe fourni avec les mêmes paramètres
    crypto.pbkdf2(password, salt, parseInt(iterations), 64, 'sha512', (err, derivedKey) => {
      if (err) {
        return reject(err);
      }
      
      // Comparaison des hash
      resolve(derivedKey.toString('hex') === hashHex);
    });
  });
}

module.exports = {
  getSecret,
  storeSecret,
  encryptData,
  decryptData,
  generateEncryptionKey,
  logSecurityEvent,
  checkPasswordStrength,
  hashPassword,
  verifyPassword
};
