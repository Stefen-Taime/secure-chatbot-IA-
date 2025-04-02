<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>AssurSanté - Chatbot IA</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn v-if="isAuthenticated" icon @click="showUserInfo = true">
        <v-icon>mdi-account-circle</v-icon>
      </v-btn>
      <v-btn v-if="isAuthenticated" text @click="logout">
        <v-icon left>mdi-logout</v-icon>
        Déconnexion
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" app temporary>
      <v-list>
        <v-list-item to="/" exact>
          <v-list-item-icon>
            <v-icon>mdi-home</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Accueil</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        
        <v-list-item to="/clients">
          <v-list-item-icon>
            <v-icon>mdi-account-search</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Recherche clients</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        
        <v-list-item to="/chat">
          <v-list-item-icon>
            <v-icon>mdi-chat</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Chat</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        
        <v-list-item to="/history">
          <v-list-item-icon>
            <v-icon>mdi-history</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title>Historique</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid>
        <v-alert
          v-if="error"
          type="error"
          dismissible
          @click="clearError"
        >
          {{ error }}
        </v-alert>
        <router-view></router-view>
      </v-container>
    </v-main>

    <v-dialog v-model="showUserInfo" max-width="400">
      <v-card>
        <v-card-title>Informations utilisateur</v-card-title>
        <v-card-text v-if="currentUser">
          <v-list>
            <v-list-item>
              <v-list-item-icon>
                <v-icon>mdi-account</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>{{ currentUser.name }}</v-list-item-title>
                <v-list-item-subtitle>{{ currentUser.username }}</v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
            
            <v-list-item>
              <v-list-item-icon>
                <v-icon>mdi-email</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>{{ currentUser.email }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            
            <v-list-item>
              <v-list-item-icon>
                <v-icon>mdi-shield-account</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>Rôles</v-list-item-title>
                <v-list-item-subtitle>{{ currentUser.roles.join(', ') }}</v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="showUserInfo = false">
            Fermer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-overlay :value="isLoading">
      <v-progress-circular indeterminate size="64"></v-progress-circular>
    </v-overlay>
  </v-app>
</template>

<script>
import { mapGetters, mapMutations, mapActions } from 'vuex';
import { getUserInfo, logout } from './services/keycloak-service';

export default {
  name: 'App',
  data() {
    return {
      drawer: false,
      showUserInfo: false
    };
  },
  computed: {
    ...mapGetters(['isLoading', 'error', 'isAuthenticated', 'currentUser'])
  },
  methods: {
    ...mapMutations(['SET_USER', 'CLEAR_ERROR']),
    ...mapActions(['setUser']),
    
    clearError() {
      this.CLEAR_ERROR();
    },
    
    logout() {
      logout().then(() => {
        this.SET_USER(null);
        this.$router.push('/login');
      });
    }
  },
  created() {
    // Récupérer les informations de l'utilisateur si authentifié
    const userInfo = getUserInfo();
    if (userInfo) {
      this.setUser(userInfo);
    }
  }
};
</script>

<style>
.v-application {
  font-family: 'Roboto', sans-serif;
}
</style>
