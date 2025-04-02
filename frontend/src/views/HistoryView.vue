<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="headline">
            <v-icon large left color="primary">mdi-history</v-icon>
            Historique des conversations
          </v-card-title>
          
          <v-card-text>
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="searchQuery"
                  label="Rechercher un client"
                  prepend-icon="mdi-magnify"
                  clearable
                  @keyup.enter="searchClients"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="3">
                <v-select
                  v-model="dateFilter"
                  :items="dateFilterOptions"
                  label="Période"
                  prepend-icon="mdi-calendar"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3">
                <v-btn
                  color="primary"
                  block
                  @click="searchSessions"
                  :loading="isLoading"
                >
                  <v-icon left>mdi-magnify</v-icon>
                  Rechercher
                </v-btn>
              </v-col>
            </v-row>
            
            <v-data-table
              :headers="headers"
              :items="sessions"
              :items-per-page="10"
              class="elevation-1 mt-4"
              :loading="isLoading"
              :no-data-text="noDataText"
            >
              <template v-slot:item.client="{ item }">
                {{ item.client_name }}
              </template>
              
              <template v-slot:item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>
              
              <template v-slot:item.message_count="{ item }">
                {{ item.message_count }}
              </template>
              
              <template v-slot:item.status="{ item }">
                <v-chip
                  small
                  :color="item.status === 'active' ? 'success' : 'grey'"
                  text-color="white"
                >
                  {{ item.status === 'active' ? 'Active' : 'Terminée' }}
                </v-chip>
              </template>
              
              <template v-slot:item.actions="{ item }">
                <v-btn
                  small
                  color="primary"
                  @click="viewSession(item)"
                >
                  <v-icon small left>mdi-eye</v-icon>
                  Voir
                </v-btn>
                <v-btn
                  small
                  color="success"
                  class="ml-2"
                  @click="resumeSession(item)"
                  v-if="item.status === 'active'"
                >
                  <v-icon small left>mdi-chat</v-icon>
                  Reprendre
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <v-dialog v-model="showSessionDialog" max-width="800">
      <v-card>
        <v-card-title>
          Conversation avec {{ selectedSession ? selectedSession.client_name : '' }}
          <v-spacer></v-spacer>
          <v-chip
            small
            :color="selectedSession && selectedSession.status === 'active' ? 'success' : 'grey'"
            text-color="white"
          >
            {{ selectedSession && selectedSession.status === 'active' ? 'Active' : 'Terminée' }}
          </v-chip>
        </v-card-title>
        <v-card-subtitle>
          {{ selectedSession ? formatDate(selectedSession.created_at) : '' }}
        </v-card-subtitle>
        
        <v-card-text>
          <div class="session-messages">
            <div
              v-for="(message, index) in sessionMessages"
              :key="index"
              :class="['message', message.role === 'user' ? 'message-user' : 'message-assistant']"
            >
              <div class="message-content">
                <div class="message-header">
                  <strong>{{ message.role === 'user' ? selectedSession.client_name : 'Assistant IA' }}</strong>
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                </div>
                <div class="message-body">{{ message.content }}</div>
              </div>
            </div>
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-btn
            color="primary"
            @click="resumeSession(selectedSession)"
            v-if="selectedSession && selectedSession.status === 'active'"
          >
            <v-icon left>mdi-chat</v-icon>
            Reprendre la conversation
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="grey"
            text
            @click="showSessionDialog = false"
          >
            Fermer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mapGetters } from 'vuex';
import { memoryService } from '@/services/api-service';
import moment from 'moment';

