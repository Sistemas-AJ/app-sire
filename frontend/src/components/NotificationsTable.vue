<template>
  <div class="bg-dark-lighter rounded-lg border border-dark-border overflow-hidden">
    <!-- Header -->
    <div class="p-4 border-b border-dark-border flex justify-between items-center">
      <h2 class="text-lg font-bold text-white">Últimas Notificaciones</h2>
      <div class="flex gap-2">
        <input 
          type="text" 
          placeholder="Buscar por RUC o Razón Social..." 
          class="bg-dark border border-dark-border text-sm text-white rounded px-3 py-1.5 focus:outline-none focus:border-primary w-64"
        >
        <button class="bg-primary hover:bg-primary-dark text-white text-sm font-medium px-4 py-1.5 rounded transition-colors flex items-center">
          <span class="mr-1">⬇</span> Descargar ZIP Filtrado
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="bg-dark/50 text-text-muted uppercase text-xs">
          <tr>
            <th class="px-6 py-3 font-semibold">Empresa / RUC</th>
            <th class="px-6 py-3 font-semibold">Asunto</th>
            <th class="px-6 py-3 font-semibold">Fecha Recibida</th>
            <th class="px-6 py-3 font-semibold">F. Descarga</th>
            <th class="px-6 py-3 font-semibold">Estado</th>
            <th class="px-6 py-3 font-semibold text-right">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-dark-border">
          <!-- Placeholder Row -->
          <tr class="hover:bg-dark-border/30 transition-colors">
            <td class="px-6 py-4">
              <div class="font-medium text-white">AJ CONTRATISTAS</div>
              <div class="text-xs text-text-muted">20601234567</div>
            </td>
            <td class="px-6 py-4 text-gray-300">Orden de Pago Nro...</td>
            <td class="px-6 py-4 text-text-muted">14/01/2026</td>
            <td class="px-6 py-4 text-text-muted">-</td>
            <td class="px-6 py-4">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-500">
                Pendiente
              </span>
            </td>
            <td class="px-6 py-4 text-right">
              <button class="text-primary hover:text-primary-dark font-medium">Ver</button>
            </td>
          </tr>
           <!-- Empty State (Hidden for now) -->
           <!--
           <tr>
             <td colspan="6" class="px-6 py-12 text-center text-text-muted">
               No hay notificaciones recientes
             </td>
           </tr>
           -->
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
// Props/Logic for data will go here
</script>
