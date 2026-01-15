<template>
  <aside 
    class="fixed inset-y-0 left-0 w-64 bg-dark-lighter border-r border-dark-border flex flex-col transform transition-transform duration-300 ease-in-out z-50 shadow-2xl"
    :class="isOpen ? 'translate-x-0' : '-translate-x-full'"
  >
    <!-- Header -->
    <div class="p-6 border-b border-dark-border flex justify-between items-center">
      <div>
        <h1 class="text-xl font-bold text-primary tracking-wider">SUNAT<span class="text-white">BOT</span></h1>
        <p class="text-xs text-text-muted mt-1">v1.0.0 Alpha</p>
      </div>
      <!-- Close Button (Mobile/Overlay) -->
      <button @click="$emit('close')" class="text-gray-400 hover:text-white">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
      
      <!-- Group: Buzones -->
      <div class="space-y-1">
        <button 
          @click="toggleGroup('buzones')"
          class="w-full flex items-center justify-between px-4 py-3 text-text-muted hover:bg-dark-border/50 hover:text-white rounded-lg transition-colors group"
          :class="{ 'bg-dark-border/30 text-white': activeGroup === 'buzones' }"
        >
          <div class="flex items-center">
            <span class="mr-3">📬</span>
            <span class="font-medium">Buzones</span>
          </div>
          <svg class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': activeGroup === 'buzones' }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        <!-- Submenu Buzones -->
        <div v-show="activeGroup === 'buzones'" class="pl-4 space-y-1">
          <router-link to="/dashboard" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click.prevent="handleNav(navigate)" 
               :class="['flex items-center px-4 py-2 rounded-lg text-sm transition-colors', isActive ? 'bg-primary/20 text-primary' : 'text-gray-500 hover:text-gray-300']">
              Dashboard
            </a>
          </router-link>
          <router-link to="/automatizacion" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click.prevent="handleNav(navigate)" 
               :class="['flex items-center px-4 py-2 rounded-lg text-sm transition-colors', isActive ? 'bg-primary/20 text-primary' : 'text-gray-500 hover:text-gray-300']">
              Automatización
            </a>
          </router-link>
        </div>
      </div>

      <!-- Single Item: Empresas -->
      <router-link to="/empresas" custom v-slot="{ href, navigate, isActive }">
        <a :href="href" @click.prevent="handleNav(navigate)" 
           :class="['flex items-center px-4 py-3 rounded-lg transition-colors duration-200', isActive ? 'bg-primary/20 text-primary' : 'hover:bg-dark-border/50 text-text-muted hover:text-white']">
          <span class="mr-3">🏢</span>
          <span class="font-medium">Empresas</span>
        </a>
      </router-link>
      
      <!-- Group: Comprobantes -->
      <div class="space-y-1">
        <button 
          @click="toggleGroup('comprobantes')"
          class="w-full flex items-center justify-between px-4 py-3 text-text-muted hover:bg-dark-border/50 hover:text-white rounded-lg transition-colors group"
          :class="{ 'bg-dark-border/30 text-white': activeGroup === 'comprobantes' }"
        >
          <div class="flex items-center">
            <span class="mr-3">📄</span>
            <span class="font-medium">Comprobantes</span>
          </div>
          <svg class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': activeGroup === 'comprobantes' }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        <!-- Submenu Comprobantes -->
        <div v-show="activeGroup === 'comprobantes'" class="pl-4 space-y-1">
          <router-link to="/comprobantes/propuesta" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click.prevent="handleNav(navigate)" 
               :class="['flex items-center px-4 py-2 rounded-lg text-sm transition-colors', isActive ? 'bg-primary/20 text-primary' : 'text-gray-500 hover:text-gray-300']">
              Propuesta
            </a>
          </router-link>
          <router-link to="/comprobantes/descarga" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click.prevent="handleNav(navigate)" 
               :class="['flex items-center px-4 py-2 rounded-lg text-sm transition-colors', isActive ? 'bg-primary/20 text-primary' : 'text-gray-500 hover:text-gray-300']">
              Descarga CPE
            </a>
          </router-link>
          <router-link to="/comprobantes/repositorio" custom v-slot="{ href, navigate, isActive }">
            <a :href="href" @click.prevent="handleNav(navigate)" 
               :class="['flex items-center px-4 py-2 rounded-lg text-sm transition-colors', isActive ? 'bg-primary/20 text-primary' : 'text-gray-500 hover:text-gray-300']">
              Repositorio
            </a>
          </router-link>
        </div>
      </div>

    </nav>

    <!-- Footer -->
    <div class="p-4 border-t border-dark-border text-xs text-center text-text-muted">
      &copy; 2026 SUNATBOT
    </div>
  </aside>

  <!-- Overlay Backdrop -->
  <div 
    v-if="isOpen" 
    @click="$emit('close')"
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity"
  ></div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['close']);

const activeGroup = ref('buzones'); // Default open group

const toggleGroup = (group) => {
  activeGroup.value = activeGroup.value === group ? null : group;
};

const handleNav = (navigate) => {
  navigate();
  emit('close');
};
</script>
