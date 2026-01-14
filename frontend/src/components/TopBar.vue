<script setup>
import logo from '../assets/Logo_Principal.png';
// TopBar logic
</script>

<template>
  <header class="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-8">
    <!-- Left Section: Hamburger + Company Info -->
    <div class="flex items-center">
      <!-- Hamburger Menu -->
      <button @click="$emit('toggle-sidebar')" class="mr-4 text-gray-500 hover:text-dark focus:outline-none">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Company Logo -->
      <img :src="logo" alt="AJ CONTRATISTAS GENERALES" class="h-8 object-contain" />
    </div>

    <!-- User Profile / Actions -->
    <div class="flex items-center space-x-6">
      <div class="text-right hidden md:block">
        <div class="text-xs text-gray-400 font-bold uppercase tracking-wider">ADMIN</div>
        <div class="flex items-center">
          <span class="w-2 h-2 rounded-full bg-green-500 mr-1.5"></span>
          <span class="text-xs text-secondary font-medium bg-gray-100 px-2 py-0.5 rounded-full">Conectado</span>
        </div>
      </div>
      
      <div class="w-10 h-10 rounded-full bg-dark text-white flex items-center justify-center hover:bg-dark-lighter cursor-pointer transition-colors">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      </div>

      <button class="flex items-center text-secondary hover:text-red-500 transition-colors text-sm font-medium">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        Cerrar Sesión
      </button>
    </div>
  </header>
</template>
