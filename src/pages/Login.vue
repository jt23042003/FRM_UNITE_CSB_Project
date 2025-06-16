<template>
  <div class="login-bg">
    <form class="login-card" @submit.prevent="login">
      
      <h2><span class="primary-text">UniteHub</span> Login</h2>

      <label>
        Username
        <input v-model="username" type="text" required placeholder="Enter your username" autocomplete="username" />
      </label>
      
      <label>
        Password
        <input v-model="password" type="password" required placeholder="••••••••" autocomplete="current-password" />
      </label>
      
      <button :disabled="loading" type="submit" class="login-btn">
        <span v-if="!loading">Login</span>
        <span v-else>Signing in...</span>
      </button>

      <div v-if="error" class="login-error">{{ error }}</div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const router = useRouter()

const login = async () => {
  error.value = ''
  loading.value = true
  try {
    const res = await axios.post('http://34.47.219.225:9000/api/login', {
      username: username.value,
      password: password.value
    })

    const token = res.headers.authorization?.split(' ')[1]
    if (token) {
      localStorage.setItem('jwt', token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      router.push('/dashboard')
    } else {
      throw new Error('Authentication token was not found in the response headers.');
    }
  } catch (err) {
    error.value = 'Invalid username or password'
    console.error(err)
  }
  loading.value = false
}
</script>

<style scoped>
  @import '@/assets/login.css'; /* Your existing global styles */
  </style>
