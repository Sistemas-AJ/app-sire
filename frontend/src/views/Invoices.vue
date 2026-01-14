<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold text-white mb-6">{{ title }}</h1>
    <div class="bg-dark-lighter rounded-lg p-8 border border-dark-border flex flex-col items-center justify-center text-center h-64">
      <div class="text-6xl mb-4">📄</div>
      <h2 class="text-xl font-bold text-white mb-2">Módulo en Construcción</h2>
      <p class="text-text-muted">La funcionalidad de {{ title }} estará disponible pronto.</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const title = computed(() => {
  if (route.path.includes('propuesta')) return 'Propuesta del RVIE y RCE';
  if (route.path.includes('descarga')) return 'Descarga de XML y CDR';
  return 'Comprobantes';
});
</script>
