<template>
  <div class="bg-dark-lighter rounded-lg border border-dark-border overflow-hidden">
    <!-- Header -->
    <div class="p-4 border-b border-dark-border flex justify-between items-center">
      <h2 class="text-lg font-bold text-white">Últimas Notificaciones</h2>
      <div class="flex gap-2">
        <input 
          v-model="search"
          type="text" 
          placeholder="Buscar por RUC o Razón Social..." 
          class="bg-dark border border-dark-border text-sm text-white rounded px-3 py-1.5 focus:outline-none focus:border-primary w-64"
        >
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="bg-dark/50 text-gray-500 uppercase text-xs">
          <tr>
            <th class="px-6 py-3 font-semibold">Empresa / RUC</th>
            <th class="px-6 py-3 font-semibold">Asunto</th>
            <th class="px-6 py-3 font-semibold">Recibido (SUNAT)</th>
            <th class="px-6 py-3 font-semibold">Descargado</th>
            <th class="px-6 py-3 font-semibold">Estado</th>
            <th class="px-6 py-3 font-semibold text-right">Acciones</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-dark-border">
           <tr v-if="loading">
             <td colspan="6" class="px-6 py-12 text-center text-gray-500 animate-pulse">Cargando datos...</td>
           </tr>
           <tr v-else-if="notifications.length === 0">
             <td colspan="6" class="px-6 py-12 text-center text-gray-500">
               No hay notificaciones recientes
             </td>
           </tr>
           <tr v-for="notif in notifications" :key="notif.id" class="hover:bg-dark-border/30 transition-colors">
             <td class="px-6 py-4">
               <div class="font-bold text-white">{{ notif.razon_social }}</div>
               <div class="text-xs text-gray-500 font-mono">{{ notif.ruc }}</div>
             </td>
             <td class="px-6 py-4 text-gray-300">{{ notif.asunto }}</td>
             <td class="px-6 py-4 text-gray-400 text-xs">{{ notif.fecha_recibido ? new Date(notif.fecha_recibido).toLocaleString() : '-' }}</td>
             <td class="px-6 py-4 text-gray-400 text-xs">{{ notif.fecha_descarga ? new Date(notif.fecha_descarga).toLocaleString() : '-' }}</td>
             <td class="px-6 py-4">
               <span :class="getStatusClass(notif.estado)" class="px-2 py-0.5 rounded text-[10px] font-bold border uppercase">
                 {{ notif.estado }}
               </span>
             </td>
             <td class="px-6 py-4 text-right">
               <a v-if="notif.ruta_pdf" :href="getFileLink(notif.ruta_pdf)" target="_blank" class="text-primary hover:text-white font-bold text-xs underline">
                 Ver PDF
               </a>
             </td>
           </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import api from '../apiConfig';

const notifications = ref([]);
const loading = ref(false);
const search = ref('');
const startDate = ref('');
const endDate = ref('');

const fetchNotifications = async () => {
    loading.value = true;
    try {
        const params = {
            search: search.value,
            limit: 50
        };
        if(startDate.value) params.start_date = startDate.value;
        if(endDate.value) params.end_date = endDate.value;

        // Using /dashboard/notifications based on context
        const res = await api.get('/dashboard/notifications', { params });
        notifications.value = res.data;
    } catch (e) {
        console.error("Error loading notifications", e);
    } finally {
        loading.value = false;
    }
};

// Debounce search
let timeout = null;
watch(search, () => {
    if(timeout) clearTimeout(timeout);
    timeout = setTimeout(fetchNotifications, 500);
});

const getFileLink = (path) => path ? `/api/files/download?path=${encodeURIComponent(path)}` : '#';
const getStatusClass = (status) => {
    switch(status) {
        case 'LEIDO': return 'text-green-400 bg-green-900/30 border-green-900';
        case 'PENDIENTE': return 'text-yellow-400 bg-yellow-900/30 border-yellow-900'; 
        default: return 'text-gray-400 bg-gray-700';
    }
};

onMounted(fetchNotifications);
</script>
