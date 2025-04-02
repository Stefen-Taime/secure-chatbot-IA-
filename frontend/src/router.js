import { createRouter, createWebHistory } from 'vue-router';
import { isAuthenticated } from './services/keycloak-service';
import HomeView from './views/HomeView.vue';
import LoginView from './views/LoginView.vue';
import ChatView from './views/ChatView.vue';
import ClientSearchView from './views/ClientSearchView.vue';
import ClientDetailView from './views/ClientDetailView.vue';
import HistoryView from './views/HistoryView.vue';

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
  {
    path: '/chat',
    name: 'chat',
    component: ChatView,
    meta: { requiresAuth: true }
  },
  {
    path: '/clients',
    name: 'clients',
    component: ClientSearchView,
    meta: { requiresAuth: true }
  },
  {
    path: '/clients/:id',
    name: 'client-detail',
    component: ClientDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryView,
    meta: { requiresAuth: true }
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

// Navigation guard pour vérifier l'authentification
router.beforeEach((to, from, next) => {
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // Cette route nécessite une authentification
    if (!isAuthenticated()) {
      // L'utilisateur n'est pas authentifié, rediriger vers la page de login
      next({ name: 'login' });
    } else {
      // L'utilisateur est authentifié, continuer
      next();
    }
  } else {
    // Cette route ne nécessite pas d'authentification
    next();
  }
});

export default router;
