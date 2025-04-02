<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="4" v-if="selectedClient">
        <v-card class="mb-4">
          <v-card-title class="headline">
            <v-icon large left color="primary">mdi-account</v-icon>
            Informations client
          </v-card-title>
          
          <v-card-text>
            <v-list>
              <v-list-item>
                <v-list-item-icon>
                  <v-icon>mdi-account</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ selectedClient.prenom }} {{ selectedClient.nom }}</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              
              <v-list-item>
                <v-list-item-icon>
                  <v-icon>mdi-email</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ selectedClient.email }}</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              
              <v-list-item>
                <v-list-item-icon>
                  <v-icon>mdi-phone</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ selectedClient.telephone }}</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              
              <v-list-item v-if="selectedClient.numero_securite_sociale">
                <v-list-item-icon>
                  <v-icon>mdi-card-account-details</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ selectedClient.numero_securite_sociale }}</v-list-item-title>
                  <v-list-item-subtitle>Numéro de sécurité sociale</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
            
            <v-divider class="my-3"></v-divider>
            
            <h3 class="text-subtitle-1 mb-2">Contrats</h3>
            <v-list dense>
              <v-list-item v-for="(contrat, index) in selectedClient.contrats" :key="index">
                <v-list-item-icon>
                  <v-icon>mdi-file-document</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ contrat.type_contrat }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip
                      small
                      :color="getContractColor(contrat.niveau_couverture)"
                      text-color="white"
                      class="mr-1"
                    >
                      {{ contrat.niveau_couverture }}
                    </v-chip>
                    <v-chip
                      small
                      :color="contrat.statut === 'Actif' ? 'success' : 'error'"
                      text-color="white"
                    >
                      {{ contrat.statut }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
            
            <v-divider class="my-3"></v-divider>
            
            <h3 class="text-subtitle-1 mb-2">Réclamations récentes</h3>
            <v-list dense v-if="recentClaims.length > 0">
              <v-list-item v-for="(claim, index) in recentClaims" :key="index">
                <v-list-item-icon>
                  <v-icon>mdi-alert-circle</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ claim.type_reclamation }}</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip
                      small
                      :color="getStatusColor(claim.statut)"
                      text-color="white"
                    >
                      {{ claim.statut }}
                    </v-chip>
                    {{ formatDate(claim.date_reclamation) }}
                  </v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
            <p v-else class="text-body-2 text-center my-3">Aucune réclamation récente</p>
          </v-card-text>
        </v-card>
        
        <v-card>
          <v-card-title>Base de connaissances</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="knowledgeQuery"
              label="Rechercher dans la base de connaissances"
              prepend-icon="mdi-book-search"
              clearable
              @keyup.enter="searchKnowledge"
            ></v-text-field>
            
            <v-list dense v-if="knowledgeResults.length > 0">
              <v-list-item v-for="(item, index) in knowledgeResults" :key="index">
                <v-list-item-icon>
                  <v-icon>mdi-book-open-variant</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ item.title }}</v-list-item-title>
                  <v-list-item-subtitle>{{ item.category }}</v-list-item-subtitle>
                </v-list-item-content>
                <v-list-item-action>
                  <v-btn icon @click="showKnowledgeDetail(item)">
                    <v-icon>mdi-information</v-icon>
                  </v-btn>
                </v-list-item-action>
              </v-list-item>
            </v-list>
            <p v-else-if="knowledgeSearchPerformed" class="text-body-2 text-center my-3">
              Aucun résultat trouvé
            </p>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" :md="selectedClient ? 8 : 12">
        <v-card>
          <v-card-title class="headline">
            <v-icon large left color="primary">mdi-chat</v-icon>
            Conversation
            <v-spacer></v-spacer>
            <v-btn
              v-if="!selectedClient"
              color="primary"
              to="/clients"
            >
              <v-icon left>mdi-account-search</v-icon>
              Sélectionner un client
            </v-btn>
          </v-card-title>
          
          <v-card-text v-if="!selectedClient" class="text-center pa-6">
            <v-icon size="64" color="grey lighten-1">mdi-account-question</v-icon>
            <h3 class="text-h5 mt-4">Aucun client sélectionné</h3>
            <p class="text-body-1 mt-2">
              Veuillez sélectionner un client pour démarrer une conversation.
            </p>
          </v-card-text>
          
          <template v-else>
            <div class="chat-container">
              <div class="chat-messages" ref="chatMessages">
                <div
                  v-for="(message, index) in chatHistory"
                  :key="index"
                  :class="['message', message.role === 'user' ? 'message-user' : 'message-assistant']"
                >
                  <div class="message-content">
                    <div class="message-header">
                      <strong>{{ message.role === 'user' ? selectedClient.prenom : 'Assistant IA' }}</strong>
                      <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                    </div>
                    <div class="message-body">{{ message.content }}</div>
                  </div>
                </div>
                
                <div v-if="isTyping" class="message message-assistant">
                  <div class="message-content">
                    <div class="message-header">
                      <strong>Assistant IA</strong>
                    </div>
                    <div class="message-body typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
              
              <v-divider></v-divider>
              
              <div class="chat-input">
                <v-textarea
                  v-model="messageInput"
                  rows="2"
                  auto-grow
                  hide-details
                  placeholder="Tapez votre message ici..."
                  @keydown.enter.prevent="sendMessage"
                ></v-textarea>
                <v-btn
                  color="primary"
                  fab
                  small
                  :disabled="!messageInput.trim() || isLoading"
                  :loading="isLoading"
                  @click="sendMessage"
                >
                  <v-icon>mdi-send</v-icon>
                </v-btn>
              </div>
            </div>
          </template>
        </v-card>
      </v-col>
    </v-row>
    
    <v-dialog v-model="showKnowledgeDialog" max-width="600">
      <v-card>
        <v-card-title>{{ selectedKnowledgeItem ? selectedKnowledgeItem.title : '' }}</v-card-title>
        <v-card-subtitle>{{ selectedKnowledgeItem ? selectedKnowledgeItem.category : '' }}</v-card-subtitle>
        <v-card-text>
          <p v-if="selectedKnowledgeItem" style="white-space: pre-line">{{ selectedKnowledgeItem.content }}</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            text
            @click="insertKnowledgeInMessage"
          >
            <v-icon left>mdi-content-copy</v-icon>
            Utiliser dans le message
          </v-btn>
          <v-btn
            color="grey"
            text
            @click="showKnowledgeDialog = false"
          >
            Fermer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import { lookService } from '@/services/api-service';
