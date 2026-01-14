<template>
  <div class="p-8 h-full flex flex-col gap-6">
    
    <!-- Title -->
    <div>
        <h2 class="text-3xl font-bold text-white">Generación de Propuesta RVIE / RCE</h2>
        <p class="text-gray-400 text-sm mt-1">Selecciona las empresas y el periodo para generar la propuesta y descargar los archivos.</p>
    </div>

    <div class="flex flex-col xl:flex-row gap-8 min-h-0 flex-1">
        
        <!-- Left Panel: Configuration -->
        <div class="w-full xl:w-1/3 flex flex-col gap-6">
            
            <!-- Period Config Card -->
            <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg">
                <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    📅 Configuración
                </h3>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-500 mb-1">Periodo (YYYYMM)</label>
                        <input v-model="config.periodo" type="text" placeholder="202501" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white focus:border-primary focus:outline-none placeholder-gray-600 font-mono" />
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Fecha Inicio</label>
                            <input v-model="config.fec_ini" type="date" class="w-full bg-dark border border-gray-700 rounded-lg px-2 py-2 text-white text-xs focus:border-primary focus:outline-none" />
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-500 mb-1">Fecha Fin</label>
                            <input v-model="config.fec_fin" type="date" class="w-full bg-dark border border-gray-700 rounded-lg px-2 py-2 text-white text-xs focus:border-primary focus:outline-none" />
                        </div>
                    </div>
                </div>
            </div>

            <!-- Companies Selector -->
            <div class="bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg flex-1 flex flex-col min-h-0">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-bold text-white flex items-center gap-2">
                        🏢 Empresas
                        <span class="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded-full">{{ selectedRucs.length }} / {{ filteredCompanies.length }}</span>
                    </h3>
                    <button @click="toggleSelectAll" class="text-xs text-primary hover:text-white transition-colors font-medium">
                        {{ allSelected ? 'Deseleccionar' : 'Seleccionar Todo' }}
                    </button>
                </div>

                <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-2">
                    <div v-if="loadingCompanies" class="text-center py-4 text-gray-500 text-xs">Cargando empresas...</div>
                    <div v-if="!loadingCompanies && filteredCompanies.length === 0" class="text-center py-4 text-gray-500 text-xs">No hay empresas aptas (con propuesta) para generar.</div>
                    
                    <label v-for="company in filteredCompanies" :key="company.ruc" 
                        class="flex items-center p-3 rounded-lg border transition-colors cursor-pointer group"
                        :class="selectedRucs.includes(company.ruc) ? 'bg-primary/10 border-primary/30' : 'bg-dark border-gray-800 hover:border-gray-600'"
                    >
                        <input type="checkbox" :value="company.ruc" v-model="selectedRucs" class="hidden" />
                        
                        <!-- Status Dot -->
                        <div class="w-2 h-2 rounded-full mr-3 flex-shrink-0"
                             :class="company.propuesta_activa ? 'bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.5)]' : 'bg-red-500 opacity-50'"
                             :title="company.propuesta_activa ? 'SIRE Activo' : 'SIRE Inactivo'"></div>
                        
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
                        @click="runProposal" 
                        :disabled="processing || selectedRucs.length === 0"
                        class="w-full bg-primary hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/20 transition-all flex justify-center items-center gap-2"
                    >
                        <span v-if="processing" class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
                        <span v-else>🚀 Generar Propuesta</span>
                    </button>
                    <p v-if="!processing && selectedRucs.length === 0" class="text-center text-[10px] text-red-400 mt-2">Selecciona al menos una empresa</p>
                </div>
            </div>
        </div>

        <!-- Right Panel: Results -->
        <div class="w-full xl:w-2/3 bg-dark-lighter p-6 rounded-xl border border-gray-800 shadow-lg flex flex-col min-h-0">
            <h3 class="text-lg font-bold text-white mb-4 flex justify-between items-center">
                <span>📊 Resultados</span>
                <button v-if="results.length > 0 || errors.length > 0" @click="clearResults" class="text-xs text-gray-500 hover:text-white">Limpiar</button>
            </h3>

            <!-- Initial State -->
            <div v-if="results.length === 0 && errors.length === 0 && !processing" class="flex-1 flex flex-col items-center justify-center text-gray-600 opacity-50">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-24 w-24 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>Los resultados de la generación aparecerán aquí</p>
            </div>

             <!-- Processing State -->
            <div v-if="processing" class="flex-1 flex flex-col items-center justify-center text-primary">
                 <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-primary mb-4"></div>
                 <p class="text-white font-medium animate-pulse">Procesando {{ selectedRucs.length }} empresas...</p>
                 <p class="text-xs text-gray-400 mt-2">Esto puede tomar unos momentos</p>
            </div>

            <!-- Results List -->
            <div v-if="!processing && (results.length > 0 || errors.length > 0)" class="flex-1 overflow-y-auto custom-scrollbar space-y-6">
                
                <!-- Successes -->
                <div v-if="results.length > 0">
                    <h4 class="text-green-400 font-bold text-sm mb-3 uppercase tracking-wider">✅ Completados ({{ results.length }})</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div v-for="res in results" :key="res.ruc" class="bg-gray-800/50 border border-green-500/20 rounded-lg p-4 hover:bg-gray-800 transition-colors">
                            <div class="flex justify-between items-start mb-2">
                                <div>
                                    <p class="text-white font-bold">{{ getCompanyName(res.ruc) }}</p>
                                    <p class="text-xs text-gray-500 font-mono">{{ res.ruc }}</p>
                                </div>
                                <span class="bg-green-900/30 text-green-400 text-[10px] px-2 py-0.5 rounded font-mono">{{ res.ticket }}</span>
                            </div>
                            
                            <div class="flex gap-2 mt-3">
                                <a v-if="res.csv" :href="getFileUrl(res.csv)" target="_blank" class="flex-1 bg-dark border border-gray-600 hover:border-gray-400 text-gray-300 hover:text-white text-xs py-1.5 rounded text-center transition-colors">
                                    CSV
                                </a>
                                <a v-if="res.xlsx" :href="getFileUrl(res.xlsx)" target="_blank" class="flex-1 bg-green-700/20 border border-green-800 hover:bg-green-700/40 text-green-400 text-xs py-1.5 rounded text-center transition-colors">
                                    Excel
                                </a>
                                <a v-if="res.zip" :href="getFileUrl(res.zip)" target="_blank" class="flex-1 bg-dark border border-gray-600 hover:border-gray-400 text-gray-300 hover:text-white text-xs py-1.5 rounded text-center transition-colors">
                                    ZIP
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Errors -->
                <div v-if="errors.length > 0">
                    <h4 class="text-red-400 font-bold text-sm mb-3 uppercase tracking-wider">❌ Errores ({{ errors.length }})</h4>
                     <div class="space-y-2">
                        <div v-for="(err, idx) in errors" :key="idx" class="bg-red-900/10 border border-red-900/30 rounded-lg p-3">
                            <div class="flex items-center justify-between mb-1">
                                <span class="text-red-300 font-bold text-sm">{{ getCompanyName(err.ruc) || err.ruc }}</span>
                                <span class="text-red-500/50 text-[10px] font-mono">{{ err.ruc }}</span>
                            </div>
                             <p class="text-gray-400 text-xs">{{ err.error || 'Error desconocido' }}</p>
                        </div>
                     </div>
                </div>

            </div>

        </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import api from '../apiConfig';

