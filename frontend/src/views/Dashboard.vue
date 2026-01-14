<template>
  <div class="p-8 space-y-8">
    
    <!-- Title Section -->
    <div>
      <h1 class="text-2xl font-bold text-white mb-6">Dashboard General</h1>
      
      <!-- KPI Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Empresas Activas" 
          value="6"
        />
        <StatCard 
          title="Ejecuciones Hoy" 
          value="0" 
          subValue="(0% Éxito)"
          subValueClass="text-green-500" 
        />
        <StatCard 
          title="Errores Hoy" 
          value="0"
          valueClass="text-red-500" 
        />
        <StatCard 
          title="PDFs Descargados" 
          value="0"
          valueClass="text-accent" 
        />
      </div>
    </div>

    <!-- Notifications Table Section -->
    <NotificationsTable />

  </div>
</template>

<script setup>
import StatCard from '../components/StatCard.vue';
import NotificationsTable from '../components/NotificationsTable.vue';
</script>
