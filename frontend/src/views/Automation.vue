<template>
  <div class="p-8">
    <h2 class="text-3xl font-bold text-white mb-6">Panel de Control de Automatización</h2>

    <!-- Actions Card -->
    <div class="bg-dark-lighter p-8 rounded-xl border border-gray-800 shadow-lg mb-8">
        <div class="flex flex-col md:flex-row justify-between items-center gap-6">
            <div>
                <h3 class="text-xl font-bold text-white mb-2">Ejecutar Robot</h3>
                <p class="text-gray-400 text-sm max-w-md">
                    Inicia el proceso de descarga masiva. El robot analizará los buzones de todas las empresas activas según los filtros configurados.
                </p>
                
                <div class="flex gap-4 mt-4">
                    <label class="flex items-center gap-2 text-gray-300 text-sm cursor-pointer">
                        <input type="radio" v-model="runMode" value="todo" class="text-primary focus:ring-primary" />
                        <span>Procesar Todo</span>
                    </label>
                    <label class="flex items-center gap-2 text-gray-300 text-sm cursor-pointer">
                        <input type="radio" v-model="runMode" value="solo_fallidos" class="text-primary focus:ring-primary" />
                        <span>Solo Fallidos / Pendientes</span>
                    </label>
                </div>
                
                <div class="flex items-center gap-2 mt-4 text-sm text-gray-400">
                    <span>Analizar mensajes desde:</span>
                    <input type="date" v-model="startDate" :max="todayDate" class="bg-dark border border-gray-700 rounded px-2 py-1 text-white text-center" />
                </div>

                <div class="mt-4">
                    <label class="flex items-center gap-2 text-sm text-gray-300 cursor-pointer select-none">
                        <div class="relative">
                            <input type="checkbox" v-model="showBrowser" class="sr-only peer">
                            <div class="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                        </div>
                        <span class="font-medium">Mostrar Ventana (Navegador visible)</span>
                    </label>
                </div>
            </div>
            
            <div class="flex flex-col gap-2">
                <button 
                    v-if="!isRunning"
                    @click="runAutomation" 
                    class="relative overflow-hidden group bg-primary hover:bg-blue-600 text-white px-8 py-4 rounded-xl text-lg font-bold transition-all shadow-lg shadow-primary/20 transform hover:-translate-y-1">
                    <span class="flex items-center gap-3">
                        🚀 INICIAR AUTOMATIZACIÓN
                    </span>
                </button>

                <button 
                    v-else
                    @click="stopAutomation" 
                    class="relative overflow-hidden group bg-red-600 hover:bg-red-700 text-white px-8 py-4 rounded-xl text-lg font-bold transition-all shadow-lg shadow-red-600/20 transform hover:-translate-y-1">
                    <span class="flex items-center gap-3">
                        🛑 DETENER (AL FINALIZAR EMPRESA)
                    </span>
                </button>
                <div v-if="isRunning" class="flex flex-col items-center gap-2">
                    <p class="text-xs text-gray-500 text-center animate-pulse">El robot se detendrá tras completar la empresa actual.</p>
                    <button @click="forceReset" class="text-xs text-red-400 hover:text-red-300 underline mt-1">
                        (Forzar reinicio de estado)
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Live Status -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Status Chart / List -->
        <div class="bg-dark-lighter rounded-xl border border-gray-800 shadow-lg p-6">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-white">Estado Actual (Tiempo Real)</h3>
                <button @click="fetchStatus" class="text-xs text-primary hover:underline">Refrescar</button>
            </div>
            
            <div v-if="statusData" class="space-y-4">
                <div class="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span class="text-gray-400">Total Empresas</span>
                    <span class="text-white font-bold">{{ statusData.resumen.total_empresas }}</span>
                </div>
                
                <div class="space-y-2">
                    <div class="flex justify-between text-xs text-gray-500 uppercase">
                        <span>Progreso</span>
                        <span>{{ statusData.resumen.completados + statusData.resumen.sin_novedades }} / {{ statusData.resumen.total_empresas }}</span>
                    </div>
                     <div class="w-full bg-gray-700 rounded-full h-2.5">
                        <div class="bg-primary h-2.5 rounded-full transition-all duration-500" :style="{ width: ((statusData.resumen.completados + statusData.resumen.sin_novedades) / statusData.resumen.total_empresas * 100) + '%' }"></div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4 pt-2">
                    <div class="text-center p-3 rounded-lg border border-gray-800 bg-gray-800/20">
                        <div class="text-2xl font-bold text-yellow-500">{{ statusData.resumen.pendientes }}</div>
                        <div class="text-xs text-gray-500">Pendientes</div>
                    </div>
                    <div class="text-center p-3 rounded-lg border border-gray-800 bg-gray-800/20">
                        <div class="text-2xl font-bold text-green-500">{{ statusData.resumen.completados + statusData.resumen.sin_novedades }}</div>
                        <div class="text-xs text-gray-500">Completados</div>
                    </div>
                     <div class="text-center p-3 rounded-lg border border-gray-800 bg-gray-800/20">
                        <div class="text-2xl font-bold text-blue-500">{{ statusData.resumen.procesando }}</div>
                        <div class="text-xs text-gray-500">Procesando</div>
                    </div>
                    <div class="text-center p-3 rounded-lg border border-gray-800 bg-gray-800/20">
                        <div class="text-2xl font-bold text-red-500">{{ statusData.resumen.errores }}</div>
                        <div class="text-xs text-gray-500">Errores</div>
                    </div>
                </div>
            </div>
            <div v-else class="text-center py-10 text-gray-500">
                Cargando estado...
            </div>
        </div>

        <!-- Error Log -->
        <div class="bg-dark-lighter rounded-xl border border-gray-800 shadow-lg p-6 overflow-hidden flex flex-col max-h-[500px]">
             <h3 class="text-lg font-bold text-red-400 mb-4 flex items-center gap-2">
                <span>⚠️</span> Registro de Errores ({{ errors.length }})
             </h3>
             
             <div class="flex-1 overflow-auto space-y-3 pr-2 custom-scrollbar">
                <div v-for="(err, idx) in errors" :key="idx" class="bg-red-900/10 border border-red-900/30 p-3 rounded-lg text-sm">
                    <div class="flex justify-between items-start mb-1">
                        <span class="font-bold text-red-300">{{ err.razon_social }}</span>
                        <span class="text-xs text-red-500/70">{{ new Date(err.fecha).toLocaleTimeString() }}</span>
                    </div>
                    <p class="text-gray-400 break-words font-mono text-xs">{{ err.error }}</p>
                </div>
                <div v-if="errors.length === 0" class="text-center py-10 text-gray-600">
                    🎉 Sin errores reportados
                </div>
             </div>
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import api from '../apiConfig';