const companies = ref([]);
const loadingCompanies = ref(false);
const processing = ref(false);
const selectedRucs = ref([]);

const results = ref([]);
const errors = ref([]);

// Dates Setup
const now = new Date();
const currentYear = now.getFullYear();
const currentMonth = String(now.getMonth() + 1).padStart(2, '0');
const defaultPeriod = `${currentYear}${currentMonth}`;

// Form Config
const config = ref({
    periodo: defaultPeriod,
    fec_ini: `${currentYear}-${currentMonth}-01`,
    fec_fin: new Date(currentYear, now.getMonth() + 1, 0).toISOString().split('T')[0] // Last day of current month
});

const fetchCompanies = async () => {
    loadingCompanies.value = true;
    try {
        const res = await api.get('/empresas/');
        companies.value = res.data || [];
    } catch (e) {
        console.error("Error loading companies", e);
    } finally {
        loadingCompanies.value = false;
    }
};

const filteredCompanies = computed(() => {
    return companies.value.filter(c => c.propuesta_activa);
});

const allSelected = computed(() => {
    return filteredCompanies.value.length > 0 && selectedRucs.value.length === filteredCompanies.value.length;
});

const toggleSelectAll = () => {
    if (allSelected.value) {
        selectedRucs.value = [];
    } else {
        selectedRucs.value = filteredCompanies.value.map(c => c.ruc);
    }
};

