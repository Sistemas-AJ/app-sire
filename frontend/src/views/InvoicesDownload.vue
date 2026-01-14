<template>
  <div class="p-8 h-full flex flex-col gap-6">
    
    <!-- Title -->
    <div>
        <h2 class="text-3xl font-bold text-white">Descarga de XML y Detalles</h2>
        <p class="text-gray-400 text-sm mt-1">Descarga masiva de comprobantes electrónicos (XML) y visualización detallada.</p>
    </div>

    <div class="flex flex-col xl:flex-row gap-8 min-h-0 flex-1">
        
        <!-- Left Panel: Configuration -->
        <div class="w-full xl:w-1/3 flex flex-col gap-6">
            
            <!-- Config Card -->
            <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg">
                <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    📅 Configuración
                </h3>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Periodo (YYYYMM)</label>
                        <input v-model="config.periodo" type="text" placeholder="202501" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-primary focus:outline-none placeholder-gray-600 font-mono" />
                    </div>
                </div>
            </div>

            <!-- Companies Selector -->
            <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg flex-1 flex flex-col min-h-0">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-bold text-white flex items-center gap-2">
                        🏢 Empresas
                        <span class="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full">{{ selectedRucs.length }} / {{ companies.length }}</span>
                    </h3>
                    <button @click="toggleSelectAll" class="text-xs text-primary hover:text-white transition-colors font-medium">
                        {{ allSelected ? 'Deseleccionar' : 'Seleccionar Todo' }}
                    </button>
                </div>

                <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-2">
                    <div v-if="loadingCompanies" class="text-center py-4 text-gray-500 text-xs">Cargando empresas...</div>
                    
                    <label v-for="company in companies" :key="company.ruc" 
                        class="flex items-center p-3 rounded-lg border transition-colors cursor-pointer group"
                        :class="selectedRucs.includes(company.ruc) ? 'bg-primary/10 border-primary/30' : 'bg-dark border-gray-800 hover:border-gray-600'"
                    >
                        <input type="checkbox" :value="company.ruc" v-model="selectedRucs" class="hidden" />
                        
                        <!-- Status Indicator (Just aesthetic or reusing prop active) -->
                        <div class="w-2 h-2 rounded-full mr-3 flex-shrink-0 bg-gray-600"></div>
                        
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-bold text-gray-200 truncate group-hover:text-white transition-colors">{{ company.razon_social }}</p>
                            <p class="text-xs text-gray-500 font-mono">{{ company.ruc }}</p>
                        </div>
                         <div v-if="selectedRucs.includes(company.ruc)" class="text-primary ml-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                            </svg>
                        </div>
                    </label>
                </div>

                <!-- Action Button -->
                <div class="pt-4 mt-4 border-t border-gray-800">
                    <button 
                        @click="runDownload" 
                        :disabled="processing || selectedRucs.length === 0"
                        class="w-full bg-primary hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/20 transition-all flex justify-center items-center gap-2"
                    >
                        <span v-if="processing" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
                        <span v-else>🚀 Iniciar Descarga XML</span>
                    </button>
                    <p v-if="!processing && selectedRucs.length === 0" class="text-center text-[10px] text-red-400 mt-2">Selecciona al menos una empresa</p>
                </div>
            </div>
        </div>

        <!-- Right Panel: Progress & Results -->
        <div class="w-full xl:w-2/3 flex flex-col gap-6 min-h-0">
             
             <!-- Progress Tracking Area -->
             <div v-if="activeDownloads.length > 0" class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg flex-shrink-0">
                <h3 class="text-lg font-bold text-white mb-4">📊 Progreso de Descarga</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[300px] overflow-y-auto custom-scrollbar">
                    <div v-for="progress in progressList" :key="progress.ruc" 
                        @click="viewEvidences(progress.ruc)"
                        class="bg-gray-800/50 border border-gray-700 hover:border-primary/50 p-4 rounded-lg cursor-pointer transition-all relative overflow-hidden group">
                        
                        <!-- Loading shimmer if pending usually -->
                        
                        <div class="flex justify-between items-start mb-2 relative z-10">
                             <div>
                                <h4 class="text-white font-bold text-sm truncate w-48">{{ getCompanyName(progress.ruc) }}</h4>
                                <span class="text-[10px] text-gray-500 font-mono">{{ progress.ruc }}</span>
                            </div>
                            <div class="text-right">
                                <span class="text-lg font-bold text-primary">{{ progress.percentage }}%</span>
                            </div>
                        </div>

                        <!-- Progress Bar -->
                        <div class="w-full bg-gray-700 h-2 rounded-full overflow-hidden mb-3 relative z-10">
                            <div class="bg-primary h-full transition-all duration-500" :style="{ width: progress.percentage + '%' }"></div>
                        </div>

                        <!-- Stats Grid -->
                        <div class="grid grid-cols-4 gap-2 text-center relative z-10">
                            <div class="bg-green-900/20 rounded py-1 px-1 border border-green-900/50">
                                <div class="text-xs font-bold text-green-400">{{ progress.ok }}</div>
                                <div class="text-[8px] text-gray-500 uppercase">OK</div>
                            </div>
                            <div class="bg-red-900/20 rounded py-1 px-1 border border-red-900/50">
                                <div class="text-xs font-bold text-red-400">{{ progress.error + progress.auth }}</div>
                                <div class="text-[8px] text-gray-500 uppercase">Err</div>
                            </div>
                             <div class="bg-yellow-900/20 rounded py-1 px-1 border border-yellow-900/50">
                                <div class="text-xs font-bold text-yellow-400">{{ progress.pending }}</div>
                                <div class="text-[8px] text-gray-500 uppercase">Pend</div>
                            </div>
                            <div class="bg-gray-700/30 rounded py-1 px-1 border border-gray-700">
                                <div class="text-xs font-bold text-gray-400">{{ progress.total_items }}</div>
                                <div class="text-[8px] text-gray-500 uppercase">Total</div>
                            </div>
                        </div>
                        
                        <div class="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
                    </div>
                </div>
             </div>

             <!-- Evidence Explorer -->
             <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg flex-1 flex flex-col min-h-0 relative">
                <div v-if="!currentRuc" class="absolute inset-0 flex flex-col items-center justify-center text-gray-600 z-10 bg-dark-lighter/50 backdrop-blur-sm rounded-xl">
                    <div class="text-4xl mb-4">📂</div>
                    <p>Selecciona una empresa del panel de progreso (o inicia una descarga) para ver los detalles.</p>
                </div>

                <div v-else class="flex flex-col h-full">
                    <div class="flex justify-between items-center mb-4">
                        <div>
                            <h3 class="text-lg font-bold text-white flex items-center gap-2">
                                📂 Evidencias
                                <span class="text-sm font-normal text-gray-400">| {{ getCompanyName(currentRuc) }}</span>
                            </h3>
                            <span class="text-xs text-primary font-mono bg-primary/10 px-2 py-0.5 rounded">{{ currentRuc }} - {{ config.periodo }}</span>
                        </div>
                        <button @click="loadEvidences(currentRuc)" class="p-2 hover:bg-gray-800 rounded-lg text-primary transition-colors" title="Recargar">
                             🔄 Refresh
                        </button>
                    </div>

                    <!-- Filters / Search could go here -->

                    <!-- Table -->
                    <div class="flex-1 overflow-y-auto custom-scrollbar border border-dark-border rounded-lg bg-dark/30">
                        <table class="w-full text-left text-sm text-gray-400">
                            <thead class="bg-dark/80 text-xs uppercase text-gray-500 sticky top-0 backdrop-blur-sm">
                                <tr>
                                    <th class="px-4 py-3 font-semibold">ID</th>
                                    <th class="px-4 py-3 font-semibold">Archivo</th>
                                    <th class="px-4 py-3 font-semibold">Estado</th>
                                    <th class="px-4 py-3 font-semibold">Intentos</th>
                                    <th class="px-4 py-3 font-semibold text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-dark-border">
                                <tr v-if="loadingEvidences" class="animate-pulse">
                                    <td colspan="5" class="px-4 py-8 text-center text-gray-500">Cargando evidencias...</td>
                                </tr>
                                <tr v-for="item in evidences" :key="item.propuesta_item_id" class="hover:bg-dark-border/30 transition-colors">
                                    <td class="px-4 py-3 font-mono text-xs">{{ item.propuesta_item_id }}</td>
                                    <td class="px-4 py-3">
                                        <div class="text-white truncate max-w-[200px]" :title="item.storage_path">{{ getFilename(item.storage_path) }}</div>
                                    </td>
                                    <td class="px-4 py-3">
                                        <span :class="getStatusBadge(item.status)" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border">
                                            {{ item.status }}
                                        </span>
                                    </td>
                                    <td class="px-4 py-3 text-xs">{{ item.attempt_count }}</td>
                                    <td class="px-4 py-3 text-right space-x-2">
                                        <a v-if="item.status === 'OK'" :href="getDownloadLink(item.storage_path)" target="_blank" class="text-green-400 hover:text-green-300 font-bold text-xs underline" title="Descargar XML">
                                            XML
                                        </a>
                                        <button @click="openDetail(item.propuesta_item_id)" class="text-blue-400 hover:text-blue-300 font-bold text-xs underline">
                                            Ver Detalle
                                        </button>
                                    </td>
                                </tr>
                                <tr v-if="!loadingEvidences && evidences.length === 0">
                                    <td colspan="5" class="px-4 py-8 text-center text-gray-600">No hay evidencias registradas para este periodo.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
             </div>
        </div>

    </div>

    <!-- Detail Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="closeModal">
        <div class="bg-dark-lighter w-full max-w-2xl rounded-2xl border border-gray-700 shadow-2xl flex flex-col max-h-[90vh]">
            <div class="p-6 border-b border-gray-700 flex justify-between items-center bg-gray-800/50 rounded-t-2xl">
                <h3 class="text-xl font-bold text-white">📄 Detalle del Comprobante</h3>
                <button @click="closeModal" class="text-gray-400 hover:text-white transition-colors text-2xl leading-none">&times;</button>
            </div>
            
            <div class="flex-1 overflow-y-auto p-6 custom-scrollbar" v-if="detailData">
                
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div class="bg-dark p-3 rounded-lg border border-gray-700">
                        <span class="text-xs text-gray-500 uppercase block mb-1">Fecha Emisión</span>
                        <span class="text-white font-mono">{{ detailData.detalle_json?.issue_date }}</span>
                    </div>
                    <div class="bg-dark p-3 rounded-lg border border-gray-700">
                        <span class="text-xs text-gray-500 uppercase block mb-1">Moneda</span>
                        <span class="text-white font-mono">{{ detailData.detalle_json?.currency }}</span>
                    </div>
                     <div class="bg-green-900/10 p-3 rounded-lg border border-green-900/30">
                        <span class="text-xs text-green-500 uppercase block mb-1">Total a Pagar</span>
                        <span class="text-green-400 font-bold text-lg font-mono">{{ detailData.detalle_json?.totals?.payable_amount }}</span>
                    </div>
                    <div class="bg-blue-900/10 p-3 rounded-lg border border-blue-900/30">
                        <span class="text-xs text-blue-500 uppercase block mb-1">Impuestos (IGV)</span>
                        <span class="text-blue-400 font-bold text-lg font-mono">{{ detailData.detalle_json?.totals?.tax_amount }}</span>
                    </div>
                </div>

                <h4 class="text-sm font-bold text-gray-400 uppercase tracking-widest mb-3 border-b border-gray-700 pb-2">Items / Líneas</h4>
                
                <div class="space-y-2">
                    <div v-for="(line, idx) in detailData.detalle_json?.lines" :key="idx" class="bg-gray-800/30 p-3 rounded border border-gray-800 flex justify-between items-center text-sm">
                        <div class="flex items-center gap-3">
                            <span class="bg-gray-700 text-gray-300 font-mono text-xs px-2 py-0.5 rounded">{{ line.quantity }}</span>
                            <span class="text-gray-300">{{ line.description }}</span>
                        </div>
                        <span class="text-white font-mono font-bold">{{ line.line_total }}</span>
                    </div>
                </div>

                <div class="mt-6 pt-4 border-t border-gray-800 text-xs text-gray-600 font-mono break-all">
                    SHA256: {{ detailData.source_sha256 }}
                </div>

            </div>
            
            <div v-else class="flex-1 flex items-center justify-center p-12">
                 <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import api from '../apiConfig';

