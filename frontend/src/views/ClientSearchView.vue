<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="headline">
            <v-icon large left color="primary">mdi-account-search</v-icon>
            Recherche de clients
          </v-card-title>
          
          <v-card-text>
            <v-form @submit.prevent="searchClients">
              <v-row>
                <v-col cols="12" md="8">
                  <v-text-field
                    v-model="searchQuery"
                    label="Rechercher un client"
                    placeholder="Nom, prénom, numéro de contrat ou numéro de sécurité sociale"
                    prepend-icon="mdi-magnify"
                    clearable
                    @keyup.enter="searchClients"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="4">
                  <v-btn
                    color="primary"
                    block
                    :loading="isLoading"
                    @click="searchClients"
                    :disabled="!searchQuery"
                  >
                    <v-icon left>mdi-magnify</v-icon>
                    Rechercher
                  </v-btn>
                </v-col>
              </v-row>
            </v-form>
            
            <v-alert
              v-if="searchPerformed && clients.length === 0"
              type="info"
              border="left"
              colored-border
              elevation="2"
              class="mt-4"
            >
              Aucun client trouvé pour la recherche "{{ lastSearchQuery }}".
            </v-alert>
            
            <v-data-table
              v-if="clients.length > 0"
              :headers="headers"
              :items="clients"
              :items-per-page="10"
              class="elevation-1 mt-4"
            >
              <template v-slot:item.actions="{ item }">
                <v-btn
                  small
                  color="primary"
                  :to="`/clients/${item.id}`"
                >
                  <v-icon small left>mdi-eye</v-icon>
                  Détails
                </v-btn>
                <v-btn
                  small
                  color="success"
                  @click="startChat(item)"
                  class="ml-2"
                >
                  <v-icon small left>mdi-chat</v-icon>
                  Chat
                </v-btn>
              </template>
              
              <template v-slot:item.contrats="{ item }">
                <v-chip
                  v-for="(contrat, index) in item.contrats"
                  :key="index"
                  small
                  :color="getContractColor(contrat.niveau_couverture)"
                  text-color="white"
                  class="mr-1"
                >
                  {{ contrat.niveau_couverture }}
                </v-chip>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <v-dialog v-model="showChatDialog" max-width="500">
      <v-card>
        <v-card-title>Démarrer une conversation</v-card-title>
        <v-card-text>
          <p>Vous êtes sur le point de démarrer une conversation avec le client :</p>
          <v-list>
            <v-list-item>
              <v-list-item-icon>
                <v-icon>mdi-account</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>{{ selectedClient ? `${selectedClient.prenom} ${selectedClient.nom}` : '' }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
            
            <v-list-item v-if="selectedClient && selectedClient.contrats && selectedClient.contrats.length > 0">
              <v-list-item-icon>
                <v-icon>mdi-file-document</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>{{ selectedClient.contrats[0].type_contrat }}</v-list-item-title>
                <v-list-item-subtitle>{{ selectedClient.contrats[0].niveau_couverture }}</v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" text @click="showChatDialog = false">
            Annuler
          </v-btn>
          <v-btn color="primary" @click="confirmStartChat">
            Démarrer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  name: 'ClientSearchView',
  data() {
    return {
      searchQuery: '',
      lastSearchQuery: '',
      searchPerformed: false,
      headers: [
        { text: 'Nom', value: 'nom' },
        { text: 'Prénom', value: 'prenom' },
        { text: 'Email', value: 'email' },
        { text: 'Téléphone', value: 'telephone' },
        { text: 'Contrats', value: 'contrats' },
        { text: 'Actions', value: 'actions', sortable: false }
      ],
      showChatDialog: false,
      selectedClient: null
    };
  },
  computed: {
    ...mapGetters(['clients', 'isLoading'])
  },
  methods: {
    ...mapActions(['searchClients', 'createChatSession']),
    
    async searchClients() {
      if (!this.searchQuery) return;
      
      this.lastSearchQuery = this.searchQuery;
      this.searchPerformed = true;
      
      try {
        await this.searchClients(this.searchQuery);
      } catch (error) {
        console.error('Erreur lors de la recherche des clients:', error);
      }
    },
    
    getContractColor(level) {
      switch (level) {
        case 'Premium':
          return 'purple';
        case 'Confort':
          return 'blue';
        case 'Essentiel':
          return 'green';
        default:
          return 'grey';
      }
    },
    
    startChat(client) {
      this.selectedClient = client;
      this.showChatDialog = true;
    },
    
    async confirmStartChat() {
      this.showChatDialog = false;
      
      try {
        await this.createChatSession(this.selectedClient.id);
        this.$router.push('/chat');
      } catch (error) {
        console.error('Erreur lors de la création de la session de chat:', error);
      }
    }
  }
};
</script>

<style scoped>
/* Styles spécifiques à la vue de recherche client */
</style>
