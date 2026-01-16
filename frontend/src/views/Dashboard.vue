<template>
  <div class="p-8 space-y-8">
    
    <!-- Title Section -->
    <div>
      <h1 class="text-2xl font-bold text-white mb-6">Dashboard General</h1>
      
      <!-- KPI Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Empresas Activas" 
          :value="stats.total_empresas"
        />
        <StatCard 
          title="Ejecuciones Hoy" 
          :value="stats.runs_today.total" 
          :subValue="`(${stats.runs_today.success_rate_percent}% Éxito)`"
          subValueClass="text-green-500" 
        />
        <StatCard 
          title="Errores Hoy" 
          :value="stats.runs_today.error"
          valueClass="text-red-500" 
        />
        <StatCard 
          title="PDFs Descargados" 
          :value="stats.notifications.total_downloaded"
          valueClass="text-accent" 
        />
      </div>
    </div>

    <!-- Notifications Table Section -->
    <NotificationsTable />

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../apiConfig';
import StatCard from '../components/StatCard.vue';
import NotificationsTable from '../components/NotificationsTable.vue';

const stats = ref({
    total_empresas: 0,
    runs_today: {
        total: 0,
        success: 0,
        error: 0,
        success_rate_percent: 0
    },
    notifications: {
        total_downloaded: 0,
        pending_action: 0
    }
});

const fetchStats = async () => {
    try {
        const res = await api.get('/dashboard/stats');
        stats.value = res.data;
    } catch (e) {
        console.error("Error loading stats", e);
    }
};

onMounted(fetchStats);
</script>
