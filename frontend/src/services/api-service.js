import axios from 'axios';
import { getToken } from './keycloak-service';

// Création d'une instance axios avec une configuration de base
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8080/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Intercepteur pour ajouter le token d'authentification à chaque requête
apiClient.interceptors.request.use(
  config => {
    const token = getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Service pour l'API Look
export const lookService = {
  // Recherche de clients
  searchClients(query, limit = 10) {
    return apiClient.get(`/look/v1/clients/search?query=${query}&limit=${limit}`);
  },
  
  // Récupération des détails d'un client
  getClientDetails(clientId) {
    return apiClient.get(`/look/v1/clients/${clientId}`);
  },
  
  // Recherche de réclamations
  searchClaims(query, clientId = null, status = null, limit = 10) {
    let url = `/look/v1/claims/search?query=${query}&limit=${limit}`;
    if (clientId) url += `&client_id=${clientId}`;
    if (status) url += `&status=${status}`;
    return apiClient.get(url);
  },
  
  // Recherche dans la base de connaissances
  searchKnowledge(query, category = null, limit = 5) {
    let url = `/look/v1/knowledge/search?query=${query}&limit=${limit}`;
    if (category) url += `&category=${category}`;
    return apiClient.get(url);
  },
  
  // Recherche combinée
  combinedSearch(query, clientId = null, limit = 10) {
    let url = `/look/v1/combined-search?query=${query}&limit=${limit}`;
    if (clientId) url += `&client_id=${clientId}`;
    return apiClient.get(url);
  },
  
  // Envoi d'un message au chatbot
  sendChatMessage(sessionId, clientId, message) {
    return apiClient.post(`/look/v1/chat`, {
      session_id: sessionId,
      client_id: clientId,
      message: message
    });
  }
};

// Service pour l'API Tools
export const toolsService = {
  // Création d'un ticket
  createTicket(ticket) {
    return apiClient.post('/tools/v1/tickets', ticket);
  },
  
  // Création d'une réclamation
  createClaim(claim) {
    return apiClient.post('/tools/v1/claims', claim);
  },
  
  // Mise à jour d'une réclamation
  updateClaim(claimId, updates) {
    return apiClient.put(`/tools/v1/claims/${claimId}`, updates);
  },
  
  // Simulation d'envoi d'email
  simulateEmail(emailData) {
    return apiClient.post('/tools/v1/emails/simulate', emailData);
  }
};

// Service pour l'API Memory
export const memoryService = {
  // Création d'une session
  createSession(agentId, clientId, metadata = {}) {
    return apiClient.post('/memory/v1/sessions', {
      agent_id: agentId,
      client_id: clientId,
      metadata: metadata
    });
  },
  
  // Ajout d'un message à une session
  addMessage(sessionId, message) {
    return apiClient.post(`/memory/v1/sessions/${sessionId}/messages`, message);
  },
  
  // Récupération de l'historique des messages
  getMessages(sessionId, limit = 50) {
    return apiClient.get(`/memory/v1/sessions/${sessionId}/messages?limit=${limit}`);
  },
  
  // Mise à jour du contexte d'une session
  updateContext(sessionId, context) {
    return apiClient.put(`/memory/v1/sessions/${sessionId}/context`, context);
  },
  
  // Récupération du contexte d'une session
  getContext(sessionId) {
    return apiClient.get(`/memory/v1/sessions/${sessionId}/context`);
  },
  
  // Récupération des sessions d'un client
  getClientSessions(clientId) {
    return apiClient.get(`/memory/v1/sessions?client_id=${clientId}`);
  }
};

// Service pour l'API Output
export const outputService = {
  // Génération d'une réponse structurée
  generateResponse(rawContent, format, template, clientId) {
    return apiClient.post('/output/v1/responses/generate', {
      raw_content: rawContent,
      format: format,
      template: template,
      client_id: clientId
    });
  },
  
  // Conversion de format
  convertFormat(content, sourceFormat, targetFormat) {
    return apiClient.post('/output/v1/responses/convert', {
      content: content,
      source_format: sourceFormat,
      target_format: targetFormat
    });
  },
  
  // Génération d'email à partir de template
  renderEmail(template, variables, format = 'html') {
    return apiClient.post('/output/v1/emails/render', {
      template: template,
      variables: variables,
      format: format
    });
  },
  
  // Anonymisation de données sensibles
  anonymizeContent(content, level = 'standard', preserveFormat = true) {
    return apiClient.post('/output/v1/anonymize', {
      content: content,
      anonymization_level: level,
      preserve_format: preserveFormat
    });
  }
};
