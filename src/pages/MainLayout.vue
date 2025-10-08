<template>
  <div class="app">
    <div class="topbar" v-if="isMobile">
      <button class="hamburger" @click="openSidebar" aria-label="Open menu">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
      </button>
      <div class="topbar-title">Unite Hub</div>
    </div>
    <Sidebar />
    <div class="main">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import Sidebar from '@/components/Sidebar.vue';

const isMobile = ref(false);
function updateIsMobile() { isMobile.value = window.innerWidth <= 900; }
function openSidebar() { window.dispatchEvent(new CustomEvent('toggle-sidebar')); }

onMounted(() => { updateIsMobile(); window.addEventListener('resize', updateIsMobile); });
onBeforeUnmount(() => { window.removeEventListener('resize', updateIsMobile); });
</script>

<style scoped>
.app {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.topbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 56px;
  background: #23252b;
  color: #fff;
  display: none;
  align-items: center;
  gap: 0.75rem;
  padding: 0 0.75rem;
  z-index: 1100;
}
.hamburger { background: none; border: none; color: #fff; padding: 6px; border-radius: 6px; }
.topbar-title { font-weight: 700; letter-spacing: 0.3px; }

.main {
  flex: 1;
  overflow: auto;
  position: relative;
}

@media (max-width: 900px) {
  .topbar { display: flex; }
  .app { padding-top: 56px; }
}
</style>