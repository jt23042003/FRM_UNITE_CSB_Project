import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import axios from 'axios'

// Import styles - @import statements must come first
import './assets/base.css'
import './assets/main.css'
import './assets/styles.css'
import './assets/ui-pro.css'

// Global axios interceptor for JWT token expiration
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    // Check if it's a JWT expiration error (500 status with JWT expired message)
    if (error.response?.status === 500 && 
        (error.response?.data?.detail?.includes('JWTExpired') || 
         error.response?.data?.detail?.includes('Expired at'))) {
      
      // Clear stored tokens
      localStorage.removeItem('jwt')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_type')
      localStorage.removeItem('username')
      
      // Remove authorization header
      delete axios.defaults.headers.common['Authorization']
      
      // Show user-friendly error message using notification system
      if (window.showNotification) {
        window.showNotification('warning', 'Session Expired', 'Your session has expired. Please log in again.', 8000)
        // Redirect after a short delay to let user see the notification
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      } else {
        alert('Your session has expired. Please log in again.')
        router.push('/login')
      }
      
      return Promise.reject(error)
    }
    
    // For other errors, pass them through
    return Promise.reject(error)
  }
)

createApp(App).use(router).mount('#app')