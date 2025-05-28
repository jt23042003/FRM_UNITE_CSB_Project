<template>
  <div class="app">
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>

</script>


<!-- <template>
  <div>
    <router-view v-slot="{ Component, route }">
      <div v-if="route.path === '/login'">
        <component :is="Component" />
      </div>
      <div v-else class="app">
        <Sidebar />
        <div class="main-content">
          <Topbar />
          <component :is="Component" />
        </div>
      </div>
    </router-view>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
import Topbar from './components/Topbar.vue'
</script> -->