// Data
const companies = ref([]);
const loadingCompanies = ref(false);
const processing = ref(false);
const selectedRucs = ref([]);

// Setup Dates
const now = new Date();
const config = ref({
    periodo: `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`
});

// Progress
const activeDownloads = ref([]); // List of RUCs being tracked
const progressList = ref({}); // Map RUC -> Stats Object
let pollingInterval = null;

// Evidences (Current view RUC)
const currentRuc = ref(null);
const evidences = ref([]);
const loadingEvidences = ref(false);

// Detail Modal
const showModal = ref(false);
const detailData = ref(null);

const fetchCompanies = async () => {
    loadingCompanies.value = true;
    try {
        const res = await api.get('/empresas/');
        companies.value = res.data || [];
    } catch (e) { console.error(e); } 
    finally { loadingCompanies.value = false; }
};

const allSelected = computed(() => companies.value.length > 0 && selectedRucs.value.length === companies.value.length);
const toggleSelectAll = () => {
    selectedRucs.value = allSelected.value ? [] : companies.value.map(c => c.ruc);
};

const getCompanyName = (ruc) => {
    const c = companies.value.find(c => c.ruc === ruc);
    return c ? c.razon_social : ruc;
};

// --- Action: Run Download ---
const runDownload = async () => {
    processing.value = true;
    // Activate tracking for these RUCs
    selectedRucs.value.forEach(ruc => {
        if (!activeDownloads.value.includes(ruc)) activeDownloads.value.push(ruc);
    });

    try {
        await api.post('/xml/run', {
            periodo: config.value.periodo,
            rucs: selectedRucs.value,
            limit: null,
            headless: true
        });
        
        // Start polling immediately if not running
        if (!pollingInterval) startPolling();
        
        // Set view to first selected
        if (selectedRucs.value.length > 0) {
            viewEvidences(selectedRucs.value[0]);
        }

    } catch (e) {
        alert("Error iniciando descarga: " + e.message);
    } finally {
        processing.value = false;
    }
};

