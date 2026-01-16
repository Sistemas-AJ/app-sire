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
                        <label class="block text-xs font-bold text-gray-500 mb-1 flex justify-between">
                            Periodo (YYYYMM)
                             <button @click="togglePeriodMode" class="text-primary hover:text-white" title="Alternar manual/lista">✏️</button>
                        </label>
                        <select v-if="periodMode === 'select' && availablePeriods.length > 0" v-model="config.periodo" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-primary focus:outline-none font-mono appearance-none">
                            <option v-for="p in availablePeriods" :key="p" :value="p">{{ p }}</option>
                        </select>
                        <input v-else v-model="config.periodo" type="text" placeholder="202501" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-primary focus:outline-none placeholder-gray-600 font-mono" />
                        <p v-if="availabilityMessage" class="text-[10px] text-green-400 mt-1">{{ availabilityMessage }}</p>
                    </div>

                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Límite de Descarga</label>
                        <div class="flex items-center gap-3">
                            <label class="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                                <input type="radio" v-model="config.limitType" value="unlimited" name="limit" class="text-primary focus:ring-primary" />
                                <span>Todo (Sin límite)</span>
                            </label>
                             <label class="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
                                <input type="radio" v-model="config.limitType" value="custom" name="limit" class="text-primary focus:ring-primary" />
                                <span>Límite (Cant.)</span>
                            </label>
                        </div>
                        <input v-if="config.limitType === 'custom'" v-model.number="config.limit" type="number" class="mt-2 w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white text-xs focus:border-primary focus:outline-none" placeholder="Ej. 100" />
                    </div>
                </div>
            </div>

            <!-- Companies Selector -->
            <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg flex-1 flex flex-col min-h-0">
                <div class="flex flex-col gap-2 mb-4">
                    <div class="flex justify-between items-center">
                        <h3 class="text-lg font-bold text-white flex items-center gap-2">
                            🏢 Empresas
                            <span class="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full">{{ selectedRucs.length }} / {{ filteredCompanies.length }}</span>
                        </h3>
                        <button @click="toggleSelectAll" class="text-xs text-primary hover:text-white transition-colors font-medium">
                            {{ allSelected ? 'Deseleccionar' : 'Seleccionar Todo' }}
                        </button>
                    </div>
                     <input v-model="companySearch" type="text" placeholder="Buscar empresa..." class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white text-xs focus:border-primary focus:outline-none placeholder-gray-600" />
                </div>

                <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-2">
                    <div v-if="loadingCompanies" class="text-center py-4 text-gray-500 text-xs">Cargando empresas...</div>
                    <div v-if="!loadingCompanies && filteredCompanies.length === 0" class="text-center py-4 text-gray-500 text-xs text-balance px-4">
                        {{ companySearch ? 'No se encontraron empresas con ese nombre.' : 'No hay empresas aptas (con propuesta) para el periodo seleccionado.' }}
                    </div>
                    
                    <label v-for="company in filteredCompanies" :key="company.ruc" 
                        class="flex items-center p-3 rounded-lg border transition-colors cursor-pointer group"
                        :class="selectedRucs.includes(company.ruc) ? 'bg-primary/10 border-primary/30' : 'bg-dark border-gray-800 hover:border-gray-600'"
                    >
                        <input type="checkbox" :value="company.ruc" v-model="selectedRucs" class="hidden" />
                        
                        <!-- Status Indicator (Just aesthetic or reusing prop active) -->
                        <div class="w-2 h-2 rounded-full mr-3 flex-shrink-0" :class="company.propuesta_activa ? 'bg-green-500' : 'bg-gray-600'"></div>
                        
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
                        :disabled="processing || selectedRucs.length === 0 || ['PENDING', 'RUNNING'].includes(jobStatus)"
                        class="w-full bg-primary hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/20 transition-all flex justify-center items-center gap-2 group"
                    >
                        <span v-if="processing" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
                        
                        <span v-else-if="jobStatus === 'PENDING'">⏳ En Cola (Esperando Worker)...</span>
                        <span v-else-if="jobStatus === 'RUNNING'">🚀 Ejecutando...</span>
                        <span v-else-if="jobStatus === 'STOPPED'">⏯️ Reanudar Descarga</span>
                        <span v-else-if="jobStatus === 'PARTIAL'">🔄 Reintentar Fallidos</span>
                        <span v-else-if="jobStatus === 'ERROR'">⚠️ Reintentar (Error Global)</span>
                        <span v-else>🚀 Iniciar Descarga XML</span>
                    </button>
                    <p v-if="!processing && selectedRucs.length === 0" class="text-center text-[10px] text-red-400 mt-2">Selecciona al menos una empresa</p>
                </div>
            </div>
        </div>

        <!-- Right Panel: Dashboard & Results -->
        <div class="w-full xl:w-2/3 flex flex-col gap-6 min-h-0">
             
             <!-- Wait/Idle State -->
             <div v-if="activeDownloads.length === 0" class="flex-1 bg-dark-lighter rounded-xl border border-gray-800 border-dashed flex flex-col items-center justify-center text-gray-600">
                 <div class="text-5xl mb-4 opacity-50">📡</div>
                 <p class="text-lg font-medium">Esperando iniciar descarga...</p>
                 <p class="text-sm">Selecciona empresas a la izquierda y pulsa Iniciar</p>
             </div>

             <!-- Global Dashboard (Active Run) -->
             <div v-if="activeDownloads.length > 0" class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg flex-shrink-0 animate-fade-in-up">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-lg font-bold text-white flex items-center gap-2">
                             <span v-if="isGlobalRunning" class="relative flex h-3 w-3 mr-1">
                                <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                                <span class="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
                            </span>
                            <span v-else class="text-gray-500">⏹️</span>
                            Progreso Global
                        </h3>
                        <p class="text-xs text-gray-400 mt-1">Empresas Completadas: <span class="text-white font-bold">{{ globalStats.completedCompanies }} / {{ activeDownloads.length }}</span></p>
                    </div>
                    <button v-if="isGlobalRunning" @click="stopAll" class="bg-red-900/30 hover:bg-red-900/50 text-red-400 border border-red-900 px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2">
                        🛑 Detener Todo
                    </button>
                </div>

                <!-- Current Company Banner -->
                <div v-if="currentProcessingCompany" class="bg-blue-900/10 border border-blue-900/30 rounded-lg p-3 mb-4 flex items-center gap-4 animate-pulse-soft">
                    <div class="p-2 bg-blue-900/30 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                        </svg>
                    </div>
                    <div class="flex-1">
                        <p class="text-[10px] text-blue-400 font-bold uppercase tracking-wider">Procesando Actualmente</p>
                        <p class="text-white font-bold truncate">{{ getCompanyName(currentProcessingCompany.ruc) }}</p>
                        <p class="text-xs text-gray-400 mt-0.5">
                            <span class="text-white font-mono">{{ currentProcessingCompany.processedItems }}</span> de {{ currentProcessingCompany.total_items }} items
                             <span class="text-gray-600 mx-1">|</span>
                             <span class="text-green-400">{{ currentProcessingCompany.ok }} OK</span>, 
                             <span class="text-red-400">{{ currentProcessingCompany.error }} ERR</span>,
                             <span class="text-yellow-500">{{ currentProcessingCompany.pending }} Pendientes</span>
                        </p>
                    </div>
                </div>

                <!-- Cards Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[300px] overflow-y-auto custom-scrollbar">
                    <div v-for="ruc in activeDownloads" :key="ruc" 
                        @click="viewEvidences(ruc)"
                        class="bg-gray-800/50 border border-gray-700 hover:border-primary/50 p-4 rounded-lg cursor-pointer transition-all relative overflow-hidden group"
                        :class="{'border-green-500/50 bg-green-900/10': getProgress(ruc).isCompleted}">
                        
                        <div class="flex justify-between items-start mb-2 relative z-10">
                             <div class="min-w-0 pr-2">
                                <h4 class="text-gray-300 font-bold text-xs truncate">{{ getCompanyName(ruc) }}</h4>
                                <span class="text-[10px] text-gray-500 font-mono">{{ ruc }}</span>
                            </div>
                            <!-- Status Badge -->
                            <span v-if="getProgress(ruc).isCompleted" class="text-[10px] bg-green-900/50 text-green-400 px-1.5 py-0.5 rounded border border-green-800 shadow-sm shadow-green-900/20 whitespace-nowrap">COMPLETADO</span>
                            <span v-else class="text-[10px] bg-gray-700 text-gray-400 px-1.5 py-0.5 rounded whitespace-nowrap">{{ getProgress(ruc).percentage }}%</span>
                        </div>

                        <!-- Mini Bar -->
                        <div class="w-full bg-gray-700 h-1.5 rounded-full overflow-hidden mb-2 relative z-10">
                            <div class="bg-primary h-full transition-all duration-500" :style="{ width: getProgress(ruc).percentage + '%' }"></div>
                        </div>

                        <div class="text-[10px] text-gray-500 flex flex-col gap-0.5 relative z-10">
                             <div class="flex justify-between font-mono">
                                 <!-- Counter Logic: Processed / Limit (if custom) else Total -->
                                 <span v-if="config.limitType === 'custom'" class="text-gray-300">
                                     <span class="text-white font-bold">{{ getProgress(ruc).processedItems }}</span> / {{ config.limit }}
                                     <span class="text-gray-600 text-[9px] ml-1">(Total: {{ getProgress(ruc).real_total || getProgress(ruc).total_items }})</span>
                                 </span>
                                 <span v-else>
                                     <span class="text-white font-bold">{{ getProgress(ruc).processedItems }}</span> / {{ getProgress(ruc).total_items }}
                                 </span>
                             </div>
                             
                             <div class="flex justify-end space-x-2">
                                 <span v-if="getProgress(ruc).ok > 0" class="text-green-500">{{ getProgress(ruc).ok }} OK</span>
                                 <span v-if="getProgress(ruc).error > 0" class="text-red-500">{{ getProgress(ruc).error }} ERR</span>
                             </div>
                        </div>
                    </div>
                </div>
             </div>

             <!-- Evidence Explorer -->
             <div v-if="activeDownloads.length > 0" class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg flex-1 flex flex-col min-h-0 relative animate-fade-in-up delay-100">
                <div v-if="!currentRuc" class="absolute inset-0 flex flex-col items-center justify-center text-gray-600 z-10 bg-dark-lighter/50 backdrop-blur-sm rounded-xl">
                    <div class="text-4xl mb-4">📂</div>
                    <p>Selecciona una empresa para ver los detalles.</p>
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
                        <div class="flex gap-2">
                            <button @click="downloadReport" :disabled="isDownloadingReport" class="flex items-center gap-1 p-2 hover:bg-gray-800 rounded-lg text-green-400 transition-colors border border-transparent hover:border-gray-700" title="Descargar Reporte Excel">
                                <span v-if="isDownloadingReport" class="animate-spin h-3 w-3 border-2 border-green-500 border-t-transparent rounded-full"></span>
                                <span v-else>📊</span>
                                <span class="text-xs font-bold">Excel</span>
                            </button>
                            <button @click="loadEvidences(currentRuc)" class="p-2 hover:bg-gray-800 rounded-lg text-primary transition-colors border border-transparent hover:border-gray-700" title="Recargar">
                                 🔄 Refresh
                            </button>
                        </div>
                    </div>

                    <div class="flex-1 overflow-y-auto custom-scrollbar border border-dark-border rounded-lg bg-dark/30">
                        <table class="w-full text-left text-sm text-gray-400">
                            <thead class="bg-dark/80 text-xs uppercase text-gray-500 sticky top-0 backdrop-blur-sm">
                                <tr>
                                    <th class="px-4 py-3 font-semibold">ID</th>
                                    <th class="px-4 py-3 font-semibold">Archivo</th>
                                    <th class="px-4 py-3 font-semibold">Estado</th>
                                    <th class="px-4 py-3 font-semibold text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-dark-border">
                                <tr v-for="(item, index) in evidences" :key="item.propuesta_item_id" class="hover:bg-dark-border/30 transition-colors">
                                    <td class="px-4 py-3 font-mono text-xs">{{ index + 1 }}</td>
                                    <td class="px-4 py-3"><div class="text-white truncate max-w-[200px]" :title="item.storage_path">{{ getFilename(item.storage_path) }}</div></td>
                                    <td class="px-4 py-3"><span :class="getStatusBadge(item.status)" class="px-2 py-0.5 rounded text-[10px] font-bold uppercase border">{{ item.status }}</span></td>
                                    <td class="px-4 py-3 text-right space-x-2">
                                        <a v-if="item.status === 'OK'" :href="getDownloadLink(item.storage_path)" target="_blank" class="text-green-400 hover:text-green-300 font-bold text-xs underline">XML</a>
                                        <a v-if="item.status === 'OK'" :href="getDownloadLink(item.storage_path.replace('/xml/', '/pdf/').replace('.xml', '.pdf'))" target="_blank" class="text-red-400 hover:text-red-300 font-bold text-xs underline">PDF</a>
                                        <button @click="openDetail(item.propuesta_item_id)" class="text-blue-400 hover:text-blue-300 font-bold text-xs underline">Ver Detalle</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
             </div>
        </div>
    </div>

    <!-- Modal -->
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
                <!-- Lines -->
                <div class="space-y-2">
                    <div v-for="(line, idx) in detailData.detalle_json?.lines" :key="idx" class="bg-gray-800/30 p-3 rounded border border-gray-800 flex justify-between items-center text-sm">
                        <div class="flex items-center gap-3">
                            <span class="bg-gray-700 text-gray-300 font-mono text-xs px-2 py-0.5 rounded">{{ line.quantity }}</span>
                            <span class="text-gray-300">{{ line.description }}</span>
                        </div>
                        <span class="text-white font-mono font-bold">{{ line.line_total }}</span>
                    </div>
                </div>
                <!-- Debug SHA -->
                 <div class="mt-6 pt-4 border-t border-gray-800 text-xs text-gray-600 font-mono break-all">
                    SHA256: {{ detailData.source_sha256 }}
                </div>
            </div>
            <div v-else class="flex-1 flex items-center justify-center p-12"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div></div>
        </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import api from '../apiConfig';

