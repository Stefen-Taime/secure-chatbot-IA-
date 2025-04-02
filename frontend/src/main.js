import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import 'vuetify/styles';
import { initKeycloak } from './services/keycloak-service';

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        dark: false,
        colors: {
          primary: '#1976D2',
          secondary: '#424242',
          accent: '#82B1FF',
          error: '#FF5252',
          info: '#2196F3',
          success: '#4CAF50',
          warning: '#FFC107',
        }
      }
    }
  }
});

// Initialiser Keycloak avant de monter l'application
initKeycloak().then(() => {
  createApp(App)
    .use(store)
    .use(router)
    .use(vuetify)
    .mount('#app');
}).catch(error => {
  console.error('Erreur lors de l\'initialisation de Keycloak:', error);
  // Afficher un message d'erreur à l'utilisateur
  document.getElementById('app').innerHTML = `
    <div style="text-align: center; margin-top: 50px;">
      <h1>Erreur de connexion</h1>
      <p>Impossible de se connecter au service d'authentification. Veuillez réessayer ultérieurement.</p>
    </div>
  `;
});
