<template>
    <div class="action-page-bg">
      <h1 class="screen-header">ECBT Action Page</h1>
      <section class="card-section">
        <p>This is the detail page for ECBT cases.</p>
        <p><strong>Case ID:</strong> {{ case_id }}</p>
      </section>
    </div>
  </template>
  
  <script setup>
  import { defineProps } from 'vue';
  
  const props = defineProps({
    case_id: {
      type: String,
      required: true
    }
  });
  </script>