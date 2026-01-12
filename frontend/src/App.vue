<template>
  <div class="flex h-screen bg-dark text-gray-200 font-sans">
    <!-- Sidebar -->
    <aside class="w-64 bg-dark-lighter border-r border-gray-800 flex flex-col">
      <div class="p-6 border-b border-gray-800">
        <h1 class="text-xl font-bold text-primary tracking-wider">SUNAT<span class="text-white">BOT</span></h1>
        <p class="text-xs text-gray-500 mt-1">v1.0.0 Alpha</p>
      </div>

      <nav class="flex-1 p-4 space-y-2">
        <router-link to="/dashboard" custom v-slot="{ href, navigate, isActive }">
          <a :href="href" @click="navigate" 
             :class="['flex items-center px-4 py-3 rounded-lg transition-colors duration-200', isActive ? 'bg-primary/20 text-primary' : 'hover:bg-gray-800 text-gray-400']">
            <span>📊 Dashboard</span>
          </a>
        </router-link>
        
        <router-link to="/empresas" custom v-slot="{ href, navigate, isActive }">
          <a :href="href" @click="navigate" 
             :class="['flex items-center px-4 py-3 rounded-lg transition-colors duration-200', isActive ? 'bg-primary/20 text-primary' : 'hover:bg-gray-800 text-gray-400']">
            <span>🏢 Empresas</span>
          </a>
        </router-link>
        
        <router-link to="/automatizacion" custom v-slot="{ href, navigate, isActive }">
          <a :href="href" @click="navigate" 
             :class="['flex items-center px-4 py-3 rounded-lg transition-colors duration-200', isActive ? 'bg-primary/20 text-primary' : 'hover:bg-gray-800 text-gray-400']">
            <span>🤖 Automatización</span>
          </a>
        </router-link>
      </nav>

      <div class="p-4 border-t border-gray-800 text-xs text-center text-gray-600">
        &copy; 2026 Buzón Automator
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto bg-dark p-8">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
