<template>
  <div class="app">
    <Sidebar />
    <div class="main">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue';
</script>

<style scoped>
.app {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.main {
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>