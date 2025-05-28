<template>
    <div class="login-bg">
      <form class="login-card" @submit.prevent="login">
        <h2>UniteHub Login</h2>
        <label>
          User ID
          <input v-model="userId" required autocomplete="userId" />
        </label>
        <label>
          Password
          <input v-model="password" type="password" required autocomplete="current-password" />
        </label>
        <button :disabled="loading" type="submit" class="login-btn">
          <span v-if="loading">Logging in...</span>
          <span v-else>Login</span>
        </button>
        <div v-if="error" class="login-error">{{ error }}</div>
      </form>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import axios from 'axios'
  import { useRouter } from 'vue-router'
  import '../assets/Login.css'
  
  const userId = ref('')
  const password = ref('')
  const loading = ref(false)
  const error = ref('')
  const router = useRouter()
  
  const login = async () => {
    error.value = ''
    loading.value = true
    try {
      // Replace with your backend login endpoint
      const res = await axios.post('http://your-backend/api/login', {
        userId: userId.value,
        password: password.value
      })
      const token = res.data.token
      localStorage.setItem('jwt', token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      router.push('/dashboard')
    } catch (err) {
      error.value = 'Invalid User Id or password'
    }
    loading.value = false
  }
  </script>