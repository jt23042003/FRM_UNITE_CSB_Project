import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'

// Import styles
import './assets/base.css'
import './assets/main.css'
import './assets/styles.css'

createApp(App).use(router).mount('#app')