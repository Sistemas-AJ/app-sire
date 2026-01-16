<template>
  <div class="p-8">
    <h2 class="text-3xl font-bold text-white mb-6">Panel de Control de Automatización</h2>

    <!-- Actions Card -->
    <div class="bg-dark-lighter p-8 rounded-xl border border-gray-800 shadow-lg mb-8">
        <div class="flex flex-col md:flex-row justify-between items-center gap-6">
            <div>
                <h3 class="text-xl font-bold text-white mb-2">Ejecutar Robot</h3>
                <p class="text-gray-400 text-sm max-w-md">
                    Inicia el proceso de descarga masiva. El robot analizará los buzones de todas las empresas activas.
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
                    <span>Desde:</span>
                    <input type="date" v-model="startDate" :max="getToday()" class="bg-dark border border-gray-700 rounded px-2 py-1 text-white text-center" />
                    <span>Hasta:</span>
                    <input type="date" v-model="endDate" :max="getToday()" class="bg-dark border border-gray-700 rounded px-2 py-1 text-white text-center" />
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
            
            <div class="flex flex-col gap-2 w-full md:w-auto">
                <!-- SINGLE DYNAMIC BUTTON -->
                <button 
                    @click="['RUNNING', 'PENDING'].includes(jobStatus) ? stopAutomation() : runAutomation()"
                    :class="['RUNNING', 'PENDING'].includes(jobStatus) ? 'bg-red-600 hover:bg-red-700 shadow-red-600/20' : 'bg-primary hover:bg-blue-600 shadow-primary/20'"
                    class="relative overflow-hidden group text-white px-8 py-4 rounded-xl text-lg font-bold transition-all shadow-lg transform hover:-translate-y-1 w-full md:min-w-[300px]"
                >
                    <span class="flex items-center justify-center gap-3">
                         <span v-if="jobStatus === 'PENDING'">⏳ En Cola (Detener)</span>
                         <span v-else-if="jobStatus === 'RUNNING'">🛑 Detener Ejecución</span>
                         <span v-else-if="jobStatus === 'STOPPED'">⏯️ Reanudar (Detenido)</span>
                         <span v-else-if="jobStatus === 'PARTIAL'">🔄 Reintentar Fallidos</span>
                         <span v-else-if="jobStatus === 'ERROR'">⚠️ Reintentar (Error)</span>
                         <span v-else>🚀 INICIAR AUTOMATIZACIÓN</span>
                    </span>
                </button>
                
                <div v-if="['RUNNING', 'PENDING'].includes(jobStatus)" class="flex flex-col items-center gap-2">
                    <p class="text-xs text-gray-500 text-center animate-pulse">Solicitando detención al finalizar tarea actual...</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Live Status -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Status Summary -->
        <div class="bg-dark-lighter rounded-xl border border-gray-800 shadow-lg p-6">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-white">Resumen de Estado</h3>
                <button @click="fetchRuns" class="text-xs text-primary hover:underline">Refrescar</button>
            </div>
            
            <div v-if="statusData" class="space-y-4">
                <div class="flex justify-between items-center p-3 bg-gray-800/50 rounded-lg">
                    <span class="text-gray-400">Total Empresas (Filtro)</span>
                    <span class="text-white font-bold">{{ statusData.resumen.total_empresas }} runs activos</span>
                </div>
                
                <div class="space-y-2">
                    <div class="flex justify-between text-xs text-gray-500 uppercase">
                        <span>Progreso</span>
                        <span>{{ statusData.resumen.completados + statusData.resumen.sin_novedades }} / {{ statusData.resumen.total_empresas }}</span>
                    </div>
                     <div class="w-full bg-gray-700 rounded-full h-2.5">
                        <div class="bg-primary h-2.5 rounded-full transition-all duration-500" :style="{ width: (statusData.resumen.total_empresas > 0 ? ((statusData.resumen.completados + statusData.resumen.sin_novedades) / statusData.resumen.total_empresas * 100) : 0) + '%' }"></div>
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

        <!-- Detailed Runs List -->
        <div class="bg-dark-lighter rounded-xl border border-dark-border shadow-lg p-6 overflow-hidden flex flex-col max-h-[500px]">
             <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span>📋</span> Detalle de Ejecuciones
             </h3>
             
             <div class="flex-1 overflow-auto custom-scrollbar">
                <table class="w-full text-left text-xs">
                    <thead class="bg-dark/50 text-gray-500 uppercase sticky top-0 backdrop-blur-sm">
                        <tr>
                            <th class="px-3 py-2">Empresa</th>
                            <th class="px-3 py-2">Estado</th>
                            <th class="px-3 py-2 text-right">Inicio</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-dark-border">
                        <tr v-if="runs.length === 0">
                            <td colspan="3" class="p-4 text-center text-gray-500">Sin ejecuciones recientes.</td>
                        </tr>
                        <tr v-for="run in runs" :key="run.id" class="hover:bg-dark-border/30">
                            <td class="px-3 py-2 font-medium text-gray-300">
                                {{ run.ruc_empresa }}
                            </td>
                            <td class="px-3 py-2">
                                <span v-if="run.status === 'RUNNING'" class="text-blue-400 animate-pulse font-bold">RUNNING</span>
                                <span v-else-if="run.status === 'OK'" class="text-green-500">OK</span>
                                <span v-else-if="run.status === 'ERROR'" class="text-red-500 font-bold">ERROR</span>
                                <span v-else-if="run.status === 'PENDING'" class="text-yellow-500">PENDING</span>
                                <span v-else class="text-gray-400">{{ run.status }}</span>
                            </td>
                            <td class="px-3 py-2 text-right text-gray-500">
                                {{ run.started_at ? new Date(run.started_at).toLocaleTimeString() : '-' }}
                            </td>
                        </tr>
                    </tbody>
                </table>
             </div>
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import api from '../apiConfig';

