import { createStore } from 'vuex';
import axios from 'axios';
import { getToken } from '../services/keycloak-service';

export default createStore({
  state: {
    user: null,
    clients: [],
    selectedClient: null,
    chatHistory: [],
    currentSession: null,
    isLoading: false,
    error: null
  },
  getters: {
    isAuthenticated: state => !!state.user,
    currentUser: state => state.user,
    clients: state => state.clients,
    selectedClient: state => state.selectedClient,
    chatHistory: state => state.chatHistory,
    currentSession: state => state.currentSession,
    isLoading: state => state.isLoading,
    hasError: state => !!state.error,
    errorMessage: state => state.error
  },
  mutations: {
    SET_USER(state, user) {
      state.user = user;
    },
    SET_CLIENTS(state, clients) {
      state.clients = clients;
    },
    SET_SELECTED_CLIENT(state, client) {
      state.selectedClient = client;
    },
    SET_CHAT_HISTORY(state, history) {
      state.chatHistory = history;
    },
    ADD_CHAT_MESSAGE(state, message) {
      state.chatHistory.push(message);
    },
    SET_CURRENT_SESSION(state, session) {
      state.currentSession = session;
    },
    SET_LOADING(state, isLoading) {
      state.isLoading = isLoading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
    CLEAR_ERROR(state) {
      state.error = null;
    }
  },
  actions: {
    // Action pour définir l'utilisateur courant
    setUser({ commit }, user) {
      commit('SET_USER', user);
    },
    
    // Action pour rechercher des clients
    async searchClients({ commit, state }, query) {
      try {
        commit('SET_LOADING', true);
        commit('CLEAR_ERROR');
        
        const response = await axios.get(`/api/look/v1/clients/search?query=${query}`, {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });
        
        commit('SET_CLIENTS', response.data.data);
        return response.data.data;
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.message || 'Erreur lors de la recherche des clients');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    // Action pour récupérer les détails d'un client
    async getClientDetails({ commit }, clientId) {
      try {
        commit('SET_LOADING', true);
        commit('CLEAR_ERROR');
        
        const response = await axios.get(`/api/look/v1/clients/${clientId}`, {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });
        
        commit('SET_SELECTED_CLIENT', response.data.data);
        return response.data.data;
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.message || 'Erreur lors de la récupération des détails du client');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    // Action pour créer une nouvelle session de chat
    async createChatSession({ commit, state }, clientId) {
      try {
        commit('SET_LOADING', true);
        commit('CLEAR_ERROR');
        
        const response = await axios.post('/api/memory/v1/sessions', {
          agent_id: state.user.id,
          client_id: clientId,
          metadata: {
            source: 'agent_web_interface',
            browser: navigator.userAgent
          }
        }, {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });
        
        commit('SET_CURRENT_SESSION', response.data.data);
        commit('SET_CHAT_HISTORY', []);
        return response.data.data;
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.message || 'Erreur lors de la création de la session de chat');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    // Action pour envoyer un message au chatbot
    async sendMessage({ commit, state }, message) {
      try {
        commit('SET_LOADING', true);
        commit('CLEAR_ERROR');
        
        // Ajouter le message de l'utilisateur à l'historique
        const userMessage = {
          role: 'user',
          content: message,
          timestamp: new Date().toISOString()
        };
        commit('ADD_CHAT_MESSAGE', userMessage);
        
        // Envoyer le message à l'API
        const response = await axios.post(`/api/memory/v1/sessions/${state.currentSession.session_id}/messages`, userMessage, {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });
        
        // Attendre la réponse du chatbot
        const botResponse = await axios.post('/api/look/v1/chat', {
          session_id: state.currentSession.session_id,
          client_id: state.selectedClient.id,
          message: message
        }, {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });
        
        // Ajouter la réponse du chatbot à l'historique
        const botMessage = {
          role: 'assistant',
          content: botResponse.data.response,
          timestamp: new Date().toISOString()
        };
        commit('ADD_CHAT_MESSAGE', botMessage);
        
        return botResponse.data;
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.message || 'Erreur lors de l\'envoi du message');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    // Action pour récupérer l'historique des conversations
    async getChatHistory({ commit }, clientId) {
      try {
        commit('SET_LOADING', true);
        commit('CLEAR_ERROR');
        
        const response = await axios.get(`/api/memory/v1/sessions?client_id=${clientId}`, {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        });
        
        return response.data.data;
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.message || 'Erreur lors de la récupération de l\'historique des conversations');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    }
  }
});
