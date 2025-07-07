<template>
  <div class="app">
    <aside class="sidebar">
      <div class="logo">
        UNITE Hub Technologies
        <img src="@/assets/unite_hub_tech_logo.png" class="logo-img" alt="Logo" />
      </div>
      <nav>
        <ul>
          <li><router-link to="/dashboard">Dashboard</router-link></li>
          <li><router-link to="/bulk-upload">File Upload</router-link></li>
          <li><router-link to="/data-entry">Data Entry</router-link></li>
          <li><router-link to="/case-details">Case Details</router-link></li>
          </ul>
      </nav>

      <button @click="logout" class="logout-btn">
        Logout
      </button>
    </aside>
    
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import axios from 'axios'; // Import axios to clear the default header

const router = useRouter();

const logout = () => {
  // 1. Remove the token from local storage
  localStorage.removeItem('jwt');

  // 2. Remove the default Authorization header from future axios requests
  delete axios.defaults.headers.common['Authorization'];

  // 3. Redirect the user to the login page
  router.push('/login');
};
</script>

<style scoped>
/* Assuming you have global styles, we'll just add to them */
@import '@/assets/styles.css';

/* Make the sidebar a flex container to position the logout button */
</style>