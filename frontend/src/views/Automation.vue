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
                
                <!-- Historic Periods -->
                <div class="mt-4">
                    <label class="text-[10px] text-gray-500 uppercase font-bold mb-2 block">Periodos Anteriores</label>
                    <select 
                        v-if="periods.length > 0"
                        @change="(e) => selectPeriod(periods[e.target.value])"
                        class="w-full bg-dark border border-gray-700 text-gray-300 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-primary appearance-none cursor-pointer"
                    >
                        <option value="" disabled selected>Seleccionar periodo historial...</option>
                        <option 
                            v-for="(p, idx) in periods" 
                            :key="idx" 
                            :value="idx"
                        >
                             {{ p.fecha_desde }} ➜ {{ p.fecha_hasta }} ({{ p.ok }} / {{ p.total }} OK)
                        </option>
                    </select>
                    <div v-else class="text-xs text-gray-500 italic px-2">
                        No se encontraron periodos registrados.
                    </div>
                </div>
                
                <div class="flex items-center gap-2 mt-4 text-sm text-gray-400">
                    <span>Desde:</span>
                    <input type="date" v-model="startDate" :max="getToday()" class="bg-dark border border-gray-700 rounded px-2 py-1 text-white text-center" />
                    <span>Hasta:</span>
                    <input type="date" v-model="endDate" :max="getToday()" class="bg-dark border border-gray-700 rounded px-2 py-1 text-white text-center" />
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
                         <span v-else-if="jobStatus === 'STOPPED'">⏯️ REANUDAR EJECUCIÓN</span>
                         <span v-else-if="jobStatus === 'PARTIAL'">🔄 Reintentar Fallidos</span>
                         <span v-else-if="jobStatus === 'ERROR'">⚠️ Reintentar (Error)</span>
                         <span v-else>🚀 INICIAR AUTOMATIZACIÓN</span>
                    </span>
                </button>
                
                <div v-if="['RUNNING', 'PENDING'].includes(jobStatus)" class="flex flex-col items-center gap-2">
                    <p v-if="isStopping" class="text-xs text-red-400 text-center animate-pulse">Solicitando detención del servidor...</p>
                    <p v-else class="text-xs text-green-500 text-center animate-pulse">Proceso Activo: Analizando buzones...</p>
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
                        <span>{{ statusData.resumen.completados }} / {{ statusData.resumen.total_empresas }}</span>
                    </div>
                     <div class="w-full bg-gray-700 rounded-full h-2.5">
                        <div class="bg-primary h-2.5 rounded-full transition-all duration-500" :style="{ width: (statusData.resumen.total_empresas > 0 ? (statusData.resumen.completados / statusData.resumen.total_empresas * 100) : 0) + '%' }"></div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4 pt-2">
                    <div class="text-center p-3 rounded-lg border border-gray-800 bg-gray-800/20">
                        <div class="text-2xl font-bold text-yellow-500">{{ statusData.resumen.pendientes }}</div>
                        <div class="text-xs text-gray-500">Pendientes</div>
                    </div>
                    <div class="text-center p-3 rounded-lg border border-gray-800 bg-gray-800/20">
                        <div class="text-2xl font-bold text-green-500">{{ statusData.resumen.completados }}</div>
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
                            <th class="px-3 py-2 text-center">Evidencia</th>
                            <th class="px-3 py-2 text-right">Fecha</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-dark-border">
                        <tr v-if="runs.length === 0">
                            <td colspan="4" class="p-4 text-center text-gray-500">Sin ejecuciones recientes.</td>
                        </tr>
                        <tr v-for="run in runs" :key="run.id" class="hover:bg-dark-border/30">
                            <td class="px-3 py-2">
                                <div class="font-medium text-gray-200">{{ getCompanyName(run.ruc_empresa) }}</div>
                                <div class="text-[10px] text-gray-500 font-mono flex items-center gap-2">
                                    <span>{{ run.ruc_empresa }}</span>
                                    <span class="text-gray-700">|</span>
                                    <span>{{ run.fecha_desde }} <span class="text-gray-600">➜</span> {{ run.fecha_hasta }}</span>
                                </div>
                            </td>
                            <td class="px-3 py-2">
                                <span v-if="run.status === 'RUNNING'" class="text-blue-400 animate-pulse font-bold">EJECUTANDO...</span>
                                <span v-else-if="run.status === 'PENDING' && run.queued" class="text-purple-400 font-bold">EN COLA</span>
                                <span v-else-if="run.status === 'PENDING'" class="text-gray-500">PENDIENTE</span>
                                <span v-else-if="run.status === 'OK'" class="text-green-500 font-bold">COMPLETADO</span>
                                <span v-else-if="['ERROR', 'PARTIAL'].includes(run.status)" class="text-red-500 font-bold">ERROR</span>
                                <span v-else-if="run.status === 'STOPPED'" class="text-yellow-500 font-bold">DETENIDO</span>
                                <span v-else class="text-gray-400">{{ run.status }}</span>
                            </td>
                            <td class="px-3 py-2 text-center">
                                <button 
                                    v-if="run.evidencia_path" 
                                    @click="openEvidence(run.evidencia_path)" 
                                    class="text-primary hover:text-white text-xs underline font-bold"
                                    title="Ver captura de evidencia"
                                >
                                    Ver
                                </button>
                                <span v-else class="text-gray-600 text-[10px]">-</span>
                            </td>
                            <td class="px-3 py-2 text-right text-gray-500">
                                {{ run.finished_at ? new Date(run.finished_at.replace('Z', '')).toLocaleString() : '-' }}
                            </td>
                        </tr>
                    </tbody>
                </table>
             </div>
        </div>
    </div>

    <!-- Evidence Modal -->
    <div v-if="showEvidenceModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click="closeEvidence">
        <div class="relative max-w-[95vw] max-h-[95vh] flex flex-col items-center" @click.stop>
            <button 
                @click="closeEvidence"
                class="absolute -top-10 right-0 text-white hover:text-red-500 text-2xl font-bold transition-colors"
                title="Cerrar (Esc)"
            >
                ✕
            </button>
            <img 
                :src="currentEvidenceUrl" 
                class="max-w-full max-h-[90vh] rounded-lg shadow-2xl border border-gray-600 object-contain"
                alt="Evidencia" 
            />
            <div class="mt-2 flex gap-4">
                 <a :href="currentEvidenceUrl" download="evidencia.png" class="text-primary text-sm hover:underline">Descargar Imagen</a>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import api from '../apiConfig';

