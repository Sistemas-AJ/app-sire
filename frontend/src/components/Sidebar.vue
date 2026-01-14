<template>
  <aside class="w-64 bg-dark-lighter border-r border-dark-border flex flex-col h-full">
    <!-- Header -->
    <div class="p-6 border-b border-dark-border">
      <h1 class="text-xl font-bold text-primary tracking-wider">SUNAT<span class="text-white">BOT</span></h1>
      <p class="text-xs text-text-muted mt-1">v1.0.0 Alpha</p>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 p-4 space-y-2">
      <router-link to="/dashboard" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center px-4 py-3 rounded-lg transition-colors duration-200', isActive ? 'bg-primary/20 text-primary' : 'hover:bg-dark-border/50 text-text-muted hover:text-white']">
          <span class="mr-3">📊</span>
          <span>Dashboard</span>
        </a>
      </router-link>
      
      <router-link to="/empresas" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center px-4 py-3 rounded-lg transition-colors duration-200', isActive ? 'bg-primary/20 text-primary' : 'hover:bg-dark-border/50 text-text-muted hover:text-white']">
          <span class="mr-3">🏢</span>
          <span>Empresas</span>
        </a>
      </router-link>
      
      <router-link to="/automatizacion" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click="navigate" 
           :class="['flex items-center px-4 py-3 rounded-lg transition-colors duration-200', isActive ? 'bg-primary/20 text-primary' : 'hover:bg-dark-border/50 text-text-muted hover:text-white']">
          <span class="mr-3">🤖</span>
          <span>Automatización</span>
        </a>
      </router-link>
    </nav>

    <!-- Footer -->
    <div class="p-4 border-t border-dark-border text-xs text-center text-text-muted">
      &copy; 2026 SUNATBOT
    </div>
  </aside>
</template>

<script setup>
// Sidebar logic if needed
</script>
