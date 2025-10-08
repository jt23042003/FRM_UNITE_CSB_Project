<template>
  <TransitionGroup
    name="notification"
    tag="div"
    class="notification-container"
  >
    <div
      v-for="notification in notifications"
      :key="notification.id"
      :class="['notification', `notification-${notification.type}`]"
      @click="removeNotification(notification.id)"
    >
      <div class="notification-icon">
        <svg v-if="notification.type === 'success'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
        <svg v-else-if="notification.type === 'error'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
        <svg v-else-if="notification.type === 'warning'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 16v-4M12 8h.01"/>
        </svg>
      </div>
      
      <div class="notification-content">
        <h4 class="notification-title">{{ notification.title }}</h4>
        <p v-if="notification.message" class="notification-message">{{ notification.message }}</p>
      </div>
      
      <button class="notification-close" @click.stop="removeNotification(notification.id)">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
      
      <div class="notification-progress" v-if="notification.duration > 0"></div>
    </div>
  </TransitionGroup>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const notifications = ref([]);
let nextId = 1;

// Notification types: 'success', 'error', 'warning', 'info'
const showNotification = (type, title, message = '', duration = 5000) => {
  const id = nextId++;
  const notification = {
    id,
    type,
    title,
    message,
    duration,
    timestamp: Date.now()
  };
  
  notifications.value.push(notification);
  
  // Auto-remove after duration
  if (duration > 0) {
    setTimeout(() => {
      removeNotification(id);
    }, duration);
  }
  
  return id;
};

const removeNotification = (id) => {
  const index = notifications.value.findIndex(n => n.id === id);
  if (index > -1) {
    notifications.value.splice(index, 1);
  }
};

const clearAll = () => {
  notifications.value = [];
};

// Expose methods globally
onMounted(() => {
  window.showNotification = showNotification;
  window.removeNotification = removeNotification;
  window.clearAllNotifications = clearAll;
});

onUnmounted(() => {
  delete window.showNotification;
  delete window.removeNotification;
  delete window.clearAllNotifications;
});

// Expose for component usage
defineExpose({
  showNotification,
  removeNotification,
  clearAll
});
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 400px;
}

.notification {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: white;
  border-left: 4px solid;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  min-width: 300px;
  transition: all 0.3s ease;
}

.notification:hover {
  transform: translateX(-4px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

.notification-success {
  border-left-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
}

.notification-error {
  border-left-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, #fef2f2 100%);
}

.notification-warning {
  border-left-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

.notification-info {
  border-left-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
}

.notification-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.notification-success .notification-icon {
  color: #10b981;
}

.notification-error .notification-icon {
  color: #ef4444;
}

.notification-warning .notification-icon {
  color: #f59e0b;
}

.notification-info .notification-icon {
  color: #3b82f6;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
}

.notification-message {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.4;
}

.notification-close {
  flex-shrink: 0;
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
  margin-top: 2px;
}

.notification-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #6b7280;
}

.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: currentColor;
  animation: progress-shrink linear forwards;
}

.notification-success .notification-progress {
  background: #10b981;
}

.notification-error .notification-progress {
  background: #ef4444;
}

.notification-warning .notification-progress {
  background: #f59e0b;
}

.notification-info .notification-progress {
  background: #3b82f6;
}

@keyframes progress-shrink {
  from { width: 100%; }
  to { width: 0%; }
}

/* Animation classes */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification-move {
  transition: transform 0.3s ease;
}

/* Responsive design */
@media (max-width: 480px) {
  .notification-container {
    right: 10px;
    left: 10px;
    max-width: none;
  }
  
  .notification {
    min-width: auto;
  }
}
</style>