const companies = ref([]);
const loadingCompanies = ref(false);
const processing = ref(false);
const selectedRucs = ref([]);

// Availability Data
const availablePeriods = ref([]);
const periodMode = ref('select'); // select | manual
const availableRucs = ref([]);
const availabilityMessage = ref('');
const companySearch = ref('');
const jobStatus = ref('UNKNOWN'); // PENDING, RUNNING, PARTIAL, ERROR, OK, STOPPED

const togglePeriodMode = () => {
    periodMode.value = periodMode.value === 'select' ? 'manual' : 'select';
};

const now = new Date();
const config = ref({
    periodo: '', // Will default to latest available
    limitType: 'unlimited',
    limit: 100
});
// ... 
// (lines 375-380)

const filteredCompanies = computed(() => {
    let list = companies.value;
    
    // 1. Availability Filter (if period set)
    if (config.value.periodo) {
        list = list.filter(c => availableRucs.value.includes(c.ruc)); // Only available
    } else {
        return []; // No period, no list
    }
    
    // 2. Search Filter
    if (companySearch.value) {
        const term = companySearch.value.toLowerCase();
        list = list.filter(c => c.razon_social.toLowerCase().includes(term) || c.ruc.includes(term));
    }
    
    return list;
});

// Progress Tracking
const activeDownloads = ref([]); 
const progressList = ref({}); 
let pollingInterval = null;

