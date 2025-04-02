<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="headline">
            <v-icon large left color="primary">mdi-home</v-icon>
            Tableau de bord Agent
          </v-card-title>
          
          <v-card-text>
            <v-alert
              type="info"
              border="left"
              colored-border
              elevation="2"
              class="mb-4"
            >
              Bienvenue, {{ currentUser ? currentUser.name : 'Agent' }}. Vous êtes connecté en tant que {{ userRole }}.
            </v-alert>
            
            <v-row>
              <v-col cols="12" md="6" lg="3">
                <v-card outlined class="dashboard-card">
                  <v-card-title>Recherche client</v-card-title>
                  <v-card-text>
                    <p>Recherchez des clients par nom, prénom ou numéro de contrat.</p>
                  </v-card-text>
                  <v-card-actions>
                    <v-btn
                      color="primary"
                      to="/clients"
                      block
                    >
                      <v-icon left>mdi-account-search</v-icon>
                      Rechercher
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
              
              <v-col cols="12" md="6" lg="3">
                <v-card outlined class="dashboard-card">
                  <v-card-title>Conversation</v-card-title>
                  <v-card-text>
                    <p>Démarrez une nouvelle conversation avec le chatbot IA.</p>
                  </v-card-text>
                  <v-card-actions>
                    <v-btn
                      color="primary"
                      to="/chat"
                      block
                    >
                      <v-icon left>mdi-chat</v-icon>
                      Démarrer
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
              
              <v-col cols="12" md="6" lg="3">
                <v-card outlined class="dashboard-card">
                  <v-card-title>Historique</v-card-title>
                  <v-card-text>
                    <p>Consultez l'historique des conversations avec les clients.</p>
                  </v-card-text>
                  <v-card-actions>
                    <v-btn
                      color="primary"
                      to="/history"
                      block
                    >
                      <v-icon left>mdi-history</v-icon>
                      Consulter
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
              
              <v-col cols="12" md="6" lg="3" v-if="isSupervisor">
                <v-card outlined class="dashboard-card">
                  <v-card-title>Administration</v-card-title>
                  <v-card-text>
                    <p>Accédez aux fonctionnalités d'administration du système.</p>
                  </v-card-text>
                  <v-card-actions>
                    <v-btn
                      color="primary"
                      to="/admin"
                      block
                    >
                      <v-icon left>mdi-shield-account</v-icon>
                      Administrer
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
            </v-row>
            
            <v-divider class="my-6"></v-divider>
            
            <h3 class="text-h5 mb-4">Activité récente</h3>
            
            <v-data-table
              :headers="headers"
              :items="recentActivity"
              :items-per-page="5"
              class="elevation-1"
            >
              <template v-slot:item.date="{ item }">
                {{ formatDate(item.date) }}
              </template>
              
              <template v-slot:item.actions="{ item }">
                <v-btn
                  small
                  text
                  color="primary"
                  :to="`/clients/${item.client_id}`"
                >
                  <v-icon small>mdi-eye</v-icon>
                  Voir
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { mapGetters } from 'vuex';
import { hasRole } from '@/services/keycloak-service';
import moment from 'moment';

export default {
  name: 'HomeView',
  data() {
    return {
      headers: [
        { text: 'Date', value: 'date' },
        { text: 'Client', value: 'client_name' },
        { text: 'Type', value: 'type' },
        { text: 'Statut', value: 'status' },
        { text: 'Actions', value: 'actions', sortable: false }
      ],
      recentActivity: [
        {
          date: '2024-04-01T10:15:30Z',
          client_id: 42,
          client_name: 'Martin Sophie',
          type: 'Conversation',
          status: 'Terminée'
        },
        {
          date: '2024-04-01T09:45:12Z',
          client_id: 43,
          client_name: 'Dupont Jean',
          type: 'Réclamation',
          status: 'En cours'
        },
        {
          date: '2024-03-31T16:22:45Z',
          client_id: 44,
          client_name: 'Dubois Pierre',
          type: 'Conversation',
          status: 'Terminée'
        },
        {
          date: '2024-03-31T14:10:05Z',
          client_id: 45,
          client_name: 'Leroy Marie',
          type: 'Ticket',
          status: 'Résolu'
        },
        {
          date: '2024-03-30T11:35:18Z',
          client_id: 46,
          client_name: 'Bernard Thomas',
          type: 'Réclamation',
          status: 'Traitée'
        }
      ]
    };
  },
  computed: {
    ...mapGetters(['currentUser']),
    
    userRole() {
      if (!this.currentUser) return 'Agent';
      
      if (this.isSupervisor) return 'Superviseur';
      if (this.isSeniorAgent) return 'Agent Senior';
      return 'Agent Standard';
    },
    
    isSupervisor() {
      return hasRole('superviseur');
    },
    
    isSeniorAgent() {
      return hasRole('agent_senior');
    }
  },
  methods: {
    formatDate(dateString) {
      return moment(dateString).format('DD/MM/YYYY HH:mm');
    }
  }
};
</script>

<style scoped>
.dashboard-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.dashboard-card .v-card__text {
  flex-grow: 1;
}
</style>