// --- Polling Progress ---
const startPolling = () => {
    pollingInterval = setInterval(async () => {
        if (activeDownloads.value.length === 0) {
            clearInterval(pollingInterval);
            pollingInterval = null;
            return;
        }

        // Poll each active RUC (concurrency could be improved but simple loop ok for <20 companies)
        // Or specific endpoint for bulk status if existed. Here user specified /xml/progress?ruc=...
        for (const ruc of activeDownloads.value) {
            try {
                const res = await api.get('/xml/progress', { params: { ruc, periodo: config.value.periodo } });
                const data = res.data;
                
                // Calculate percentage
                let pct = 0;
                if (data.total_items > 0) {
                    pct = Math.round(((data.ok + data.error + data.not_found + data.auth) / data.total_items) * 100);
                }
                
                progressList.value[ruc] = { ...data, percentage: pct };

                // If finished? Logic is tricky since it's a stream process.
                // We'll leave them in activeDownloads for now so user can see 100%.
                // Maybe a manual "Clear" later or auto-remove if completed.
                // For now, keep polling to show updates.

            } catch (e) {
                console.error(`Error polling ${ruc}`, e);
            }
        }
    }, 2000); // 2 seconds
};

// --- Evidence Explorer ---
const viewEvidences = (ruc) => {
    currentRuc.value = ruc;
    loadEvidences(ruc);
};

