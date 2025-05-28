<!-- src/layouts/MainLayout.vue -->
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
            <li><router-link to="/data-entry">Data Entry</router-link></li>
            <li><router-link to="/case-details">Case Details</router-link></li>
            <li><router-link to="/case-risk-review">Case Review</router-link></li>
            <!-- Add more routes here -->
          </ul>
        </nav>
      </aside>
      
      <main class="main">
        <router-view />
      </main>
    </div>
  </template>
  
  <script setup>
  // You can optionally add script logic here if needed
  </script>
  
  <style scoped>
  @import '@/assets/styles.css'; /* Your existing global styles */
  </style>