// State
const jobStatus = ref('UNKNOWN'); 
const runs = ref([]);
const companies = ref([]);
const errors = ref([]);
const statusData = ref(null); // Back to ref, populated by API
const isStopping = ref(false);
const periods = ref([]); // New

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

// Actions
const fetchPeriods = async () => {
    try {
        const res = await api.get('/automatizacion/periods');
        console.log("Periods response:", res.data); // Debug
        if (res.data.ok && Array.isArray(res.data.periods)) {
            periods.value = res.data.periods;
        } else {
             console.warn("Invalid periods response:", res.data);
        }
    } catch (e) {
        console.error("Error fetching periods", e);
    }
};

const selectPeriod = (p) => {
    startDate.value = p.fecha_desde;
    endDate.value = p.fecha_hasta;
    fetchRuns(); // Auto refresh
    fetchSummary();
};

// Init Dates
startDate.value = getSevenDaysAgo();
endDate.value = getToday();

const isRunning = computed(() => {
    return runs.value.some(r => ['PENDING', 'RUNNING'].includes(r.status));
});

// Actions
const getCompanyName = (ruc) => companies.value.find(c => c.ruc === ruc)?.razon_social || ruc;
const getEvidenceLink = (path) => path ? `/api/files/download?path=${encodeURIComponent(path)}` : '#';

// Evidence Modal Logic
const showEvidenceModal = ref(false);
const currentEvidenceUrl = ref('');

const openEvidence = (path) => {
    currentEvidenceUrl.value = getEvidenceLink(path);
    showEvidenceModal.value = true;
};

const closeEvidence = () => {
    showEvidenceModal.value = false;
    currentEvidenceUrl.value = '';
};

// Esc Key Listener
const handleKeydown = (e) => {
    if (e.key === 'Escape' && showEvidenceModal.value) closeEvidence();
};

const fetchCompanies = async () => {
    try {
        const res = await api.get('/empresas/');
        companies.value = res.data || [];
    } catch(e) { console.error(e); }
};

