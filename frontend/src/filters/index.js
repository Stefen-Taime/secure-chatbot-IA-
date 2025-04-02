import Vue from 'vue';
import moment from 'moment';

// Filtre pour formater les dates
export const formatDate = (value, format = 'DD/MM/YYYY') => {
  if (!value) return '';
  return moment(value).format(format);
};

// Filtre pour formater les montants en euros
export const formatCurrency = (value, currency = '€', decimals = 2) => {
  if (value === null || value === undefined) return '';
  const formattedValue = parseFloat(value).toFixed(decimals);
  return `${formattedValue} ${currency}`;
};

// Filtre pour tronquer un texte
export const truncateText = (value, length = 100, suffix = '...') => {
  if (!value) return '';
  if (value.length <= length) return value;
  return value.substring(0, length) + suffix;
};

// Enregistrement global des filtres
Vue.filter('formatDate', formatDate);
Vue.filter('formatCurrency', formatCurrency);
Vue.filter('truncateText', truncateText);

export default {
  formatDate,
  formatCurrency,
  truncateText
};
