<template>
    <nav :class="['sidebar-ui', { collapsed }]">
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <img src="@/assets/unite_hub_tech_logo.png" class="sidebar-logo" alt="Logo" />
          <span v-if="!collapsed" class="sidebar-title">UNITE Hub<br>Technologies</span>
        </div>
        <button class="sidebar-toggle" @click="toggleSidebar" :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
          <svg v-if="collapsed" xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <div class="sidebar-search">
          <svg class="sidebar-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"/></svg>
          <input v-if="!collapsed" type="text" class="sidebar-search-input" placeholder="Search..." />
        </div>
      </div>
      <ul class="sidebar-menu">
        <li>
          <router-link to="/dashboard" class="sidebar-link" active-class="active">
            <svg class="sidebar-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M13 5v6h6"/></svg>
            <span v-if="!collapsed">Dashboard</span>
          </router-link>
        </li>
        <li>
          <router-link to="/bulk-upload" class="sidebar-link" active-class="active">
            <svg class="sidebar-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10V6a5 5 0 0110 0v4M12 16v-4m0 0l-2 2m2-2l2 2"/></svg>
            <span v-if="!collapsed">File Upload</span>
          </router-link>
        </li>
        <li>
          <router-link to="/data-entry" class="sidebar-link" active-class="active">
            <svg class="sidebar-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            <span v-if="!collapsed">Data Entry</span>
          </router-link>
        </li>
        <li>
          <router-link to="/case-details" class="sidebar-link" active-class="active">
            <svg class="sidebar-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2a4 4 0 014-4h4m0 0V7a4 4 0 00-4-4H7a4 4 0 00-4 4v10a4 4 0 004 4h4"/></svg>
            <span v-if="!collapsed">Case Details</span>
          </router-link>
        </li>
        <li v-if="userRole !== 'others'">
          <router-link to="/review-assigned-cases" class="sidebar-link" active-class="active">
            <svg class="sidebar-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            <span v-if="!collapsed">Review Assigned Cases</span>
          </router-link>
        </li>
      </ul>
      <div class="sidebar-bottom">
        <button class="sidebar-link sidebar-logout" @click="logout">
          <svg class="sidebar-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2h4a2 2 0 012 2v1"/></svg>
          <span v-if="!collapsed">Logout</span>
        </button>
        <div class="sidebar-toggle-mode">
          <svg class="sidebar-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m8.66-13.66l-.71.71M4.05 19.95l-.71.71M21 12h1M3 12H2m16.95 7.05l-.71-.71M4.05 4.05l-.71-.71M12 5a7 7 0 100 14 7 7 0 000-14z"/></svg>
          <span v-if="!collapsed">Light Mode</span>
          <label class="switch">
            <input type="checkbox" disabled />
            <span class="slider"></span>
          </label>
        </div>
      </div>
    </nav>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import axios from 'axios';
  
  const collapsed = ref(false);
  const router = useRouter();
  const userRole = ref('');
  
  function toggleSidebar() {
    collapsed.value = !collapsed.value;
  }
  
  function logout() {
    localStorage.removeItem('jwt');
    delete axios.defaults.headers.common['Authorization'];
    router.push('/login');
  }
  
  // Fetch user role on mount
  const fetchUserRole = async () => {
    try {
      const token = localStorage.getItem('jwt');
      if (!token) return;
      
      const response = await axios.get('/api/new-case-list', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data && response.data.logged_in_user_type) {
        userRole.value = response.data.logged_in_user_type;
      }
    } catch (err) {
      console.error('Failed to fetch user role:', err);
    }
  };
  
  onMounted(fetchUserRole);
  </script>
  
  <style scoped>
  .sidebar-ui {
    background: #23252b;
    color: #fff;
    min-width: 250px;
    max-width: 250px;
    height: 100vh;
    border-radius: 0;
    box-shadow: 0 8px 32px rgba(16,24,40,0.18);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 1.2rem 0.7rem 1.2rem 0.7rem;
    transition: max-width 0.25s cubic-bezier(.4,0,.2,1), min-width 0.25s cubic-bezier(.4,0,.2,1);
    position: relative;
    overflow: hidden;
    flex-shrink: 0;
  }
  .sidebar-ui.collapsed {
    min-width: 70px;
    max-width: 70px;
    padding: 1.2rem 0.3rem 1.2rem 0.3rem;
    border-radius: 0;
  }
  .sidebar-top {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.2rem;
  }
  .sidebar-brand {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.7rem;
  }
  .sidebar-logo {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    background: #fff;
    box-shadow: 0 2px 8px rgba(16,24,40,0.10);
  }
  .sidebar-title {
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
    line-height: 1.1;
    color: #fff;
  }
  .sidebar-toggle {
    background: none;
    border: none;
    color: #fff;
    cursor: pointer;
    margin-bottom: 0.5rem;
    margin-top: -0.5rem;
    align-self: flex-end;
    transition: color 0.18s;
    padding: 0.2rem;
    border-radius: 6px;
  }
  .sidebar-toggle:hover {
    background: #2d2f36;
  }
  .sidebar-search {
    background: #2d2f36;
    border-radius: 10px;
    display: flex;
    align-items: center;
    padding: 0.5rem 0.7rem;
    width: 100%;
    margin-bottom: 0.7rem;
    gap: 0.6rem;
  }
  .sidebar-search-input {
    background: transparent;
    border: none;
    color: #fff;
    font-size: 1rem;
    outline: none;
    width: 100%;
  }
  .sidebar-icon {
    width: 1.4em;
    height: 1.4em;
    color: #bdbdbd;
    flex-shrink: 0;
  }
  .sidebar-menu {
    list-style: none;
    padding: 0;
    margin: 0;
    flex: 1 1 auto;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }
  .sidebar-link {
    display: flex;
    align-items: center;
    gap: 1.1em;
    padding: 0.7em 1em;
    border-radius: 10px;
    color: #fff;
    font-size: 1.08rem;
    font-weight: 500;
    text-decoration: none;
    transition: background 0.18s, color 0.18s;
    margin-bottom: 0.1em;
  }
  .sidebar-link.active, .sidebar-link.router-link-exact-active {
    background: #35363c;
    color: #fff;
  }
  .sidebar-link:hover {
    background: #2d2f36;
    color: #fff;
  }
  .sidebar-bottom {
    border-top: 1px solid #35363c;
    padding-top: 1.2rem;
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    align-items: center;
  }
  .sidebar-logout {
    width: 100%;
    justify-content: flex-start;
    background: none;
    border: none;
    color: #fff;
    font-size: 1.08rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 1.1em;
    padding: 0.7em 1em;
    border-radius: 10px;
    cursor: pointer;
    transition: background 0.18s, color 0.18s;
  }
  .sidebar-logout:hover {
    background: #2d2f36;
  }
  .sidebar-toggle-mode {
    background: #2d2f36;
    border-radius: 10px;
    display: flex;
    align-items: center;
    gap: 0.7em;
    padding: 0.5em 1em;
    width: 100%;
    justify-content: space-between;
  }
  .switch {
    position: relative;
    display: inline-block;
    width: 38px;
    height: 22px;
  }
  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .slider {
    position: absolute;
    cursor: pointer;
    top: 0; left: 0; right: 0; bottom: 0;
    background: #444;
    border-radius: 22px;
    transition: .2s;
  }
  .switch input:checked + .slider {
    background: #fff;
  }
  .slider:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 3px;
    bottom: 3px;
    background: #fff;
    border-radius: 50%;
    transition: .2s;
  }
  .switch input:checked + .slider:before {
    transform: translateX(16px);
    background: #23252b;
  }
  /* Collapsed styles */
  .sidebar-ui.collapsed .sidebar-title,
  .sidebar-ui.collapsed .sidebar-search-input,
  .sidebar-ui.collapsed .sidebar-link span,
  .sidebar-ui.collapsed .sidebar-toggle-mode span {
    display: none;
  }
  .sidebar-ui.collapsed .sidebar-search {
    justify-content: center;
    padding: 0.5rem 0.2rem;
  }
  .sidebar-ui.collapsed .sidebar-toggle-mode {
    justify-content: center;
    padding: 0.5em 0.5em;
  }
  </style> 