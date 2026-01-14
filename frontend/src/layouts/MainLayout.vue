<template>
  <div class="flex h-screen bg-dark text-text-main font-sans overflow-hidden">
    <!-- Persistent Sidebar -->
    <Sidebar />

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col h-full w-full">
      <!-- TopBar -->
      <TopBar />

      <!-- Scrollable Content -->
      <main class="flex-1 overflow-auto bg-dark p-0 relative">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from '../components/Sidebar.vue';
import TopBar from '../components/TopBar.vue';
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
