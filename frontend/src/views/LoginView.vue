<template>
  <v-container fluid class="login-container">
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card elevation="10" class="login-card">
          <v-card-title class="text-center">
            <h1 class="text-h4 primary--text">AssurSanté</h1>
            <h2 class="text-subtitle-1">Portail Agent - Chatbot IA</h2>
          </v-card-title>
          
          <v-card-text>
            <v-alert
              v-if="loginError"
              type="error"
              dismissible
              class="mb-4"
            >
              {{ loginError }}
            </v-alert>
            
            <v-img
              src="/img/assursante-logo.png"
              alt="AssurSanté Logo"
              contain
              height="120"
              class="mb-6"
            ></v-img>
            
            <p class="text-center mb-6">
              Veuillez vous connecter pour accéder au système de chatbot IA.
            </p>
            
            <v-btn
              block
              color="primary"
              size="large"
              @click="login"
              :loading="isLoading"
            >
              <v-icon left>mdi-login</v-icon>
              Se connecter
            </v-btn>
          </v-card-text>
          
          <v-card-actions class="justify-center pb-6">
            <v-btn
              text
              color="grey"
              @click="showHelp = true"
            >
              Besoin d'aide ?
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    
    <v-dialog v-model="showHelp" max-width="500">
      <v-card>
        <v-card-title>Aide à la connexion</v-card-title>
        <v-card-text>
          <p>Pour vous connecter au système de chatbot IA d'AssurSanté :</p>
          <ol>
            <li>Cliquez sur le bouton "Se connecter"</li>
            <li>Entrez vos identifiants d'agent AssurSanté</li>
            <li>Suivez les instructions pour l'authentification à deux facteurs</li>
          </ol>
          <p>Si vous rencontrez des difficultés, veuillez contacter le support technique au 01 23 45 67 89.</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="showHelp = false">
            Fermer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mapGetters, mapMutations } from 'vuex';
import { login } from '@/services/keycloak-service';

export default {
  name: 'LoginView',
  data() {
    return {
      loginError: null,
      showHelp: false
    };
  },
  computed: {
    ...mapGetters(['isLoading', 'isAuthenticated'])
  },
  methods: {
    ...mapMutations(['SET_LOADING']),
    
    login() {
      this.SET_LOADING(true);
      this.loginError = null;
      
      try {
        login();
      } catch (error) {
        this.loginError = "Erreur lors de la connexion. Veuillez réessayer.";
        this.SET_LOADING(false);
      }
    }
  },
  created() {
    // Si l'utilisateur est déjà authentifié, rediriger vers la page d'accueil
    if (this.isAuthenticated) {
      this.$router.push('/');
    }
  }
};
</script>

<style scoped>
.login-container {
  height: 100%;
  display: flex;
  align-items: center;
  background-color: #f5f5f5;
}

.login-card {
  padding: 20px;
}
</style>