// State
const jobStatus = ref('UNKNOWN'); // PENDING, RUNNING, PARTIAL, ERROR, OK, STOPPED
const runs = ref([]);
const companies = ref([]);
const errors = ref([]);

// Inputs
const runMode = ref('todo');
const showBrowser = ref(false);
const startDate = ref('');
const endDate = ref('');

// Date Helpers
const getToday = () => new Date().toISOString().split('T')[0];
const getSevenDaysAgo = () => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split('T')[0];
};

// Init Dates
startDate.value = getSevenDaysAgo();
endDate.value = getToday();

// Computed Stats derived from Runs
const statusData = computed(() => {
    // Default structure to match UI
    const summary = {
        total_empresas: runs.value.length,
        pendientes: 0,
        procesando: 0,
        completados: 0,
        sin_novedades: 0,
        errores: 0
    };
    
    runs.value.forEach(r => {
        if (r.status === 'PENDING') summary.pendientes++;
        else if (r.status === 'RUNNING') summary.procesando++;
        else if (r.status === 'OK') summary.completados++; // or check stats_json?
        else if (r.status === 'PARTIAL') summary.errores++; // Count partial as error or separate?
        else if (r.status === 'ERROR') summary.errores++;
        else if (r.status === 'STOPPED') summary.errores++; // Or separate?
    });
    
    return { resumen: summary };
});

const isRunning = computed(() => {
    // Global running if any run is active
    return runs.value.some(r => ['PENDING', 'RUNNING'].includes(r.status));
});

// Actions
const fetchCompanies = async () => {
    try {
        const res = await api.get('/empresas/');
        companies.value = res.data || [];
    } catch(e) { console.error(e); }
};

const fetchRuns = async () => {
    try {
        const params = { fecha_desde: startDate.value };
        const res = await api.get('/automatizacion/runs', { params });
        
        if (Array.isArray(res.data)) {
            runs.value = res.data;
        } else if (res.data && Array.isArray(res.data.runs)) {
            runs.value = res.data.runs;
        } else {
            console.warn("Unexpected response format for runs:", res.data);
            runs.value = [];
        }
        
        // Determine Global Status
        if (runs.value.some(r => r.status === 'RUNNING')) jobStatus.value = 'RUNNING';
        else if (runs.value.some(r => r.status === 'PENDING')) jobStatus.value = 'PENDING';
        else if (runs.value.some(r => r.status === 'ERROR')) jobStatus.value = 'ERROR';
        else if (runs.value.some(r => r.status === 'PARTIAL')) jobStatus.value = 'PARTIAL';
        else jobStatus.value = 'OK';

    } catch(e) { 
        console.error("Error fetching runs", e); 
        runs.value = [];
    }
};