// Evidence Explorer
const currentRuc = ref(null);
const evidences = ref([]);
const loadingEvidences = ref(false);
// Modal
const showModal = ref(false);
const detailData = ref(null);

// Persistence Constants
const STORAGE_KEY = 'xml_download_state';

// --- Computed Stats ---
const getProgress = (ruc) => progressList.value[ruc] || { percentage: 0, processedItems: 0, total_items: 0, ok: 0, error: 0, isCompleted: false };

const globalStats = computed(() => {
    // Client-side fallback if backend global unsupported, but we will try to use backend data if available logic allows
    const list = activeDownloads.value.map(ruc => getProgress(ruc));
    const completedCompanies = list.filter(p => p.isCompleted).length;
    return { completedCompanies };
});

const isGlobalRunning = computed(() => ['PENDING', 'RUNNING'].includes(jobStatus.value));

const currentProcessingCompany = computed(() => {
    // If backend running, show the one that is not completed locally?
    // Or check backend progress data 'status' field?
    const ruc = activeDownloads.value.find(r => !getProgress(r).isCompleted);
    if (!ruc) return null;
    return { ruc, ...getProgress(ruc) };
});

// --- Methods ---

const SESSION_KEY = 'xml_active_session';

const saveSession = () => {
    // Only save if there are active downloads
    if (activeDownloads.value.length > 0) {
        const state = {
            activeDownloads: activeDownloads.value,
            periodo: config.value.periodo,
            limit: config.value.limit,
            limitType: config.value.limitType,
            timestamp: Date.now()
        };
        localStorage.setItem(SESSION_KEY, JSON.stringify(state));
    } else {
        localStorage.removeItem(SESSION_KEY);
    }
};

