// Implémentation de l'anonymisation des données sensibles
// Ce fichier contient les fonctions pour masquer automatiquement les données de santé sensibles

/**
 * Types de données sensibles à anonymiser
 */
const SENSITIVE_DATA_PATTERNS = {
  // Numéro de sécurité sociale (format français)
  NUMERO_SECU: /\b([1-2])\s*([0-9]{2})\s*([0-9]{2})\s*([0-9]{2})\s*([0-9]{3})\s*([0-9]{3})\s*([0-9]{2})\b/g,
  
  // Adresse email
  EMAIL: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g,
  
  // Numéro de téléphone (format français)
  TELEPHONE: /\b0[1-9](?:[\s.-]?[0-9]{2}){4}\b/g,
  
  // Données médicales sensibles
  DIAGNOSTIC: /\b(?:diagnostic|pathologie|maladie)\s*(?:de|:|d[e'])\s*([A-Za-z\s\-']+)\b/gi,
  TRAITEMENT: /\b(?:traitement|médicament|prescription)\s*(?:de|:|d[e'])\s*([A-Za-z\s\-']+)\b/gi,
  
  // Codes d'actes médicaux
  CODE_ACTE: /\b[A-Z]{4}[0-9]{3}\b/g
};

/**
 * Anonymise les données sensibles dans un texte
 * @param {string} text - Texte à anonymiser
 * @returns {string} - Texte anonymisé
 */
function anonymizeText(text) {
  if (!text || typeof text !== 'string') {
    return text;
  }
  
  let anonymizedText = text;
  
  // Anonymisation du numéro de sécurité sociale
  anonymizedText = anonymizedText.replace(
    SENSITIVE_DATA_PATTERNS.NUMERO_SECU, 
    (match, g1, g2, g3, g4, g5, g6, g7) => `${g1}${g2}***********`
  );
  
  // Anonymisation des emails
  anonymizedText = anonymizedText.replace(
    SENSITIVE_DATA_PATTERNS.EMAIL,
    (match) => {
      const [localPart, domain] = match.split('@');
      return `${localPart.substring(0, 3)}***@${domain}`;
    }
  );
  
  // Anonymisation des numéros de téléphone
  anonymizedText = anonymizedText.replace(
    SENSITIVE_DATA_PATTERNS.TELEPHONE,
    (match) => match.substring(0, 4) + '******'
  );
  
  // Anonymisation des diagnostics
  anonymizedText = anonymizedText.replace(
    SENSITIVE_DATA_PATTERNS.DIAGNOSTIC,
    (match, diagnosis) => match.replace(diagnosis, '[DIAGNOSTIC MASQUÉ]')
  );
  
  // Anonymisation des traitements
  anonymizedText = anonymizedText.replace(
    SENSITIVE_DATA_PATTERNS.TRAITEMENT,
    (match, treatment) => match.replace(treatment, '[TRAITEMENT MASQUÉ]')
  );
  
  // Anonymisation des codes d'actes médicaux
  anonymizedText = anonymizedText.replace(
    SENSITIVE_DATA_PATTERNS.CODE_ACTE,
    '[CODE ACTE MASQUÉ]'
  );
  
  return anonymizedText;
}

/**
 * Anonymise les données sensibles dans un objet
 * @param {object} data - Objet à anonymiser
 * @returns {object} - Objet anonymisé
 */
function anonymizeObject(data) {
  if (!data) return data;
  
  // Cas des tableaux
  if (Array.isArray(data)) {
    return data.map(item => anonymizeObject(item));
  }
  
  // Cas des objets
  if (typeof data === 'object') {
    const result = { ...data };
    
    // Traitement spécifique pour certains champs connus
    if (result.numero_securite_sociale && typeof result.numero_securite_sociale === 'string') {
      result.numero_securite_sociale = result.numero_securite_sociale.substring(0, 3) + '***********';
    }
    
    if (result.email && typeof result.email === 'string') {
      const [localPart, domain] = result.email.split('@');
      result.email = `${localPart.substring(0, 3)}***@${domain}`;
    }
    
    if (result.telephone && typeof result.telephone === 'string') {
      result.telephone = result.telephone.substring(0, 4) + '******';
    }
    
    if (result.diagnostic && typeof result.diagnostic === 'string') {
      result.diagnostic = '[DIAGNOSTIC MASQUÉ]';
    }
    
    if (result.traitement && typeof result.traitement === 'string') {
      result.traitement = '[TRAITEMENT MASQUÉ]';
    }
    
    // Traitement récursif pour les propriétés imbriquées
    for (const key in result) {
      if (typeof result[key] === 'object' && result[key] !== null) {
        result[key] = anonymizeObject(result[key]);
      } else if (typeof result[key] === 'string') {
        // Anonymisation des chaînes de caractères
        result[key] = anonymizeText(result[key]);
      }
    }
    
    return result;
  }
  
  // Cas des chaînes de caractères
  if (typeof data === 'string') {
    return anonymizeText(data);
  }
  
  // Autres types de données (nombre, booléen, etc.)
  return data;
}

/**
 * Middleware Express pour anonymiser les réponses API
 * @returns {Function} - Middleware Express
 */
function anonymizeResponseMiddleware() {
  return (req, res, next) => {
    // Sauvegarde de la fonction json d'origine
    const originalJson = res.json;
    
    // Remplacement par une version qui anonymise les données
    res.json = function(data) {
      // Anonymisation des données
      const anonymizedData = anonymizeObject(data);
      
      // Appel de la fonction d'origine avec les données anonymisées
      return originalJson.call(this, anonymizedData);
    };
    
    next();
  };
}

module.exports = {
  anonymizeText,
  anonymizeObject,
  anonymizeResponseMiddleware
};
