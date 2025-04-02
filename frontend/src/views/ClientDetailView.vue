<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="6" lg="4">
        <v-card>
          <v-card-title class="headline">
            <v-icon large left color="primary">mdi-account-details</v-icon>
            Détails du client
          </v-card-title>
          
          <v-card-text v-if="client">
            <v-list>
              <v-list-item>
                <v-list-item-icon>
                  <v-icon>mdi-account</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ client.prenom }} {{ client.nom }}</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              
              <v-list-item>
                <v-list-item-icon>
                  <v-icon>mdi-email</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ client.email }}</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              
              <v-list-item>
                <v-list-item-icon>
                  <v-icon>mdi-phone</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ client.telephone }}</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
              
              <v-list-item v-if="client.numero_securite_sociale">
                <v-list-item-icon>
                  <v-icon>mdi-card-account-details</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ client.numero_securite_sociale }}</v-list-item-title>
                  <v-list-item-subtitle>Numéro de sécurité sociale</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
              
              <v-list-item v-if="client.adresse">
                <v-list-item-icon>
                  <v-icon>mdi-map-marker</v-icon>
                </v-list-item-icon>
                <v-list-item-content>
                  <v-list-item-title>{{ formatAddress(client.adresse) }}</v-list-item-title>
                  <v-list-item-subtitle>Adresse</v-list-item-subtitle>
                </v-list-item-content>
              </v-list-item>
            </v-list>
            
            <v-divider class="my-3"></v-divider>
            
            <div class="d-flex justify-space-between align-center mb-3">
              <h3 class="text-subtitle-1">Contrats</h3>
              <v-btn
                small
                color="primary"
                @click="showContractDetails = true"
                v-if="client.contrats && client.contrats.length > 0"
              >
                <v-icon small left>mdi-eye</v-icon>
                Détails
              </v-btn>
            </div>
            
            <v-chip-group>
              <v-chip
                v-for="(contrat, index) in client.contrats"
                :key="index"
                :color="getContractColor(contrat.niveau_couverture)"
                text-color="white"
                class="mr-1"
              >
                {{ contrat.type_contrat }} - {{ contrat.niveau_couverture }}
              </v-chip>
            </v-chip-group>
          </v-card-text>
          
          <v-card-text v-else>
            <v-skeleton-loader
              type="list-item-avatar-three-line, divider, list-item-avatar-three-line"
              v-if="isLoading"
            ></v-skeleton-loader>
            <v-alert
              type="warning"
              v-else
            >
              Aucun client sélectionné ou trouvé.
            </v-alert>
          </v-card-text>
          
          <v-card-actions v-if="client">
            <v-btn
              color="primary"
              @click="startChat"
            >
              <v-icon left>mdi-chat</v-icon>
              Démarrer une conversation
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn
              color="grey"
              text
              to="/clients"
            >
              <v-icon left>mdi-arrow-left</v-icon>
              Retour
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6" lg="8">
        <v-card class="mb-4">
          <v-card-title class="headline">
            <v-icon large left color="primary">mdi-alert-circle</v-icon>
            Réclamations
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              @click="showNewClaimDialog = true"
              v-if="client"
            >
              <v-icon left>mdi-plus</v-icon>
              Nouvelle réclamation
            </v-btn>
          </v-card-title>
          
          <v-card-text>
            <v-data-table
              :headers="claimsHeaders"
              :items="claims"
              :items-per-page="5"
              :loading="isLoadingClaims"
              class="elevation-1"
              :no-data-text="isLoadingClaims ? 'Chargement des réclamations...' : 'Aucune réclamation trouvée'"
            >
              <template v-slot:item.date_reclamation="{ item }">
                {{ formatDate(item.date_reclamation) }}
              </template>
              
              <template v-slot:item.statut="{ item }">
                <v-chip
                  small
                  :color="getStatusColor(item.statut)"
                  text-color="white"
                >
                  {{ item.statut }}
                </v-chip>
              </template>
              
              <template v-slot:item.actions="{ item }">
                <v-btn
                  small
                  color="primary"
                  @click="viewClaim(item)"
                >
                  <v-icon small>mdi-eye</v-icon>
                </v-btn>
                <v-btn
                  small
                  color="success"
                  class="ml-2"
                  @click="updateClaim(item)"
                  v-if="canUpdateClaim(item)"
                >
                  <v-icon small>mdi-pencil</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
        
        <v-card>
          <v-card-title class="headline">
            <v-icon large left color="primary">mdi-history</v-icon>
            Historique des conversations
          </v-card-title>
          
          <v-card-text>
            <v-data-table
              :headers="sessionsHeaders"
              :items="sessions"
              :items-per-page="5"
              :loading="isLoadingSessions"
              class="elevation-1"
              :no-data-text="isLoadingSessions ? 'Chargement des conversations...' : 'Aucune conversation trouvée'"
            >
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
                  <v-icon small>mdi-eye</v-icon>
                </v-btn>
                <v-btn
                  small
                  color="success"
                  class="ml-2"
                  @click="resumeSession(item)"
                  v-if="item.status === 'active'"
                >
                  <v-icon small>mdi-chat</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- Dialog pour les détails des contrats -->
    <v-dialog v-model="showContractDetails" max-width="700">
      <v-card>
        <v-card-title>Détails des contrats</v-card-title>
        <v-card-text v-if="client && client.contrats">
          <v-expansion-panels>
            <v-expansion-panel
              v-for="(contrat, index) in client.contrats"
              :key="index"
            >
              <v-expansion-panel-header>
                <div class="d-flex align-center">
                  <v-chip
                    :color="getContractColor(contrat.niveau_couverture)"
                    text-color="white"
                    class="mr-3"
                  >
                    {{ contrat.niveau_couverture }}
                  </v-chip>
                  <span>{{ contrat.type_contrat }} ({{ contrat.numero_contrat }})</span>
                </div>
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <v-list dense>
                  <v-list-item>
                    <v-list-item-content>
                      <v-list-item-subtitle>Numéro de contrat</v-list-item-subtitle>
                      <v-list-item-title>{{ contrat.numero_contrat }}</v-list-item-title>
                    </v-list-item-content>
                  </v-list-item>
                  
                  <v-list-item>
                    <v-list-item-content>
                      <v-list-item-subtitle>Statut</v-list-item-subtitle>
                      <v-list-item-title>
                        <v-chip
                          x-small
                          :color="contrat.statut === 'Actif' ? 'success' : 'error'"
                          text-color="white"
                        >
                          {{ contrat.statut }}
                        </v-chip>
                      </v-list-item-title>
                    </v-list-item-content>
                  </v-list-item>
                  
                  <v-list-item>
                    <v-list-item-content>
                      <v-list-item-subtitle>Période</v-list-item-subtitle>
                      <v-list-item-title>
                        {{ formatDate(contrat.date_debut) }} - {{ formatDate(contrat.date_fin) }}
                      </v-list-item-title>
                    </v-list-item-content>
                  </v-list-item>
                  
                  <v-list-item>
                    <v-list-item-content>
                      <v-list-item-subtitle>Cotisation mensuelle</v-list-item-subtitle>
                      <v-list-item-title>{{ contrat.montant_cotisation }} €</v-list-item-title>
                    </v-list-item-content>
                  </v-list-item>
                </v-list>
                
                <v-divider class="my-3"></v-divider>
                
                <h3 class="text-subtitle-1 mb-2">Bénéficiaires</h3>
                <v-list dense v-if="contrat.beneficiaires && contrat.beneficiaires.length > 0">
                  <v-list-item v-for="(beneficiaire, bIndex) in contrat.beneficiaires" :key="bIndex">
                    <v-list-item-icon>
                      <v-icon>mdi-account</v-icon>
                    </v-list-item-icon>
                    <v-list-item-content>
                      <v-list-item-title>{{ beneficiaire.prenom }} {{ beneficiaire.nom }}</v-list-item-title>
                      <v-list-item-subtitle>{{ beneficiaire.relation }}</v-list-item-subtitle>
                    </v-list-item-content>
                  </v-list-item>
                </v-list>
                <p v-else class="text-body-2 text-center my-3">Aucun bénéficiaire supplémentaire</p>
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            text
            @click="showContractDetails = false"
          >
            Fermer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Dialog pour les détails d'une réclamation -->
    <v-dialog v-model="showClaimDialog" max-width="700">
      <v-card>
        <v-card-title>
          Détails de la réclamation
          <v-spacer></v-spacer>
          <v-chip
            :color="selectedClaim ? getStatusColor(selectedClaim.statut) : 'grey'"
            text-color="white"
          >
            {{ selectedClaim ? selectedClaim.statut : '' }}
          </v-chip>
        </v-card-title>
        <v-card-text v-if="selectedClaim">
          <v-row>
            <v-col cols="12" md="6">
              <v-list dense>
                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-subtitle>Référence</v-list-item-subtitle>
                    <v-list-item-title>{{ selectedClaim.numero_reclamation }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                
                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-subtitle>Type</v-list-item-subtitle>
                    <v-list-item-title>{{ selectedClaim.type_reclamation }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                
                <v-list-item>
                  <v-list-item-content>
                    <v-list-item-subtitle>Date de création</v-list-item-subtitle>
                    <v-list-item-title>{{ formatDate(selectedClaim.date_reclamation) }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                
                <v-list-item v-if="selectedClaim.montant_demande">
                  <v-list-item-content>
                    <v-list-item-subtitle>Montant demandé</v-list-item-subtitle>
                    <v-list-item-title>{{ selectedClaim.montant_demande }} €</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
                
                <v-list-item v-if="selectedClaim.agent_traitement">
                  <v-list-item-content>
                    <v-list-item-subtitle>Agent en charge</v-list-item-subtitle>
                    <v-list-item-title>{{ selectedClaim.agent_traitement }}</v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </v-list>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-card outlined>
                <v-card-title class="text-subtitle-1">Description</v-card-title>
                <v-card-text>
                  <p style="white-space: pre-line">{{ selectedClaim.description }}</p>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
          
          <v-divider class="my-3"></v-divider>
          
          <h3 class="text-subtitle-1 mb-2">Documents</h3>
          <v-list dense v-if="selectedClaim.documents && selectedClaim.documents.length > 0">
            <v-list-item v-for="(doc, index) in selectedClaim.documents" :key="index">
              <v-list-item-icon>
                <v-icon>mdi-file-document</v-icon>
              </v-list-item-icon>
              <v-list-item-content>
                <v-list-item-title>{{ doc.nom }}</v-list-item-title>
                <v-list-item-subtitle>{{ doc.type }} - {{ formatDate(doc.date_upload) }}</v-list-item-subtitle>
              </v-list-item-content>
              <v-list-item-action>
                <v-btn icon>
                  <v-icon>mdi-download</v-icon>
                </v-btn>
              </v-list-item-action>
            </v-list-item>
          </v-list>
          <p v-else class="text-body-2 text-center my-3">Aucun document associé</p>
          
          <v-divider class="my-3"></v-divider>
          
          <h3 class="text-subtitle-1 mb-2">Commentaires</h3>
          <v-timeline dense v-if="selectedClaim.commentaires && selectedClaim.commentaires.length > 0">
            <v-timeline-item
              v-for="(comment, index) in selectedClaim.commentaires"
              :key="index"
              :color="comment.visible_client ? 'primary' : 'grey'"
              small
            >
              <div class="d-flex justify-space-between">
                <span class="font-weight-bold">{{ comment.auteur }}</span>
                <span class="text-caption">{{ formatDate(comment.date) }}</span>
              </div>
              <div>{{ comment.contenu }}</div>
              <v-chip
                x-small
                outlined
                color="grey"
                class="mt-1"
                v-if="!comment.visible_client"
              >
                Interne
              </v-chip>
            </v-timeline-item>
          </v-timeline>
          <p v-else class="text-body-2 text-center my-3">Aucun commentaire</p>
        </v-card-text>
        <v-card-actions>
          <v-btn
            color="success"
            @click="updateClaim(selectedClaim)"
            v-if="selectedClaim && canUpdateClaim(selectedClaim)"
          >
            <v-icon left>mdi-pencil</v-icon>
            Mettre à jour
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            text
            @click="showClaimDialog = false"
          >
            Fermer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Dialog pour créer une nouvelle réclamation -->
    <v-dialog v-model="showNewClaimDialog" max-width="700">
      <v-card>
        <v-card-title>Nouvelle réclamation</v-card-title>
        <v-card-text>
          <v-form ref="claimForm" v-model="isClaimFormValid">
            <v-select
              v-model="newClaim.type_reclamation"
              :items="claimTypes"
              label="Type de réclamation"
              required
              :rules="[v => !!v || 'Le type est requis']"
            ></v-select>
            
            <v-textarea
              v-model="newClaim.description"
              label="Description"
              required
              :rules="[v => !!v || 'La description est requise', v => v.length >= 10 || 'La description doit contenir au moins 10 caractères']"
              rows="4"
            ></v-textarea>
            
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model.number="newClaim.montant_demande"
                  label="Montant demandé (€)"
                  type="number"
                  :rules="[v => v >= 0 || 'Le montant doit être positif']"
                ></v-text-field>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-menu
                  v-model="dateMenu"
                  :close-on-content-click="false"
                  transition="scale-transition"
                  offset-y
                  min-width="auto"
                >
                  <template v-slot:activator="{ on, attrs }">
                    <v-text-field
                      v-model="newClaim.date_soins"
                      label="Date des soins"
                      readonly
                      v-bind="attrs"
                      v-on="on"
                    ></v-text-field>
                  </template>
                  <v-date-picker
                    v-model="newClaim.date_soins"
                    @input="dateMenu = false"
                  ></v-date-picker>
                </v-menu>
              </v-col>
            </v-row>
            
            <v-file-input
              v-model="newClaim.documents"
              label="Documents justificatifs"
              multiple
              chips
              prepend-icon="mdi-paperclip"
              hint="Factures, décomptes Sécurité Sociale, etc."
              persistent-hint
            ></v-file-input>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="grey"
            text
            @click="showNewClaimDialog = false"
          >
            Annuler
          </v-btn>
          <v-btn
            color="primary"
            :disabled="!isClaimFormValid"
            @click="submitNewClaim"
          >
            Enregistrer
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import { lookService, toolsService } from '@/services/api-service';
import moment from 'moment';

export default {
  name: 'ClientDetailView',
  data() {
    return {
      isLoading: false,
      isLoadingClaims: false,
      isLoadingSessions: false,
      claims: [],
      sessions: [],
      claimsHeaders: [
        { text: 'Référence', value: 'numero_reclamation' },
        { text: 'Type', value: 'type_reclamation' },
        { text: 'Date', value: 'date_reclamation' },
        { text: 'Montant', value: 'montant_demande' },
        { text: 'Statut', value: 'statut' },
        { text: 'Actions', value: 'actions', sortable: false }
      ],
      sessionsHeaders: [
        { text: 'Date', value: 'created_at' },
        { text: 'Messages', value: 'message_count' },
        { text: 'Statut', value: 'status' },
        { text: 'Actions', value: 'actions', sortable: false }
      ],
      showContractDetails: false,
      showClaimDialog: false,
      selectedClaim: null,
      showNewClaimDialog: false,
      isClaimFormValid: false,
      dateMenu: false,
      newClaim: {
        type_reclamation: '',
        description: '',
        montant_demande: 0,
        date_soins: new Date().toISOString().substr(0, 10),
        documents: []
      },
      claimTypes: [
        'Remboursement',
        'Contestation',
        'Information',
        'Modification contrat',
        'Autre'
      ]
    };
  },
  computed: {
    ...mapGetters(['currentUser']),
    
    client() {
      return this.$store.state.selectedClient;
    },
    
    clientId() {
      return this.$route.params.id;
    }
  },
  methods: {
    ...mapActions(['getClientDetails', 'createChatSession']),
    
    formatDate(dateString) {
      return moment(dateString).format('DD/MM/YYYY');
    },
    
    formatAddress(address) {
      if (!address) return '';
      return `${address.rue}, ${address.code_postal} ${address.ville}, ${address.pays}`;
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
    
    async fetchClientData() {
      this.isLoading = true;
      
      try {
        await this.getClientDetails(this.clientId);
      } catch (error) {
        console.error('Erreur lors de la récupération des détails du client:', error);
      } finally {
        this.isLoading = false;
      }
    },
    
    async fetchClaims() {
      this.isLoadingClaims = true;
      
      try {
        // Simuler la récupération des réclamations depuis l'API
        setTimeout(() => {
          this.claims = this.getMockClaims();
          this.isLoadingClaims = false;
        }, 1000);
        
        // Exemple d'appel API réel (commenté)
        // const response = await lookService.searchClaims('', this.clientId);
        // this.claims = response.data.data;
      } catch (error) {
        console.error('Erreur lors de la récupération des réclamations:', error);
        this.claims = [];
      } finally {
        this.isLoadingClaims = false;
      }
    },
    
    async fetchSessions() {
      this.isLoadingSessions = true;
      
      try {
        // Simuler la récupération des sessions depuis l'API
        setTimeout(() => {
          this.sessions = this.getMockSessions();
          this.isLoadingSessions = false;
        }, 1000);
        
        // Exemple d'appel API réel (commenté)
        // const response = await memoryService.getClientSessions(this.clientId);
        // this.sessions = response.data.data;
      } catch (error) {
        console.error('Erreur lors de la récupération des sessions:', error);
        this.sessions = [];
      } finally {
        this.isLoadingSessions = false;
      }
    },
    
    viewClaim(claim) {
      this.selectedClaim = claim;
      this.showClaimDialog = true;
    },
    
    updateClaim(claim) {
      // Implémenter la mise à jour d'une réclamation
      console.log('Mise à jour de la réclamation:', claim);
    },
    
    canUpdateClaim(claim) {
      // Vérifier si l'agent peut mettre à jour la réclamation
      return claim.statut !== 'Traité' && claim.statut !== 'Rejeté';
    },
    
    viewSession(session) {
      // Rediriger vers la vue d'historique avec l'ID de session
      this.$router.push({
        path: '/history',
        query: { session_id: session.session_id }
      });
    },
    
    resumeSession(session) {
      // Rediriger vers la vue de chat avec l'ID de session
      this.$router.push({
        path: '/chat',
        query: { session_id: session.session_id, client_id: this.clientId }
      });
    },
    
    async startChat() {
      try {
        await this.createChatSession(this.clientId);
        this.$router.push('/chat');
      } catch (error) {
        console.error('Erreur lors de la création de la session de chat:', error);
      }
    },
    
    async submitNewClaim() {
      if (!this.$refs.claimForm.validate()) return;
      
      try {
        // Préparer les données de la réclamation
        const claimData = {
          client_id: this.clientId,
          type_reclamation: this.newClaim.type_reclamation,
          description: this.newClaim.description,
          montant_demande: this.newClaim.montant_demande,
          date_soins: this.newClaim.date_soins,
          documents: this.newClaim.documents.map(file => file.name)
        };
        
        // Simuler l'envoi de la réclamation
        console.log('Envoi de la réclamation:', claimData);
        
        // Exemple d'appel API réel (commenté)
        // const response = await toolsService.createClaim(claimData);
        
        // Fermer le dialogue et rafraîchir les réclamations
        this.showNewClaimDialog = false;
        this.fetchClaims();
        
        // Réinitialiser le formulaire
        this.$refs.claimForm.reset();
      } catch (error) {
        console.error('Erreur lors de la création de la réclamation:', error);
      }
    },
    
    // Méthodes pour générer des données de test
    getMockClaims() {
      return [
        {
          id: 789,
          numero_reclamation: "REC-2024-123",
          client_id: this.clientId,
          type_reclamation: "Remboursement",
          statut: "En cours",
          date_reclamation: "2024-03-15",
          description: "Je n'ai toujours pas reçu le remboursement de ma consultation chez l'ophtalmologue du 01/03/2024.",
          montant_demande: 95.00,
          agent_traitement: "Dubois Pierre",
          documents: [
            {
              id: "doc-456",
              nom: "facture_consultation.pdf",
              type: "facture",
              date_upload: "2024-03-15T10:23:45Z"
            },
            {
              id: "doc-457",
              nom: "decompte_secu.pdf",
              type: "decompte",
              date_upload: "2024-03-15T10:24:12Z"
            }
          ],
          commentaires: [
            {
              id: "com-123",
              auteur: "Système",
              date: "2024-03-15T10:25:00Z",
              contenu: "Réclamation créée",
              visible_client: true
            },
            {
              id: "com-124",
              auteur: "Dubois Pierre",
              date: "2024-03-16T09:15:30Z",
              contenu: "Vérification des documents en cours",
              visible_client: false
            }
          ]
        },
        {
          id: 790,
          numero_reclamation: "REC-2024-124",
          client_id: this.clientId,
          type_reclamation: "Remboursement",
          statut: "Traité",
          date_reclamation: "2024-02-10",
          description: "Demande de remboursement pour lunettes de vue",
          montant_demande: 185.50,
          agent_traitement: "Martin Sophie",
          documents: [],
          commentaires: []
        }
      ];
    },
    
    getMockSessions() {
      return [
        {
          session_id: "sess-2024-abc123",
          client_id: this.clientId,
          created_at: "2024-04-01T14:40:15Z",
          message_count: 8,
          status: "active"
        },
        {
          session_id: "sess-2024-def456",
          client_id: this.clientId,
          created_at: "2024-03-31T10:15:22Z",
          message_count: 12,
          status: "closed"
        }
      ];
    }
  },
  mounted() {
    this.fetchClientData();
    this.fetchClaims();
    this.fetchSessions();
  }
};
</script>

<style scoped>
/* Styles spécifiques à la vue de détail client */
</style>