const fetchSummary = async () => {
    try {
        // We ask the backend for the global status relative to the date range
        // If the backend doesn't support params, it might just return "Today".
        // But we'll try sending them.
        const params = { 
            fecha_desde: startDate.value,
            fecha_hasta: endDate.value
        };
        const res = await api.get('/automatizacion/status', { params });
        statusData.value = res.data;
    } catch (e) { console.error("Error fetching status summary", e); }
};

const fetchRuns = async () => {
    try {
        const params = { 
            fecha_desde: startDate.value,
            fecha_hasta: endDate.value 
        };
        const res = await api.get('/automatizacion/runs', { params });
        
        let allRuns = [];
        if (Array.isArray(res.data)) {
            allRuns = res.data;
        } else if (res.data && Array.isArray(res.data.runs)) {
            allRuns = res.data.runs;
        } else {
            console.warn("Unexpected response format for runs:", res.data);
        }

        // Strict client-side filtering to ensure UI consistency
        // We show runs that overlap or match the selected range? 
        // User said "filtra los que esten en ese rango".
        // Let's filter runs where the run's start date is >= selected start date
        // AND run's end date <= selected end date.
        // This ensures they are fully contained in the view.
        runs.value = allRuns.filter(r => {
             return r.fecha_desde >= startDate.value && r.fecha_hasta <= endDate.value;
        });


        
        // Determine Global Status
        // Determine Global Status
        if (runs.value.some(r => r.status === 'RUNNING')) {
            jobStatus.value = 'RUNNING';
        } else if (runs.value.some(r => r.status === 'PENDING' && r.queued)) {
            // Only consider it "Active PENDING" (En Cola) if queued is true
            jobStatus.value = 'PENDING';
        } else if (runs.value.some(r => r.status === 'PENDING')) {
             // Pending but NOT queued -> Ready to Start
             jobStatus.value = 'IDLE';
        } else if (runs.value.some(r => r.status === 'ERROR')) {
            jobStatus.value = 'ERROR';
        } else if (runs.value.some(r => r.status === 'PARTIAL')) {
            jobStatus.value = 'PARTIAL';
        } else if (runs.value.some(r => r.status === 'STOPPED')) {
            jobStatus.value = 'STOPPED';
        } else {
            // If everything is OK, or empty
            const allOk = runs.value.length > 0 && runs.value.every(r => r.status === 'OK');
            if (allOk) jobStatus.value = 'OK';
            else jobStatus.value = 'IDLE'; 
        }
        
        if (!['RUNNING', 'PENDING'].includes(jobStatus.value)) {
            isStopping.value = false;
        }

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
        // 'solo_fallidos' logic: Frontend explicitly filters runs from the current view
        // User Requirement: Filter runs with status ERROR, PARTIAL, or STOPPED from current period.
        const targetStatuses = ['ERROR', 'PARTIAL', 'STOPPED'];
        const failedRuns = runs.value.filter(r => targetStatuses.includes(r.status));
        
        if (failedRuns.length > 0) {
            payload.rucs = failedRuns.map(r => r.ruc_empresa);
        } else {
            // Edge case: No failed runs found in current view.
            // Option A: Send empty list (might confuse backend?)
            // Option B: Alert user.
            // Option C: Fallback to all? No, that defeats the purpose.
            alert("No hay ejecuciones con estado ERROR, PARCIAL o DETENIDO en el periodo seleccionado para reintentar.");
            return; // Abort
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
    if(!confirm("¿Detener TODAS las ejecuciones activas?")) return;
    isStopping.value = true;
    try {
        // Global Stop
        await api.post('/automatizacion/stop');
        
        // alert("Solicitud de detención enviada."); // Optional if UI updating
        fetchRuns();
    } catch (e) {
        alert("Error al detener: " + e.message);
        isStopping.value = false;
    }
};

// Lifecycle
let pollingInterval = null;
let isActive = false;

const poll = async () => {
    if (!isActive) return;
    await fetchRuns();
    if (!isActive) return;
    await fetchSummary();
    if (!isActive) return;
    await fetchErrors();
    
    if (!isActive) return;
    const delay = isRunning.value ? 4000 : 10000;
    pollingInterval = setTimeout(poll, delay);
};

onMounted(async () => {
    isActive = true;
    window.addEventListener('keydown', handleKeydown);
    await fetchCompanies();
    await fetchPeriods(); // Load initial
    poll();
});

onUnmounted(() => {
    isActive = false;
    window.removeEventListener('keydown', handleKeydown);
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