export default {
  name: 'HistoryView',
  data() {
    return {
      searchQuery: '',
      dateFilter: 'all',
      dateFilterOptions: [
        { text: 'Toutes les périodes', value: 'all' },
        { text: 'Aujourd\'hui', value: 'today' },
        { text: 'Cette semaine', value: 'week' },
        { text: 'Ce mois', value: 'month' }
      ],
      headers: [
        { text: 'Client', value: 'client' },
        { text: 'Date', value: 'created_at' },
        { text: 'Messages', value: 'message_count' },
        { text: 'Statut', value: 'status' },
        { text: 'Actions', value: 'actions', sortable: false }
      ],
      sessions: [],
      showSessionDialog: false,
      selectedSession: null,
      sessionMessages: [],
      isLoading: false,
      noDataText: 'Aucune conversation trouvée'
    };
  },
  computed: {
    ...mapGetters(['currentUser'])
  },
  methods: {
    formatDate(dateString) {
      return moment(dateString).format('DD/MM/YYYY HH:mm');
    },
    
    formatTime(dateString) {
      return moment(dateString).format('HH:mm');
    },
    
    async searchClients() {
      // Cette méthode pourrait être utilisée pour rechercher des clients
      // et filtrer les sessions par client
    },
    
    async searchSessions() {
      this.isLoading = true;
      
      try {
        // Construire les paramètres de filtrage
        let params = {};
        
        if (this.searchQuery) {
          params.client_query = this.searchQuery;
        }
        
        if (this.dateFilter !== 'all') {
          const now = moment();
          let startDate;
          
          switch (this.dateFilter) {
            case 'today':
              startDate = now.startOf('day');
              break;
            case 'week':
              startDate = now.startOf('week');
              break;
            case 'month':
              startDate = now.startOf('month');
              break;
          }
          
          params.date_from = startDate.format('YYYY-MM-DD');
        }
        
        // Simuler la récupération des sessions depuis l'API
        // Dans un environnement réel, cela serait remplacé par un appel API
        setTimeout(() => {
          this.sessions = this.getMockSessions();
          this.isLoading = false;
        }, 1000);
        
        // Exemple d'appel API réel (commenté)
        // const response = await memoryService.getSessions(params);
        // this.sessions = response.data.data;
      } catch (error) {
        console.error('Erreur lors de la recherche des sessions:', error);
        this.sessions = [];
      } finally {
        this.isLoading = false;
      }
    },
    
    async viewSession(session) {
      this.selectedSession = session;
      this.isLoading = true;
      
      try {
        // Simuler la récupération des messages depuis l'API
        setTimeout(() => {
          this.sessionMessages = this.getMockSessionMessages(session.session_id);
          this.showSessionDialog = true;
          this.isLoading = false;
        }, 1000);
        
        // Exemple d'appel API réel (commenté)
        // const response = await memoryService.getMessages(session.session_id);
        // this.sessionMessages = response.data.data;
        // this.showSessionDialog = true;
      } catch (error) {
        console.error('Erreur lors de la récupération des messages:', error);
        this.sessionMessages = [];
      } finally {
        this.isLoading = false;
      }
    },
    
    resumeSession(session) {
      // Rediriger vers la vue de chat avec l'ID de session
      this.$router.push({
        path: '/chat',
        query: { session_id: session.session_id, client_id: session.client_id }
      });
    },
    
    // Méthodes pour générer des données de test
    getMockSessions() {
      return [
        {
          session_id: 'sess-2024-abc123',
          client_id: 42,
          client_name: 'Martin Sophie',
          created_at: '2024-04-01T14:40:15Z',
          message_count: 8,
          status: 'active'
        },
        {
          session_id: 'sess-2024-def456',
          client_id: 43,
          client_name: 'Dupont Jean',
          created_at: '2024-03-31T10:15:22Z',
          message_count: 12,
          status: 'closed'
        },
        {
          session_id: 'sess-2024-ghi789',
          client_id: 44,
          client_name: 'Dubois Pierre',
          created_at: '2024-03-30T16:05:47Z',
          message_count: 5,
          status: 'closed'
        },
        {
          session_id: 'sess-2024-jkl012',
          client_id: 45,
          client_name: 'Leroy Marie',
          created_at: '2024-03-29T09:30:11Z',
          message_count: 10,
          status: 'closed'
        }
      ];
    },
    
    getMockSessionMessages(sessionId) {
      // Simuler différents messages selon la session
      if (sessionId === 'sess-2024-abc123') {
        return [
          {
            role: 'user',
            content: 'Bonjour, je souhaite savoir où en est ma demande de remboursement pour ma consultation chez l\'ophtalmologue.',
            timestamp: '2024-04-01T14:41:05Z'
          },
          {
            role: 'assistant',
            content: 'Bonjour Madame Martin, je vais vérifier l\'état de votre demande de remboursement. Pouvez-vous me préciser la date approximative de votre consultation ?',
            timestamp: '2024-04-01T14:41:15Z'
          },
          {
            role: 'user',
            content: 'C\'était le 1er mars 2024.',
            timestamp: '2024-04-01T14:41:30Z'
          },
          {
            role: 'assistant',
            content: 'Merci pour cette précision. Je vois que votre demande de remboursement pour la consultation du 1er mars 2024 chez l\'ophtalmologue a été enregistrée le 15 mars sous la référence REC-2024-123. Elle est actuellement en cours de traitement par notre service de gestion.',
            timestamp: '2024-04-01T14:41:45Z'
          },
          {
            role: 'user',
            content: 'Quand est-ce que je recevrai le remboursement ?',
            timestamp: '2024-04-01T14:42:00Z'
          },
          {
            role: 'assistant',
            content: 'Avec votre contrat Premium, vous bénéficiez d\'un remboursement à 100% du tarif de convention plus les dépassements d\'honoraires jusqu\'à 300% du tarif conventionnel. Le délai standard de traitement est de 5-7 jours ouvrés à compter de la réception complète des documents. Votre réclamation ayant été enregistrée le 15 mars, le remboursement devrait être effectué d\'ici la fin de cette semaine.',
            timestamp: '2024-04-01T14:42:15Z'
          },
          {
            role: 'user',
            content: 'Merci pour ces informations. Est-ce que je recevrai une notification quand le remboursement sera effectué ?',
            timestamp: '2024-04-01T14:42:30Z'
          },
          {
            role: 'assistant',
            content: 'Oui, vous recevrez un email de confirmation dès que le remboursement sera effectué. Vous pourrez également suivre le statut de votre remboursement dans votre espace client sur notre site web ou notre application mobile. Souhaitez-vous que je vous aide pour autre chose ?',
            timestamp: '2024-04-01T14:42:45Z'
          }
        ];
      } else {
        // Messages par défaut pour les autres sessions
        return [
          {
            role: 'user',
            content: 'Bonjour, j\'ai une question concernant mon contrat.',
            timestamp: '2024-03-31T10:15:30Z'
          },
          {
            role: 'assistant',
            content: 'Bonjour, je suis là pour vous aider. Quelle est votre question concernant votre contrat ?',
            timestamp: '2024-03-31T10:15:45Z'
          },
          {
            role: 'user',
            content: 'Je voudrais savoir si les consultations chez un ostéopathe sont prises en charge.',
            timestamp: '2024-03-31T10:16:00Z'
          },
          {
            role: 'assistant',
            content: 'Je vais vérifier cela pour vous. Pouvez-vous me confirmer le type de contrat que vous avez actuellement ?',
            timestamp: '2024-03-31T10:16:15Z'
          }
        ];
      }
    }
  },
  mounted() {
    // Charger les sessions au chargement de la page
    this.searchSessions();
  }
};
</script>

<style scoped>
.session-messages {
  max-height: 400px;
  overflow-y: auto;
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.message {
  margin-bottom: 16px;
  display: flex;
}

.message-user {
  justify-content: flex-end;
}

.message-assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 12px;
  border-radius: 8px;
}

.message-user .message-content {
  background-color: #e3f2fd;
}

.message-assistant .message-content {
  background-color: #ffffff;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 0.85rem;
}

.message-time {
  color: rgba(0, 0, 0, 0.6);
}

.message-body {
  white-space: pre-line;
}
</style>
