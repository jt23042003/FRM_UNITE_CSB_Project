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

    // FIX: Extract data from res.data (response body)
    const accessToken = res.data.access_token;
    const refreshToken = res.data.refresh_token; // Assuming you return refresh_token
    const userType = res.data.user_type;     // FIX: Extract user_type
    const loggedInUsername = res.data.username; // FIX: Extract username

    if (accessToken) {
      // Store all relevant data in localStorage
      localStorage.setItem('jwt', accessToken);
      localStorage.setItem('refresh_token', refreshToken); // Store refresh token if you get it
      localStorage.setItem('user_type', userType);         // FIX: Store user_type
      localStorage.setItem('username', loggedInUsername);   // FIX: Store username

      // Set default Authorization header for Axios for all subsequent requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`; // Use accessToken directly
      
      router.push('/dashboard'); // Redirect to dashboard after successful login
    } else {
      // This case should ideally not happen if login is successful but token is missing from body
      throw new Error('Authentication token was not found in the response body.');
    }
  } catch (err) {
    // Handle specific error messages from backend if available (e.g., err.response.data.detail)
    error.value = err.response?.data?.detail || 'Invalid username or password. Please try again.';
    console.error('Login error:', err.response?.data || err.message);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
  @import '@/assets/login.css'; /* Your existing global styles */
</style>