<template>
  <div>
    <h2 class="text-3xl font-bold text-white mb-6">Dashboard General</h2>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <!-- Total Empresas -->
      <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg hover:border-primary/50 transition-colors">
        <h3 class="text-gray-400 text-sm font-medium uppercase tracking-wider">Empresas Activas</h3>
        <p class="text-4xl font-bold text-white mt-2">{{ stats.total_empresas }}</p>
      </div>
      
      <!-- Ejecuciones Hoy -->
      <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg hover:border-primary/50 transition-colors">
        <h3 class="text-gray-400 text-sm font-medium uppercase tracking-wider">Ejecuciones Hoy</h3>
        <div class="flex items-end gap-2 mt-2">
            <p class="text-4xl font-bold text-white">{{ stats.runs_today?.total || 0 }}</p>
            <span class="text-sm text-green-400 mb-1">({{ stats.runs_today?.success_rate_percent }}% Éxito)</span>
        </div>
      </div>

      <!-- Errores Hoy -->
      <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg hover:border-red-500/50 transition-colors">
        <h3 class="text-gray-400 text-sm font-medium uppercase tracking-wider">Errores Hoy</h3>
        <p class="text-4xl font-bold text-red-500 mt-2">{{ stats.runs_today?.error || 0 }}</p>
      </div>

      <!-- PDFs Descargados -->
      <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg hover:border-accent/50 transition-colors">
        <h3 class="text-gray-400 text-sm font-medium uppercase tracking-wider">PDFs Descargados</h3>
        <p class="text-4xl font-bold text-accent mt-2">{{ stats.notifications?.total_downloaded || 0 }}</p>
      </div>
    </div>

    <!-- Filtros y Tabla -->
    <div class="bg-dark-lighter rounded-xl border border-gray-800 shadow-lg flex flex-col h-[600px]">
        <div class="p-6 border-b border-gray-800 flex justify-between items-center">
            <h3 class="text-xl font-bold text-white">Últimas Notificaciones</h3>
            <div class="flex gap-4">
                <input v-model="filters.search" placeholder="Buscar por RUC o Razón Social..." class="bg-dark border border-gray-700 text-sm rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary w-80" />
                <button @click="downloadZip" class="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                    ⬇️ Descargar ZIP Filtrado
                </button>
            </div>
        </div>

        <div class="flex-1 overflow-auto p-0">
            <table class="w-full text-left text-sm text-gray-400">
                <thead class="bg-gray-800/50 text-xs uppercase text-gray-300 sticky top-0">
                    <tr>
                        <th class="px-6 py-3 font-medium">Empresa / RUC</th>
                        <th class="px-6 py-3 font-medium">Asunto</th>
                        <th class="px-6 py-3 font-medium">Fecha Recibida</th>
                        <th class="px-6 py-3 font-medium">F. Descarga</th>
                        <th class="px-6 py-3 font-medium">Estado</th>
                        <th class="px-6 py-3 font-medium text-right">Acciones</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-800">
                    <tr v-for="notif in notifications" :key="notif.id" class="hover:bg-gray-800/30 transition-colors">
                        <td class="px-6 py-4">
                            <div class="font-medium text-white">{{ notif.razon_social }}</div>
                            <div class="text-xs text-gray-500">{{ notif.ruc }}</div>
                        </td>
                        <td class="px-6 py-4 max-w-xs truncate" :title="notif.asunto">{{ notif.asunto }}</td>
                        <td class="px-6 py-4">{{ formatDate(notif.fecha_recibido) || '-' }}</td>
                        <td class="px-6 py-4 text-gray-500 text-xs">{{ formatDate(notif.fecha_emision) }}</td>
                        <td class="px-6 py-4">
                            <span class="px-2 py-1 rounded-full text-xs font-semibold bg-green-900/30 text-green-400 border border-green-900">
                                {{ notif.estado }}
                            </span>
                        </td>
                        <td class="px-6 py-4 text-right">
                            <a :href="`${API_BASE_URL}/files/download/${notif.id}`" target="_blank" class="text-primary hover:text-blue-400 hover:underline">
                                Ver PDF
                            </a>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import api, { API_BASE_URL } from '../apiConfig';

const stats = ref({});
const notifications = ref([]);
const filters = ref({
    search: '',
    start_date: null,
    end_date: null
});

const fetchStats = async () => {
    try {
        const res = await api.get('/dashboard/stats');
        stats.value = res.data;
    } catch (e) {
        console.error("Error fetching stats", e);
    }
};

const fetchNotifications = async () => {
    try {
        const res = await api.get('/dashboard/notifications', { params: {
            search: filters.value.search || undefined,
            // TODO: bind dates
        }});
        notifications.value = res.data;
    } catch (e) {
        console.error("Error fetching notificacions", e);
    }
};

const downloadZip = () => {
    // Construir query string manualmente para abrir en nueva pestaña/descarga
    let url = `${API_BASE_URL}/files/batch-zip?`;
    // Nota: El backend de batch-zip tendria que soportar 'search' tambien si queremos consistencia, 
    // pero por ahora le pasamos el search como 'ruc' si es numerico o solo si queremos filtrar.
    // Dejamos pendiente la actualizacion de batch-zip para soportar search.
    if(filters.value.search) url += `search=${filters.value.search}&`;
    window.open(url, '_blank');
};

const formatDate = (dateStr) => {
    if(!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('es-PE', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

onMounted(() => {
    fetchStats();
    fetchNotifications();
});

watch(() => filters.value.search, () => {
    // Debounce simple
    setTimeout(fetchNotifications, 500);
});
</script>