const recoverSession = () => {
    try {
        const stored = localStorage.getItem(SESSION_KEY);
        if (stored) {
            const state = JSON.parse(stored);
            // Valid for 24h
            if (Date.now() - state.timestamp < 24 * 60 * 60 * 1000) {
                if (state.activeDownloads && state.activeDownloads.length > 0) {
                    console.log("Recovering active session...");
                    activeDownloads.value = state.activeDownloads;
                    if(state.periodo) config.value.periodo = state.periodo;
                    if(state.limit) config.value.limit = state.limit;
                    if(state.limitType) config.value.limitType = state.limitType;
                    
                    startPolling();
                    // Auto-view first if running
                    if(!currentRuc.value && activeDownloads.value.length > 0) {
                         viewEvidences(activeDownloads.value[0]);
                    }
                }
            } else {
                localStorage.removeItem(SESSION_KEY);
            }
        }
    } catch (e) { console.error(e); }
};

const fetchCompanies = async () => {
    loadingCompanies.value = true;
    try {
        const res = await api.get('/empresas/');
        companies.value = res.data || [];
    } catch (e) { console.error(e); } 
    finally { loadingCompanies.value = false; }
};

const fetchPeriods = async () => {
    try {
        const res = await api.get('/propuesta/periods');
        availablePeriods.value = res.data || [];
        // Default to first if config.periodo is empty
        if (availablePeriods.value.length > 0 && !config.value.periodo) {
            config.value.periodo = availablePeriods.value[0];
        }
    } catch (e) {
        console.error("Error fetching periods", e);
        // Fallback default
        if (!config.value.periodo) config.value.periodo = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`;
    }
};

const fetchAvailability = async () => {
    if (!config.value.periodo) return;
    try {
        const res = await api.get('/propuesta/availability', { params: { periodo: config.value.periodo }});
        availableRucs.value = res.data.available_rucs || [];
        availabilityMessage.value = res.data.message || '';
    } catch (e) {
        console.error("Error fetching availability", e);
        availableRucs.value = [];
        availabilityMessage.value = '';
    }
};

// Update availability when period changes
watch(() => config.value.periodo, fetchAvailability);



const allSelected = computed(() => filteredCompanies.value.length > 0 && selectedRucs.value.length === filteredCompanies.value.length);
const toggleSelectAll = () => selectedRucs.value = allSelected.value ? [] : filteredCompanies.value.map(c => c.ruc);
const getCompanyName = (ruc) => companies.value.find(c => c.ruc === ruc)?.razon_social || ruc;
const getStatusBadge = (status) => ({ 'OK': 'bg-green-900/30 text-green-400 border-green-900', 'ERROR': 'bg-red-900/30 text-red-500 border-red-900' }[status] || 'bg-gray-700 text-gray-400');
const getFilename = (path) => path ? path.split('/').pop() : 'Desconocido';
const getDownloadLink = (path) => `/api/files/download?path=${encodeURIComponent(path)}`;

const runDownload = async () => {
    processing.value = true;
    
    selectedRucs.value.forEach(ruc => { if (!activeDownloads.value.includes(ruc)) activeDownloads.value.push(ruc); });

    // Immediate Feedback: Show details for first selected company
    if (selectedRucs.value.length > 0 && !currentRuc.value) {
        viewEvidences(selectedRucs.value[0]);
    }

    // Save Session (active downloads only)
    saveSession();

    const finalLimit = config.value.limitType === 'custom' ? config.value.limit : null;
    const payload = {
        periodo: config.value.periodo,
        rucs: selectedRucs.value,
        limit: finalLimit,
        headless: true
    };

    try {
        await api.post('/xml/run', payload, { timeout: 120000 });
        // alert(`Descarga Iniciada.`); // Reduced noise
    } catch (e) {
        if (e.code !== 'ECONNABORTED' && (!e.response || e.response.status !== 504)) {
             alert("Error al iniciar: " + (e.response?.data?.detail || e.message));
        }
    } finally {
        processing.value = false;
        if (!pollingInterval) startPolling();
    }
};

const startPolling = () => {
    if (pollingInterval) return;
    
    // Immediate poll check
    const pollFn = async () => {
        try {
            // Source of Truth: Get ALL runs
            const runRes = await api.get('/xml/runs');
            const data = runRes.data || [];
            
            // If response is strict empty array, clear everything
            if (Array.isArray(data)) {
                 // Filter by Current Period & Deduplicate
                 const currentPeriod = config.value.periodo; // String usually
                 
                 // Normalize comparisons (ensure both string or both int if needed, but safe to assume string matches)
                 // Also handle runs that might not have 'periodo' if schema is loose (strict check preference)
                 const periodRuns = data.filter(r => String(r.periodo) === String(currentPeriod));
                 
                 const backendRucs = [...new Set(periodRuns.map(r => r.ruc_empresa))];
                 
                 // Sync activeDownloads
                 activeDownloads.value = backendRucs;

                 // Determine Global Status (Based on filtered period runs?)
                 // Actually, if we filter runs, we calculate status based on what we see.
                 // But the 'jobStatus' might be global for the worker. 
                 // User wants visual consistency: "If I see 2/2 done, it's done".
                 // So we calculate status from 'periodRuns'.

                 if (periodRuns.some(r => r.status === 'RUNNING')) jobStatus.value = 'RUNNING';
                 else if (periodRuns.some(r => r.status === 'PENDING')) jobStatus.value = 'PENDING';
                 else if (periodRuns.some(r => r.status === 'ERROR')) jobStatus.value = 'ERROR';
                 else if (periodRuns.some(r => r.status === 'PARTIAL')) jobStatus.value = 'PARTIAL';
                 else if (periodRuns.length > 0 && periodRuns.every(r => ['OK', 'STOPPED'].includes(r.status))) jobStatus.value = 'OK'; 
                 else jobStatus.value = 'STOPPED';

                 const anyRunning = periodRuns.some(r => ['RUNNING', 'PENDING'].includes(r.status));
                 if (!anyRunning && periodRuns.some(r => r.status === 'STOPPED')) jobStatus.value = 'STOPPED';
                 
                 if (periodRuns.length === 0) jobStatus.value = 'UNKNOWN';

                 // Intelligent Completion Override:
                 // If we have active downloads, and ALL of them are marked as completed locally (via progress poll),
                 // we force visual status to OK to hide the Stop button faster.
                 if (activeDownloads.value.length > 0) {
                     const allCompletedLocally = activeDownloads.value.every(ruc => progressList.value[ruc]?.isCompleted);
                     if (allCompletedLocally) {
                         jobStatus.value = 'OK';
                     }
                 }

            } else {
                 console.warn("Unexpected runs format", data);
                 // Fallback? Or clear?
                 activeDownloads.value = [];
            }

        } catch(e) { console.error("Error checking runs", e); }

        // Poll Progress for individual companies (Only what's in activeDownloads)
        // We still fetch detailed progress because runs might not have 'total_items' or real-time 'remaining' in the main list yet
        for (const ruc of activeDownloads.value) {
            try {
                const res = await api.get('/xml/progress', { params: { ruc, periodo: config.value.periodo } });
                const data = res.data;
                const processed = data.ok + data.not_found + data.error + data.auth;
                
                const limit = config.value.limitType === 'custom' ? config.value.limit : Infinity;
                const effectiveTotal = (data.total_items > 0 && limit < data.total_items) ? limit : data.total_items;

                const isCompleted = (data.remaining === 0 && data.total_items > 0) || (processed >= effectiveTotal && effectiveTotal > 0) || (data.status === 'COMPLETED');
                
                let pct = 0;
                if (effectiveTotal > 0) pct = Math.round((processed / effectiveTotal) * 100);
                if (pct > 100) pct = 100;

                progressList.value[ruc] = {
                    ...data,
                    processedItems: processed,
                    total_items: effectiveTotal,
                    real_total: data.total_items,
                    percentage: pct,
                    isCompleted
                };
            } catch (e) { 
                console.error(`Poll error ${ruc}`, e); 
            }
        }
        
        saveSession(); 
    };

    pollFn(); // First run
    pollingInterval = setInterval(pollFn, 4000); // 4s polling
};

const stopAll = async () => {
    if(!confirm("¿Detener todas las descargas?")) return;
    try {
        await api.post('/xml/stop', { });
        activeDownloads.value = []; // Clear frontend active tracking
        saveSession(); // Updates storage (clears it)
        alert("Orden de detención enviada.");
    } catch(e) { alert("Error: " + e.message); }
};

const viewEvidences = (ruc) => { currentRuc.value = ruc; loadEvidences(ruc); };
const loadEvidences = async (ruc) => {
    if(!ruc) return;
    loadingEvidences.value = true;
    try {
        const res = await api.get('/xml/evidencias', { params: { ruc, periodo: config.value.periodo }});
        evidences.value = res.data;
    } catch(e) { console.error(e); } finally { loadingEvidences.value = false; }
};

// Report Export
const isDownloadingReport = ref(false);
const downloadReport = async () => {
    if(!currentRuc.value) return;
    isDownloadingReport.value = true;
    try {
        const res = await api.get('/xml/report/export', { 
            params: { ruc: currentRuc.value, periodo: config.value.periodo } 
        });
        
        if (res.data.path) {
            // Use existing helper or direct window open
            const url = getDownloadLink(res.data.path);
            window.open(url, '_blank');
            // Optional: alert(res.data.message); 
        } else {
            alert("No se pudo generar el reporte.");
        }
    } catch(e) {
        console.error(e);
        alert("Error al exportar: " + (e.response?.data?.detail || e.message));
    } finally {
        isDownloadingReport.value = false;
    }
};

const openDetail = async (id) => {
    showModal.value = true; detailData.value = null;
    try { 
        const res = await api.get('/xml/detalle', { params: { item_id: id }}); 
        detailData.value = res.data; 
    }
    catch (e) { 
        if (e.response && e.response.status === 404) {
             alert("El detalle no está disponible aún. Es posible que el XML no se haya descargado correctamente o esté pendiente de procesamiento.");
        } else {
             alert("Error cargando detalle: " + e.message); 
        }
        showModal.value = false; 
    }
};
const closeModal = () => showModal.value = false;

onMounted(async () => {
    await fetchCompanies(); 
    await fetchPeriods(); 
    await fetchPeriods(); 
    recoverSession();
});
onUnmounted(() => { if (pollingInterval) clearInterval(pollingInterval); });
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up { animation: fade-in-up 0.5s ease-out; }

.animate-pulse-soft { animation: pulse-soft 2s infinite; }
@keyframes pulse-soft {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}
</style>