const isRunning = ref(false);
const runMode = ref('todo');
const showBrowser = ref(false); // Default visible
const manuallyStopped = ref(false); // Flag to ignore backend "running" state if forced
// Inicializar hace 7 dias
const getSevenDaysAgo = () => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split('T')[0];
};
const getToday = () => new Date().toISOString().split('T')[0];

const startDate = ref(getSevenDaysAgo());
const todayDate = getToday();

const statusData = ref(null);
const errors = ref([]);

let pollingInterval = null;

const fetchStatus = async () => {
    try {
        const res = await api.get('/automatizacion/status');
        statusData.value = res.data;
        
        // Check if running (Any processing OR pending items)
        const { procesando, pendientes } = res.data.resumen;
        
        if ((procesando > 0 || pendientes > 0) && !manuallyStopped.value) {
            isRunning.value = true;
        } else if (isRunning.value && procesando === 0 && pendientes === 0) {
            // Finished naturally
            isRunning.value = false;
            // Optional: alert("Proceso Terminado");
        } else if (manuallyStopped.value) {
             isRunning.value = false;
        }
    } catch (e) {
        console.error("Error fetching status", e);
    }
};

const fetchErrors = async () => {
     try {
        const res = await api.get('/automatizacion/errors');
        errors.value = res.data;
    } catch (e) {
        console.error("Error fetching errors", e);
    }
}

const runAutomation = async () => {
    isRunning.value = true;
    manuallyStopped.value = false; // Reset flag so we listed to API again
    
    // Calcular dias de diferencia
    const start = new Date(startDate.value);
    const end = new Date(); // Hoy
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
    
    // Asegurar minimo 1 dia
    const finalDaysBack = diffDays < 1 ? 1 : diffDays;

    try {
        await api.post('/automatizacion/run', {
            mode: runMode.value,
            days_back: finalDaysBack,
            show_browser: showBrowser.value
        });
        
        // Iniciar polling fuerte
        fetchStatus();
    } catch (e) {
        alert("Error iniciando: " + e.message);
        isRunning.value = false;
    }
};

const stopAutomation = async () => {
    if(!confirm("¿Seguro que deseas detener el robot? Terminará la empresa actual y parará.")) return;
    try {
        await api.post('/automatizacion/stop');
        alert("🛑 Solicitud enviada. El robot se detendrá pronto.");
    } catch (e) {
        console.error("Error stopping", e);
        alert("Error al intentar detener.");
    }
};

const forceReset = () => {
    if(!confirm("¿Forzar reinicio del estado visual? Esto no detiene el backend, solo resetea el botón.")) return;
    isRunning.value = false;
    manuallyStopped.value = true; // Prevent polling from re-enabling it
};

onMounted(() => {
    // Iniciar ciclo de polling adaptativo
    pollStatus();
});

onUnmounted(() => {
    // Limpiar timeout si existe para evitar memory leaks
    if(pollingTimeout) clearTimeout(pollingTimeout);
});

let pollingTimeout = null;

const pollStatus = async () => {
    await fetchStatus();
    await fetchErrors();
    
    // Polling Adaptativo:
    // Si está corriendo -> Rápido (4s) para feedback visual usuario.
    // Si está idle -> Lento (20s) para no saturar logs y red.
    const delay = isRunning.value ? 4000 : 20000;
    
    pollingTimeout = setTimeout(pollStatus, delay);
};
</script>

<style>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.5); 
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.8); 
  border-radius: 4px;
}
</style>