import moment from 'moment';

export default {
  name: 'ChatView',
  data() {
    return {
      messageInput: '',
      isTyping: false,
      knowledgeQuery: '',
      knowledgeResults: [],
      knowledgeSearchPerformed: false,
      showKnowledgeDialog: false,
      selectedKnowledgeItem: null,
      recentClaims: []
    };
  },
  computed: {
    ...mapGetters(['selectedClient', 'chatHistory', 'currentSession', 'isLoading']),
  },
  methods: {
    ...mapActions(['getClientDetails', 'createChatSession', 'sendMessage']),
    
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
    
    getStatusColor(status) {
      switch (status) {
        case 'Traité':
        case 'Résolu':
          return 'success';
        case 'En cours':
          return 'info';
        case 'En attente':
          return 'warning';
        case 'Rejeté':
          return 'error';
        default:
          return 'grey';
      }
    },
    
    formatDate(dateString) {
      return moment(dateString).format('DD/MM/YYYY');
    },
    
    formatTime(dateString) {
      return moment(dateString).format('HH:mm');
    },
    
    async sendMessage() {
      if (!this.messageInput.trim() || !this.selectedClient) return;
      
      const message = this.messageInput;
      this.messageInput = '';
      this.isTyping = true;
      
      try {
        await this.sendMessage(message);
        this.scrollToBottom();
      } catch (error) {
        console.error('Erreur lors de l\'envoi du message:', error);
      } finally {
        this.isTyping = false;
      }
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.chatMessages) {
          this.$refs.chatMessages.scrollTop = this.$refs.chatMessages.scrollHeight;
        }
      });
    },
    
    async searchKnowledge() {
      if (!this.knowledgeQuery.trim()) return;
      
      this.knowledgeSearchPerformed = true;
      
      try {
        const response = await lookService.searchKnowledge(this.knowledgeQuery);
        this.knowledgeResults = response.data.data;
      } catch (error) {
        console.error('Erreur lors de la recherche dans la base de connaissances:', error);
        this.knowledgeResults = [];
      }
    },
    
    showKnowledgeDetail(item) {
      this.selectedKnowledgeItem = item;
      this.showKnowledgeDialog = true;
    },
    
    insertKnowledgeInMessage() {
      if (this.selectedKnowledgeItem) {
        this.messageInput += `\n\nInformation de la base de connaissances:\n${this.selectedKnowledgeItem.content}`;
        this.showKnowledgeDialog = false;
      }
    },
    
    async fetchRecentClaims() {
      if (!this.selectedClient) return;
      
      try {
        const response = await lookService.searchClaims('', this.selectedClient.id, null, 3);
        this.recentClaims = response.data.data;
      } catch (error) {
        console.error('Erreur lors de la récupération des réclamations récentes:', error);
        this.recentClaims = [];
      }
    }
  },
  watch: {
    selectedClient(newVal) {
      if (newVal) {
        this.fetchRecentClaims();
      }
    },
    chatHistory() {
      this.scrollToBottom();
    }
  },
  mounted() {
    // Si un client est déjà sélectionné, récupérer ses réclamations récentes
    if (this.selectedClient) {
      this.fetchRecentClaims();
    }
    
    // Si on arrive sur cette page via une URL directe avec un ID client
    const clientId = this.$route.query.client_id;
    if (clientId && !this.selectedClient) {
      this.getClientDetails(clientId);
    }
    
    this.scrollToBottom();
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 70vh;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.chat-input {
  display: flex;
  align-items: center;
  padding: 8px 16px;
}

.chat-input .v-textarea {
  flex: 1;
  margin-right: 8px;
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
  background-color: #f5f5f5;
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

.typing-indicator {
  display: flex;
  align-items: center;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: inline-block;
  margin-right: 5px;
  animation: typing 1s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
  margin-right: 0;
}

@keyframes typing {
  0% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-5px);
  }
  100% {
    transform: translateY(0px);
  }
}
</style>