const loadEvidences = async (ruc) => {
    if(!ruc) return;
    loadingEvidences.value = true;
    try {
        const res = await api.get('/xml/evidencias', { params: { ruc, periodo: config.value.periodo }});
        evidences.value = res.data;
    } catch(e) { console.error(e); }
    finally { loadingEvidences.value = false; }
};

const getStatusBadge = (status) => {
    const map = {
        'OK': 'bg-green-900/30 text-green-400 border-green-900',
        'ERROR': 'bg-red-900/30 text-red-500 border-red-900',
        'NOT_FOUND': 'bg-gray-700 text-gray-400 border-gray-500',
        'AUTH': 'bg-orange-900/30 text-orange-400 border-orange-900'
    };
    return map[status] || 'bg-gray-800 text-gray-500';
};

const getFilename = (path) => path ? path.split('/').pop() : 'Desconocido';
const getDownloadLink = (path) => `/api/files/download?path=${encodeURIComponent(path)}`;

// --- Details Modal ---
const openDetail = async (id) => {
    showModal.value = true;
    detailData.value = null; // Clear prev
    try {
        const res = await api.get('/xml/detalle', { params: { item_id: id }});
        detailData.value = res.data;
    } catch (e) {
        alert("Error cargando detalle: " + e.message);
        showModal.value = false;
    }
};

const closeModal = () => showModal.value = false;

onMounted(() => {
    fetchCompanies();
});

onUnmounted(() => {
    if (pollingInterval) clearInterval(pollingInterval);
});

</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent; 
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #475569; 
  border-radius: 4px;
}
</style>
