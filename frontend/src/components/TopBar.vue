<template>
  <header class="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-8">
    <!-- Company Info -->
    <div class="flex items-center">
      <div class="bg-red-600 text-white p-1.5 rounded-full mr-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
           <path fill-rule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.9-1.352A1.125 1.125 0 0114.25 12h-3.883l-1.88 2.822A.75.75 0 008.96 16H5a2 2 0 01-2-2V5zm10.96 2c.58 0 .96.496.75 1.078l-3.046 5.334a.749.749 0 01-1.328 0L7.29 8.078A1.125 1.125 0 018.04 6.333h3.883c.58 0 .96.496.75 1.078l-.346.607h.653z" clip-rule="evenodd" />
           <!-- Generic icon placeholder since we don't have the logo asset -->
           <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
        </svg>
      </div>
      <h2 class="text-dark font-bold text-lg tracking-wide">AJ CONTRATISTAS GENERALES</h2>
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

<script setup>
// TopBar logic
</script>
