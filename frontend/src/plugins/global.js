import axios from 'axios';

// Configuration de base pour axios
axios.defaults.baseURL = process.env.VUE_APP_API_URL || 'http://localhost:8080/api';

// Composants communs
import AppHeader from '@/components/AppHeader.vue';
import AppFooter from '@/components/AppFooter.vue';
import ChatBubble from '@/components/ChatBubble.vue';
import ClientCard from '@/components/ClientCard.vue';
import LoadingOverlay from '@/components/LoadingOverlay.vue';
import NotificationSnackbar from '@/components/NotificationSnackbar.vue';

// Directives personnalisées
import ClickOutside from '@/directives/click-outside';
import Ripple from '@/directives/ripple';

// Filtres globaux
import { formatDate, formatCurrency, truncateText } from '@/filters';

export default {
  install(Vue) {
    // Enregistrement des composants globaux
    Vue.component('AppHeader', AppHeader);
    Vue.component('AppFooter', AppFooter);
    Vue.component('ChatBubble', ChatBubble);
    Vue.component('ClientCard', ClientCard);
    Vue.component('LoadingOverlay', LoadingOverlay);
    Vue.component('NotificationSnackbar', NotificationSnackbar);
    
    // Enregistrement des directives
    Vue.directive('click-outside', ClickOutside);
    Vue.directive('ripple', Ripple);
    
    // Enregistrement des filtres
    Vue.filter('formatDate', formatDate);
    Vue.filter('formatCurrency', formatCurrency);
    Vue.filter('truncateText', truncateText);
    
    // Configuration des intercepteurs axios
    axios.interceptors.request.use(
      config => {
        // Ajouter des en-têtes communs ou des paramètres à toutes les requêtes
        return config;
      },
      error => {
        return Promise.reject(error);
      }
    );
    
    axios.interceptors.response.use(
      response => {
        return response;
      },
      error => {
        // Gestion globale des erreurs
        if (error.response && error.response.status === 401) {
          // Rediriger vers la page de connexion en cas d'erreur d'authentification
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
    
    // Méthodes globales
    Vue.prototype.$notify = function(message, type = 'info', timeout = 3000) {
      this.$store.commit('SET_NOTIFICATION', { message, type, show: true, timeout });
    };
    
    Vue.prototype.$formatErrorMessage = function(error) {
      if (error.response && error.response.data && error.response.data.message) {
        return error.response.data.message;
      }
      return error.message || 'Une erreur est survenue';
    };
  }
};