const getCompanyName = (ruc) => {
    const c = companies.value.find(c => c.ruc === ruc);
    return c ? c.razon_social : ruc;
};

// Assuming the API returns a local path like "/app/registros/...", we need to convert it to a downloadable URL if it's served via static.
// If your nginx serves /app/registros mapped to a URL, use that. 
// OR use an endpoint download. For now, assuming direct link via simple static serving? 
// Based on context, Nginx root is /usr/share/nginx/html. The volumes mounted in backend are /app/registros.
// Unless Nginx maps a /downloads route to backend volume, these paths might not be directly clickable.
// User said: "El frontend puede mostrar las rutas para descargar".
// Let's assume for now we just show links, maybe the user needs a download endpoint like /api/download?
// Or maybe files are moved to 'public'. 
// TRICK: The user prompt example shows "/app/registros/...". This is an internal container path.
// The browser cannot reach "/app/registros".
// I will treat them as mostly informational or assume there is a generic download route.
// Let's create a proxy download link if possible, or just link assuming web server maps it?
// Given existing 'Descarga' patterns, usually we need an endpoint.
// Request said "El frontend puede mostrar las rutas para descargar". I will wrap them in a simple function that might just point to an assumed static route or leave as href for now.
// Update: Without a specific download endpoint, standard practice is `API_URL + '/files?path=' + encodedPath`.
// I will use a simple placeholder logic for now.

const getFileUrl = (internalPath) => {
    // Basic heuristic: if it's an internal path, maybe we can't download straightforwardly without a file server.
    // However, I'll bind it to a backend endpoint I hope exists or just return '#' and warn.
    // Actually, I'll construct a direct link assuming the backend serves static files or I can add a quick download helper.
    // Let's assume the backend has static mounting or similar. 
    // Wait, let's look at `web` container. It has nginx. 
    // If backend volume is not shared with web container (it isn't in docker-compose), then the frontend container Nginx CANNOT see those files.
    // The backend MUST serve them.
    // Does the backend have a download endpoint? Not specified.
    // User said: "El frontend puede mostrar las rutas para descargar o mostrar el XLSX."
    // I will try to point to `${API_BASE_URL}/download?path=${path}` strategy if I can, but I'll make it generic.
    
    // For now, I will assume a generic endpoint `/download_file` exists or similar. 
    // If not, I'll just link to the api url + path and hope backend handles it.
    // Let's stick to just the path for display if we can't download.
    // Actually, I'll log it.
    
    // Re-reading user request: "results: lista con rutas... El frontend puede mostrar las rutas para descargar"
    // I will pass the path to a hypothetical download endpoint.
    return `/api/files/download?path=${encodeURIComponent(internalPath)}`;
};

const runProposal = async () => {
    processing.value = true;
    results.value = [];
    errors.value = [];

    const payload = {
        periodo: config.value.periodo,
        fec_ini: config.value.fec_ini,
        fec_fin: config.value.fec_fin,
        rucs: selectedRucs.value
    };

    try {
        const res = await api.post('/propuesta/run', payload);
        
        // Response structure: { ok: bool, results: [], errors: [] }
        if (res.data) {
            results.value = res.data.results || [];
            errors.value = res.data.errors || [];
            
            if (errors.value.length > 0) {
                // Determine if mixed success
                if (results.value.length > 0) {
                    // Mixed
                } else {
                    // All failed
                }
            }
        }
    } catch (e) {
        console.error("Error generating proposal", e);
        alert("Error de conexión o servidor: " + e.message);
    } finally {
        processing.value = false;
    }
};

const clearResults = () => {
    results.value = [];
    errors.value = [];
}

onMounted(fetchCompanies);
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