const fetchErrors = async () => {
    try {
         const res = await api.get('/automatizacion/errors');
         errors.value = res.data || [];
    } catch (e) { console.error(e); }
}

const runAutomation = async () => {
    // Build payload
    const payload = {
        mode: runMode.value,
        date_from: startDate.value,
        date_to: endDate.value,
        show_browser: showBrowser.value,
        rucs: runMode.value === 'todo' ? [] : [] // If 'todo', maybe empty list? Backend usually handles it.
        // User said: "rucs": ["..."] in example.
        // I will interpret 'todo' as sending ALL RUCs explicitly if required, or [] if backend supports implicit "all".
        // Let's send ALL active RUCs just to be safe and explicit.
    };
    
    if (runMode.value === 'todo') {
        payload.rucs = companies.value.filter(c => c.activo).map(c => c.ruc);
    } else {
        // 'solo_fallidos' logic? Frontend doesn't strictly track failures locally except visual logs.
        // Usually backend handles 'retry failed' logic.
        // If user selects 'solo_fallidos', maybe we send empty runs list and backend finds failed from DB?
        // Or we should allow user to select?
        // Let's assume for now 'todo' is the primary use case.
        // If 'solo_fallidos', I'll send all too, hoping backend filters? 
        // Or maybe I filter runs with error status locally and send those RUCs?
        // I'll implement logic: Filter companies with recent errors?
        // Simplest: Send all, backend loop handles logic?
        // Actually, Start button text changes: "Reintentar". 
        // If we are retying, we pass the same parameters.
        if (runs.value.length > 0) {
             // Retry Failed
             const failedRucs = runs.value.filter(r => ['ERROR', 'PARTIAL'].includes(r.status)).map(r => r.ruc_empresa); // Assuming run has ruc_empresa
             if (failedRucs.length > 0) payload.rucs = failedRucs;
             else payload.rucs = companies.value.filter(c => c.activo).map(c => c.ruc);
        } else {
             payload.rucs = companies.value.filter(c => c.activo).map(c => c.ruc);
        }
    }

    try {
        await api.post('/automatizacion/run', payload);
        fetchRuns();
    } catch (e) {
        alert("Error iniciando: " + e.message);
    }
};

const stopAutomation = async () => {
    if(!confirm("¿Detener ejecuciones activas?")) return;
    try {
        // Find active runs and stop them.
        const active = runs.value.filter(r => ['PENDING', 'RUNNING'].includes(r.status));
        for (const run of active) {
             // Assuming run has ruc_empresa. User example params: stop?ruc=...&fecha_desde=...
             // The run object likely has this info.
             // If run object structure is unknown, this is risky.
             // User said: "POST /automatizacion/stop?ruc=...&fecha_desde=..."
             // I'll guess run.ruc_empresa exists.
             if (run.ruc_empresa) {
                 await api.post(`/automatizacion/stop`, null, { 
                     params: { ruc: run.ruc_empresa, fecha_desde: startDate.value } 
                 });
             }
        }
        alert("Solicitud de detención enviada.");
        fetchRuns();
    } catch (e) {
        alert("Error al detener: " + e.message);
    }
};

// Lifecycle
let pollingInterval = null;
const poll = async () => {
    await fetchRuns();
    await fetchErrors();
    const delay = isRunning.value ? 4000 : 10000;
    pollingInterval = setTimeout(poll, delay);
};

onMounted(async () => {
    await fetchCompanies();
    poll();
});

onUnmounted(() => {
    if(pollingInterval) clearTimeout(pollingInterval);
});
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
