import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/pages/MainLayout.vue'
import Dashboard from '@/pages/Dashboard.vue'
import SimpleDashboard from '@/pages/SimpleDashboard.vue'
import I4CCaseEntry from '@/pages/I4CCaseEntry.vue'
import CaseDetails from '@/pages/CaseDetails.vue'
// import CaseRiskReview from '@/pages/CaseRiskReview.vue'
import Login from '@/pages/Login.vue'
import BulkFileUpload from '@/pages/BulkFileUpload.vue'
import UserActivity from '@/pages/UserActivity.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true }, 
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'Dashboard', component: Dashboard },
      { path: 'simple-dashboard', name: 'SimpleDashboard', component: SimpleDashboard },
      { path: 'data-entry', name: 'DataEntry', component: I4CCaseEntry },
      { path: 'bulk-upload', name: 'BulkUpload', component: BulkFileUpload },
      { path: 'case-details', name: 'CaseDetails', component: CaseDetails },
      { path: 'review-assigned-cases', name: 'ReviewAssignedCases', component: () => import('@/pages/ReviewAssignedCases.vue') },
      { path: 'my-activity', name: 'UserActivity', component: UserActivity },
      { path: 'supervisor-worklist', name: 'SupervisorWorklist', component: () => import('@/pages/SupervisorWorklist.vue') },
      { path: 'delayed-cases', name: 'DelayedCases', component: () => import('@/pages/DelayedCases.vue') },
      { path: 'template-library', name: 'TemplateDisplay', component: () => import('@/pages/TemplateDisplay.vue') },
      
      // --- All your case detail pages ---
      {
        path: 'case-details/:case_id',
        name: 'CaseRiskReview', // Fallback/Default
        component: () => import('@/pages/CaseRiskReview.vue'),
        props: true,
      },
      {
        path: 'operational-action/:case_id',
        name: 'OperationalAction', // For VM cases
        component: () => import('@/pages/OperationalAction.vue'),
        props: true,
      },
      {
        path: 'beneficiary-action/:case_id',
        name: 'BeneficiaryAction', // For BM cases
        component: () => import('@/pages/BeneficiaryAction.vue'),
        props: true,
      },
      // --- NEWLY ADDED ROUTES ---
      {
        path: 'pma-action/:case_id',
        name: 'PMAAction',
        component: () => import('@/pages/PMAAction.vue'),
        props: true,
      },
      {
        path: 'pva-action/:case_id',
        name: 'PVAAction',
        component: () => import('@/pages/PVAAction.vue'),
        props: true,
      },
      {
        path: 'psa-action/:case_id',
        name: 'PSAAction',
        component: () => import('@/pages/PSAAction.vue'),
        props: true,
      },
      {
        path: 'psa-email-action/:case_id',
        name: 'PSAEmailAction',
        component: () => import('@/pages/PSAAction.vue'),
        props: true,
        meta: { isEmailCase: true },
      },
      {
        path: 'ecbt-action/:case_id',
        name: 'ECBTAction',
        component: () => import('@/pages/ECBTAction.vue'),
        props: true,
      },
      {
        path: 'ecbt-email-action/:case_id',
        name: 'ECBTEmailAction',
        component: () => import('@/pages/ECBTAction.vue'),
        props: true,
        meta: { isEmailCase: true },
      },
      {
        path: 'ecbnt-action/:case_id',
        name: 'ECBNTAction',
        component: () => import('@/pages/ECBNTAction.vue'),
        props: true,
      },
      {
        path: 'ecbnt-email-action/:case_id',
        name: 'ECBNTEmailAction',
        component: () => import('@/pages/ECBNTAction.vue'),
        props: true,
        meta: { isEmailCase: true },
      },
      {
        path: 'nab-action/:case_id',
        name: 'NABAction',
        component: () => import('@/pages/NABAction.vue'),
        props: true,
      },
      // --- MOBILE MATCHING (MM) CASE ROUTE ---
      {
        path: 'mobile-matching-action/:case_id',
        name: 'MobileMatchingAction',
        component: () => import('@/pages/MobileMatchingAction.vue'),
        props: true,
      },
      // --- NEW SUPERVISOR TEMPLATE REVIEW ROUTE ---
      {
        path: 'supervisor-template-review/:case_id',
        name: 'SupervisorTemplateReview',
        component: () => import('@/pages/SupervisorTemplateReview.vue'),
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
        // Check if user with type "others" is trying to access restricted routes
      else if (to.meta.requiresAuth && loggedIn) {
        const userType = localStorage.getItem('user_type');
        if (userType === 'others') {
          // Users with type "others" can only access case-details, simple-dashboard, and all case detail pages
          if (to.path === '/dashboard' || to.path === '/') {
            next('/simple-dashboard');
            return;
          }
          
          // Allow access to case-details list page
          if (to.path === '/case-details') {
            next();
            return;
          }

          // Allow access to user activity page
          if (to.path === '/my-activity') {
            next();
            return;
          }
          
          // Allow access to simple-dashboard
          if (to.path === '/simple-dashboard') {
            next();
            return;
          }
          
          // Allow access to template library
          if (to.path === '/template-library') {
            next();
            return;
          }
          
          // Allow access to all case detail pages (operational-action, beneficiary-action, etc.)
          if (to.path.includes('-action/') || to.path.includes('case-details/')) {
            next();
            return;
          }
          
          // Block access to all other pages
          next('/simple-dashboard');
          return;
        }
      }
  
  // Otherwise, let them proceed.
  next();
});