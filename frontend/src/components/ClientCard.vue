<template>
  <div class="client-card">
    <v-card outlined>
      <v-card-title class="d-flex justify-space-between">
        <div>
          {{ client.prenom }} {{ client.nom }}
        </div>
        <v-chip
          v-if="client.contrats && client.contrats.length > 0"
          :color="getContractColor(client.contrats[0].niveau_couverture)"
          text-color="white"
          small
        >
          {{ client.contrats[0].niveau_couverture }}
        </v-chip>
      </v-card-title>
      
      <v-card-text>
        <v-list dense>
          <v-list-item v-if="client.email">
            <v-list-item-icon>
              <v-icon small>mdi-email</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>{{ client.email }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          
          <v-list-item v-if="client.telephone">
            <v-list-item-icon>
              <v-icon small>mdi-phone</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>{{ client.telephone }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          
          <v-list-item v-if="client.numero_securite_sociale">
            <v-list-item-icon>
              <v-icon small>mdi-card-account-details</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>{{ formatSSN(client.numero_securite_sociale) }}</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-card-text>
      
      <v-card-actions>
        <v-btn
          small
          color="primary"
          :to="`/clients/${client.id}`"
          text
        >
          <v-icon small left>mdi-eye</v-icon>
          Détails
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          small
          color="success"
          @click="$emit('start-chat', client)"
          text
        >
          <v-icon small left>mdi-chat</v-icon>
          Chat
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'ClientCard',
  props: {
    client: {
      type: Object,
      required: true
    }
  },
  methods: {
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
    formatSSN(ssn) {
      if (!ssn) return '';
      // Format: 1 23 45 67 890 12 (French SSN format)
      return ssn.replace(/(\d{1})(\d{2})(\d{2})(\d{2})(\d{3})(\d{2})/, '$1 $2 $3 $4 $5 $6');
    }
  }
};
</script>

<style scoped>
.client-card {
  transition: transform 0.2s;
}

.client-card:hover {
  transform: translateY(-5px);
}
</style>
