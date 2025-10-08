import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'

// Import styles - @import statements must come first
import './assets/base.css'
import './assets/main.css'
import './assets/styles.css'
import './assets/ui-pro.css'

createApp(App).use(router).mount('#app')