<template>
  <div class="flex flex-col items-center justify-center min-h-full p-8 relative">
    <!-- Background Decor (Optional Grid/Glow) -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-dark to-dark"></div>
    </div>

    <!-- Content Container -->
    <div class="relative z-10 w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
      
      <!-- Left Column: Welcome Text -->
      <div class="space-y-6">
        <div class="bg-white rounded-2xl p-8 shadow-xl text-dark-lighter">
          <h1 class="text-3xl font-bold mb-2">
            ¡Bienvenido a <span class="text-primary">SUNATBOT</span>!
          </h1>
          <p class="text-secondary font-semibold mb-6">
            Tu asistente personal para la gestión tributaria.
          </p>
          
          <p class="text-gray-600 mb-4 leading-relaxed">
            SUNATBOT está diseñado para ayudarte a consultar, orientar y gestionar tu información tributaria de manera rápida, clara y segura.
          </p>

          <div class="space-y-3">
            <h3 class="font-bold text-dark-lighter">Con SUNATBOT podrás:</h3>
            <ul class="space-y-2 text-gray-600 text-sm">
              <li class="flex items-start">
                <span class="text-primary font-bold mr-2">•</span>
                Consultar los mensajes de SUNAT que recibes en tu Buzón.
              </li>
              <li class="flex items-start">
                <span class="text-primary font-bold mr-2">•</span>
                Descargar el SIRE del mes que elijas.
              </li>
              <li class="flex items-start">
                <span class="text-primary font-bold mr-2">•</span>
                Descargar tus comprobantes de una manera sencilla y rápida.
              </li>
            </ul>
          </div>

          <p class="text-gray-500 text-sm italic mt-8 border-t border-gray-200 pt-4">
            Comencemos cuando quieras. SUNATBOT está listo para ayudarte.
          </p>
        </div>
      </div>

      <!-- Right Column: Action Cards -->
      <div class="space-y-4">
        <!-- Card 1 -->
        <router-link to="/automatizacion" class="block w-full">
          <div class="w-full bg-white hover:bg-gray-50 hover:translate-x-2 transition-all duration-300 rounded-xl p-6 flex items-center shadow-lg group text-left cursor-pointer border border-transparent hover:border-primary/20">
            <div class="bg-blue-100 text-primary p-3 rounded-lg mr-4 group-hover:scale-110 transition-transform">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </div>
            <div>
              <h3 class="font-bold text-dark-lighter">Descarga de SIRE y Comprobante</h3>
            </div>
          </div>
        </router-link>

        <!-- Card 2 -->
        <router-link to="/dashboard" class="block w-full">
          <div class="w-full bg-white hover:bg-gray-50 hover:translate-x-2 transition-all duration-300 rounded-xl p-6 flex items-center shadow-lg group text-left cursor-pointer border border-transparent hover:border-accent/20">
            <div class="bg-orange-100 text-accent p-3 rounded-lg mr-4 group-hover:scale-110 transition-transform">
               <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 class="font-bold text-dark-lighter">Consulta de Buzón SUNAT</h3>
            </div>
          </div>
        </router-link>

         <!-- Card 3 -->
        <router-link to="/empresas" class="block w-full">
          <div class="w-full bg-white hover:bg-gray-50 hover:translate-x-2 transition-all duration-300 rounded-xl p-6 flex items-center shadow-lg group text-left cursor-pointer border border-transparent hover:border-green-500/20">
            <div class="bg-green-100 text-green-600 p-3 rounded-lg mr-4 group-hover:scale-110 transition-transform">
               <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div>
              <h3 class="font-bold text-dark-lighter">Registrar Empresas</h3>
            </div>
          </div>
        </router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
// Welcome page logic
</script>
