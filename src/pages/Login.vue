<template>
  <div class="login-split-root">
    <!-- Left: Login Form -->
    <div class="login-split-left">
      <div class="login-form-card animate-fadein-left">
        <img src="@/assets/unite_hub_tech_logo.png" alt="UniteHub Tech Logo" class="login-logo" />
        <h1 class="login-title">Login Account</h1>
        <p class="login-subtitle">Sign in to your UniteHub Tech account</p>
        <form @submit.prevent="login" class="login-form" novalidate>
          <div class="form-group">
            <label for="username" class="form-label">Username <span class="required">*</span></label>
            <input
              id="username"
              v-model.trim="username"
              type="text"
              autocomplete="username"
              :class="['form-input', { 'input-error': usernameError }]"
              placeholder="Enter your username"
              required
              @blur="validateUsername"
            />
            <div v-if="usernameError" class="form-error">{{ usernameError }}</div>
          </div>
          <div class="form-group">
            <label for="password" class="form-label">Password <span class="required">*</span></label>
            <div class="input-wrapper">
              <input
                id="password"
                v-model.trim="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                :class="['form-input', { 'input-error': passwordError }]"
                placeholder="Enter your password"
                required
                @blur="validatePassword"
              />
              <button type="button" class="toggle-password" @click="showPassword = !showPassword" :aria-label="showPassword ? 'Hide password' : 'Show password'">
                <svg v-if="showPassword" xmlns="http://www.w3.org/2000/svg" class="icon-eye" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M1.5 12C3.5 7 7.5 4 12 4s8.5 3 10.5 8c-2 5-6 8-10.5 8s-8.5-3-10.5-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="icon-eye" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.06 10.06 0 0 1 12 20c-4.5 0-8.5-3-10.5-8a17.6 17.6 0 0 1 4.06-5.94M9.53 9.53A3 3 0 0 1 12 9c1.66 0 3 1.34 3 3 0 .47-.11.91-.29 1.29M1 1l22 22"/></svg>
              </button>
            </div>
            <div v-if="passwordError" class="form-error">{{ passwordError }}</div>
          </div>
          <div class="form-row-between">
            <label class="remember-me">
              <input type="checkbox" v-model="rememberMe" /> <span>Remember me for 30 days</span>
            </label>
            <a href="#" class="forgot-link">Forgot your password?</a>
          </div>
          <button type="submit" class="login-btn" :disabled="loading">
            <span class="login-btn-text">Log In</span>
            <span v-if="loading" class="spinner"></span>
            <svg class="arrow-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3"/></svg>
          </button>
          <div v-if="error" class="form-error form-error-main">{{ error }}</div>
        </form>
      </div>
      <footer class="login-footer">© 2024 UniteHub Tech. All rights reserved.</footer>
    </div>
    <!-- Right: Welcome/Branding with image background -->
    <div class="login-split-right animate-fadein-right">
      <div class="right-image-bg"></div>
      <div class="right-content">
        <div class="right-logo-bg">
          <img src="@/assets/unite_hub_tech_logo.png" alt="UniteHub Tech Logo" class="right-logo" />
        </div>
        <div class="right-text-block">
          <h2 class="right-welcome">Welcome to</h2>
          <h1 class="right-brand">UniteHub Tech</h1>
          <p class="right-desc">Financial Risk Management Platform</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { API_ENDPOINTS } from '@/config/api'

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')
const usernameError = ref('')
const passwordError = ref('')
const rememberMe = ref(false)
const router = useRouter()

function validateUsername() {
  usernameError.value = username.value.trim() === '' ? 'Username is required.' : ''
}
function validatePassword() {
  passwordError.value = password.value.trim() === '' ? 'Password is required.' : ''
}

