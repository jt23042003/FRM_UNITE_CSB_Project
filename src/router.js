import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/pages/MainLayout.vue'
import I4CCaseEntry from '@/pages/I4CCaseEntry.vue'
import CaseDetails from '@/pages/CaseDetails.vue'
import Dashboard from './pages/Dashboard.vue'
import CaseRiskReview from './pages/CaseRiskReview.vue'
import CaseScreen from './pages/CaseScreen.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: 'dashboard', name:'Dashboard', component: Dashboard },
      { path: 'data-entry', name:'DataEntry', component: I4CCaseEntry },
      { path: 'case-details', name:'CaseDetails', component: CaseDetails },
      { path: 'case-risk-review', name:'CaseRiskReview', component: CaseRiskReview },
      {
        path: 'case-details/:ackno',
        name: 'CaseScreen',
        component: CaseScreen,
        props: true
      }
      // Add more children routes here
    ]
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})

// import { createRouter, createWebHistory } from 'vue-router'
// import MainLayout from '@/pages/MainLayout.vue'
// import I4CCaseEntry from '@/pages/I4CCaseEntry.vue'
// import CaseDetails from '@/pages/CaseDetails.vue'
// import CaseViewDashboard from './pages/CaseViewDashboard.vue'
// import Dashboard from './pages/Dashboard.vue'
// import CaseManagement from './pages/CaseManagement.vue'

// const Login = () => import('@/pages/Login.vue')

// const routes = [
//   {
//     path: '/login',
//     component: Login
//   },
//   {
//     path: '/',
//     component: MainLayout,
//     meta: { requiresAuth: true },
//     children: [
//       { path: 'dashboard', name:'Dashboard', component: Dashboard },
      // { path: 'data-entry', name:'DataEntry', component: I4CCaseEntry },
      // { path: 'case-details', name:'CaseDetails', component: CaseDetails },
      // { path: 'case-risk-review', name:'CaseRiskReview', component: CaseRiskReview },
      // {
      //   path: 'case-details/:ackno',
      //   name: 'CaseScreen',
      //   component: CaseScreen,
      //   props: true
      // }
//       // Add more children routes here
//     ]
//   },
//   { path: '/:catchAll(.*)', redirect: '/login' }
// ]

// const router = createRouter({
//   history: createWebHistory(),
//   routes
// })

// // Route guard for JWT auth
// router.beforeEach((to, from, next) => {
//   const token = localStorage.getItem('jwt')
//   if (to.meta.requiresAuth && !token) {
//     next('/login')
//   } else if (to.path === '/login' && token) {
//     next('/dashboard')
//   } else {
//     next()
//   }
// })

// export { router }
