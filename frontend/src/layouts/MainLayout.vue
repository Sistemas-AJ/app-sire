<template>
  <div class="flex h-screen bg-dark text-text-main font-sans overflow-hidden">
    <!-- TopBar (Fixed state logic could be added, but here it's part of flex col) -->
    
    <!-- Collapsible Sidebar (Overlay) -->
    <Sidebar :isOpen="isSidebarOpen" @close="isSidebarOpen = false" />

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col h-full w-full relative">
      <!-- TopBar -->
      <TopBar @toggle-sidebar="toggleSidebar" />

      <!-- Scrollable Content -->
      <main class="flex-1 overflow-auto bg-dark p-0 relative w-full">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <keep-alive>
               <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Sidebar from '../components/Sidebar.vue';
import TopBar from '../components/TopBar.vue';

const isSidebarOpen = ref(false); // Default closed

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value;
};
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