const login = async () => {
  error.value = ''
  validateUsername()
  validatePassword()
  if (usernameError.value || passwordError.value) return
  loading.value = true
  try {
    const res = await axios.post(API_ENDPOINTS.LOGIN, {
      username: username.value,
      password: password.value
    })
    const accessToken = res.data.access_token
    const refreshToken = res.data.refresh_token
    const userType = res.data.user_type
    const loggedInUsername = res.data.username
    if (accessToken) {
      localStorage.setItem('jwt', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
      localStorage.setItem('user_type', userType)
      localStorage.setItem('username', loggedInUsername)
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
      router.push('/dashboard')
    } else {
      throw new Error('Authentication token was not found in the response body.')
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Invalid username or password. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-split-root {
  min-height: 100vh;
  height: 100vh;
  width: 100vw;
  display: flex;
  background: #f7f7f8;
  overflow: hidden;
}
.login-split-left, .login-split-right {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-width: 0;
}
.login-split-left {
  background: #fff;
  z-index: 2;
  box-shadow: 2px 0 24px 0 rgba(16,24,40,0.04);
  position: relative;
}
.login-form-card {
  width: 100%;
  max-width: 480px;
  padding: 3.5rem 3rem 2.5rem 3rem;
  border-radius: 22px;
  box-shadow: 0 8px 48px rgba(16, 24, 40, 0.13);
  border: 1px solid #ececec;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  animation: fadein-left 0.7s cubic-bezier(.4,0,.2,1);
  background: #fff;
  margin: 0 auto;
}
.login-logo {
  width: 60px;
  height: 60px;
  object-fit: contain;
  margin: 0 auto 1.2rem auto;
  border-radius: 8px;
  background: #fff;
  display: block;
}
.login-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #222;
  margin-bottom: 0.3rem;
  text-align: left;
  letter-spacing: -0.01em;
  width: 100%;
}
.login-subtitle {
  color: #666;
  text-align: left;
  margin-bottom: 2.2rem;
  font-size: 1.05rem;
  width: 100%;
}
.login-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  width: 100%;
}
.form-label {
  font-size: 1.01rem;
  font-weight: 500;
  color: #222;
  margin-bottom: 0.2rem;
  display: flex;
  align-items: center;
  gap: 0.2rem;
}
.required {
  color: #e11d48;
  font-size: 1em;
}
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}
.form-input {
  width: 100%;
  padding: 0.7rem 2.5rem 0.7rem 0.9rem;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 1.05rem;
  background: #fafbfc;
  color: #222;
  transition: border 0.2s;
  box-sizing: border-box;
}
.form-input:focus {
  border-color: #222;
  background: #fff;
  outline: none;
}
.input-error {
  border-color: #e11d48 !important;
}
.toggle-password {
  position: absolute;
  right: 0.7rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: #888;
  display: flex;
  align-items: center;
  height: 100%;
}
.icon-eye {
  width: 1.25em;
  height: 1.25em;
}
.form-row-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0.2rem 0 0.5rem 0;
  width: 100%;
  gap: 1.2rem;
}
.remember-me {
  font-size: 1.01rem;
  color: #444;
  display: flex;
  align-items: center;
  gap: 0.4em;
  user-select: none;
}
.forgot-link {
  font-size: 1.01rem;
  color: #888;
  text-decoration: underline;
  cursor: pointer;
  transition: color 0.18s;
  margin-left: 0.5em;
}
.forgot-link:hover {
  color: #222;
}
.login-btn {
  width: 100%;
  margin-top: 0.2rem;
  padding: 0.9rem 0;
  background: #222;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1.13rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.18s;
  box-shadow: 0 2px 8px rgba(16, 24, 40, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
}
.login-btn-text {
  display: inline-block;
  vertical-align: middle;
}
.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.arrow-icon {
  width: 1.3em;
  height: 1.3em;
  margin-left: 0.2em;
  stroke: #fff;
  vertical-align: middle;
  display: inline-block;
}
.spinner {
  width: 1.2em;
  height: 1.2em;
  border: 2.5px solid #e5e7eb;
  border-top: 2.5px solid #222;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.form-error {
  color: #e11d48;
  font-size: 1.01rem;
  margin-top: 0.2rem;
  font-weight: 500;
  text-align: left;
}
.form-error-main {
  text-align: center;
  margin-top: 1.1rem;
}
.login-footer {
  margin-top: 2.2rem;
  font-size: 0.97rem;
  color: #888;
  text-align: center;
}
/* Right Side */
.login-split-right {
  background: #f3f3f3;
  position: relative;
  overflow: hidden;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.right-image-bg {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: url('@/assets/scott-graham-5fNmWej4tAA-unsplash.jpg') center center/cover no-repeat;
  filter: grayscale(0.15) brightness(0.93);
  opacity: 0.93;
}
.right-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 0;
  height: 100%;
}
.right-logo-bg {
  background: #fff;
  border-radius: 50%;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 2.2rem auto;
  box-shadow: 0 2px 12px rgba(16,24,40,0.08);
}
.right-logo {
  width: 70px;
  height: 70px;
  object-fit: contain;
}
.right-text-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: 0.5rem;
}
.right-welcome {
  font-size: 1.18rem;
  color: #444;
  margin-bottom: 0.2rem;
  text-align: center;
}
.right-brand {
  font-size: 2.2rem;
  font-weight: 700;
  color: #222;
  margin-bottom: 0.5rem;
  text-align: center;
  letter-spacing: -0.01em;
}
.right-desc {
  color: #666;
  text-align: center;
  font-size: 1.09rem;
  margin-bottom: 1.5rem;
}
/* Animations */
.animate-fadein-left {
  animation: fadein-left 0.7s cubic-bezier(.4,0,.2,1);
}
.animate-fadein-right {
  animation: fadein-right 0.7s cubic-bezier(.4,0,.2,1);
}
@keyframes fadein-left {
  from { opacity: 0; transform: translateX(-40px); }
  to { opacity: 1; transform: none; }
}
@keyframes fadein-right {
  from { opacity: 0; transform: translateX(40px); }
  to { opacity: 1; transform: none; }
}
/* Responsive */
@media (max-width: 1100px) {
  .login-form-card { max-width: 98vw; padding: 2.2rem 1.2rem 1.2rem 1.2rem; }
  .right-logo-bg { width: 70px; height: 70px; }
  .right-logo { width: 50px; height: 50px; }
  .right-brand { font-size: 1.5rem; }
}
@media (max-width: 900px) {
  .login-split-root {
    flex-direction: column;
  }
  .login-split-left, .login-split-right {
    min-height: 320px;
    width: 100vw;
    max-width: 100vw;
  }
  .login-split-left {
    box-shadow: none;
    border-bottom: 1px solid #ececec;
  }
  .login-split-right {
    min-height: 220px;
    box-shadow: none;
    border-top: none;
  }
  .right-content { height: auto; }
}
@media (max-width: 600px) {
  .login-form-card {
    padding: 1.2rem 0.5rem 1.2rem 0.5rem;
    max-width: 98vw;
  }
  .right-logo-bg {
    width: 50px; height: 50px;
  }
  .right-logo {
    width: 30px; height: 30px;
  }
  .right-brand {
    font-size: 1.1rem;
  }
}
</style>