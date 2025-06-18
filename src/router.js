import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/pages/MainLayout.vue'
import Dashboard from './pages/Dashboard.vue'
import I4CCaseEntry from '@/pages/I4CCaseEntry.vue'
import CaseDetails from '@/pages/CaseDetails.vue'
import CaseRiskReview from './pages/CaseRiskReview.vue'
import Login from '@/pages/Login.vue' // <-- 1. Import the new Login page
import BulkFileUpload from '@/pages/BulkFileUpload.vue' // Import BulkUpload if needed

const routes = [
  // 2. Add a route for the Login page
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/',
    component: MainLayout,
    // Add a meta field to protect these routes
    meta: { requiresAuth: true }, 
    children: [
      { path: '', redirect: '/dashboard' }, // Redirect root to dashboard
      { path: 'dashboard', name: 'Dashboard', component: Dashboard },
      { path: 'data-entry', name: 'DataEntry', component: I4CCaseEntry },
      { path: 'bulk-upload', name: 'BulkUpload', component: BulkFileUpload },
      { path: 'case-details', name: 'CaseDetails', component: CaseDetails },
      {
        path: 'case-details/:ackno',
        name: 'CaseRiskReview',
        component: CaseRiskReview,
        props: true,
      },
    ],
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 3. Add a Navigation Guard for Security
router.beforeEach((to, from, next) => {
  const loggedIn = localStorage.getItem('jwt');

  // If the route requires authentication and the user is not logged in,
  // redirect them to the login page.
  if (to.meta.requiresAuth && !loggedIn) {
    next('/login');
  } 
  // If the user is logged in and tries to go to the login page,
  // send them to the dashboard instead.
  else if (to.path === '/login' && loggedIn) {
    next('/dashboard');
  } 
  // Otherwise, let them proceed.
  else {
    next();
  }
});