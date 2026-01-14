<template>
  <div class="p-8 h-full flex flex-col gap-6">
    
    <!-- Header -->
    <div>
        <h2 class="text-3xl font-bold text-white flex items-center gap-3">
             <span class="text-primary text-4xl">📂</span>
            Repositorio de XML
        </h2>
        <p class="text-gray-400 text-sm mt-1">Historial y gestión de documentos electrónicos descargados.</p>
    </div>

    <!-- Filters Bar -->
    <div class="bg-dark-lighter p-4 rounded-xl border border-gray-800 shadow-lg flex flex-col md:flex-row gap-4 items-end md:items-center justify-between">
        
        <div class="flex flex-wrap gap-4 flex-1">
            <!-- Periodo -->
            <div class="w-32">
                <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Periodo</label>
                <input v-model="filters.periodo" type="text" placeholder="YYYYMM" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary focus:outline-none placeholder-gray-600 font-mono" />
            </div>

            <!-- Empresa -->
            <div class="w-48">
                <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Empresa</label>
                <select v-model="filters.ruc_empresa" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary focus:outline-none appearance-none">
                    <option value="">Todas</option>
                    <option v-for="c in companies" :key="c.ruc" :value="c.ruc">{{ c.razon_social }}</option>
                </select>
            </div>

            <!-- Status -->
             <div class="w-32">
                <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Estado</label>
                <select v-model="filters.status" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:border-primary focus:outline-none appearance-none">
                    <option value="">Todos</option>
                    <option value="OK">OK (Descargado)</option>
                    <option value="ERROR">Error</option>
                    <option value="MISSING">No Encontrado</option>
                </select>
            </div>
             
             <!-- Search -->
            <div class="flex-1 min-w-[200px]">
                <label class="block text-[10px] font-bold text-gray-500 uppercase mb-1">Búsqueda</label>
                <div class="relative">
                    <input v-model="filters.search" @keyup.enter="fetchItems" type="text" placeholder="RUC Emisor, Serie, Número..." class="w-full bg-dark border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-white text-sm focus:border-primary focus:outline-none placeholder-gray-600" />
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
            </div>
        </div>

        <button @click="fetchItems" class="bg-primary hover:bg-blue-600 text-white font-bold h-10 px-6 rounded-lg shadow-lg flex items-center transition-colors">
            Filtrar
        </button>
    </div>

    <!-- Results Table -->
    <div class="flex-1 bg-dark-lighter rounded-xl border border-gray-800 shadow-lg flex flex-col min-h-0 relative">
        <div class="flex-1 overflow-y-auto custom-scrollbar rounded-t-xl">
            <table class="w-full text-left text-sm text-gray-400">
                <thead class="bg-dark/80 text-xs uppercase text-gray-500 sticky top-0 backdrop-blur-sm z-10">
                    <tr>
                        <th class="px-6 py-4 font-semibold">Emisión</th>
                        <th class="px-6 py-4 font-semibold">Emisor</th>
                        <th class="px-6 py-4 font-semibold">Comprobante</th>
                        <th class="px-6 py-4 font-semibold">Total</th>
                        <th class="px-6 py-4 font-semibold text-center">Estado</th>
                        <th class="px-6 py-4 font-semibold text-right">Acciones</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-dark-border">
                    <tr v-if="loading" class="animate-pulse">
                        <td colspan="6" class="px-6 py-12 text-center text-gray-500">
                            Cargando repositorio...
                        </td>
                    </tr>
                    <tr v-if="!loading && items.length === 0">
                        <td colspan="6" class="px-6 py-12 text-center text-gray-600 flex flex-col items-center">
                            <span class="text-4xl mb-2 grayscale opacity-50">📭</span>
                            No se encontraron comprobantes con estos filtros.
                        </td>
                    </tr>
                    
                    <tr v-for="item in items" :key="item.id" class="hover:bg-dark-border/30 transition-colors group">
                        <td class="px-6 py-4 font-mono text-white">{{ item.fecha_emision }}</td>
                        <td class="px-6 py-4">
                            <div class="text-white font-bold truncate max-w-[200px]">{{ item.razon_social_emisor || 'Desconocido' }}</div>
                            <div class="text-xs text-gray-500 font-mono">{{ item.ruc_emisor }}</div>
                        </td>
                        <td class="px-6 py-4">
                            <div class="flex items-center gap-2">
                                <span class="bg-gray-800 text-gray-300 px-1.5 py-0.5 rounded text-[10px] font-mono">{{ item.tipo_comprobante }}</span>
                                <span class="text-white font-mono">{{ item.serie }}-{{ item.numero }}</span>
                            </div>
                        </td>
                         <td class="px-6 py-4 font-mono font-bold text-gray-300">
                             {{ item.moneda }} {{ item.total }}
                         </td>
                        <td class="px-6 py-4 text-center">
                            <span :class="getStatusBadge(item.status_xml)" class="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border min-w-[60px] text-center">
                                {{ item.status_xml }}
                            </span>
                        </td>
                        <td class="px-6 py-4 text-right space-x-3">
                             <a v-if="item.status_xml === 'OK' && item.xml_path" :href="getDownloadLink(item.xml_path)" target="_blank" class="text-green-400 hover:text-green-300 font-bold text-xs underline" title="Descargar XML">
                                XML
                            </a>
                            <button @click="openDetail(item.id)" class="text-blue-400 hover:text-blue-300 font-bold text-xs underline">
                                Detalle
                            </button>
                            <!-- Optional retry logic if configured -->
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        <div class="p-4 border-t border-gray-800 flex justify-between items-center bg-dark/50 rounded-b-xl">
            <span class="text-xs text-gray-500">
                Mostrando {{ items.length }} de {{ pagination.total }} registros
            </span>
            <div class="flex items-center gap-2">
                <button @click="changePage(pagination.page - 1)" :disabled="pagination.page <= 1" class="p-2 rounded-lg bg-dark border border-gray-700 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-gray-400">
                    ◀️
                </button>
                <span class="text-sm font-bold text-white px-2">Página {{ pagination.page }} de {{ pagination.pages }}</span>
                <button @click="changePage(pagination.page + 1)" :disabled="pagination.page >= pagination.pages" class="p-2 rounded-lg bg-dark border border-gray-700 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-gray-400">
                    ▶️
                </button>
            </div>
        </div>
    </div>

    <!-- Detail Modal (Reusing structure) -->
    <div v-if="showModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="closeModal">
        <div class="bg-dark-lighter w-full max-w-2xl rounded-2xl border border-gray-700 shadow-2xl flex flex-col max-h-[90vh] animate-fade-in-up">
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
import { ref, onMounted, reactive } from 'vue';
import api from '../apiConfig';

const companies = ref([]);
const loading = ref(false);
const items = ref([]);

// Pagination State
const pagination = reactive({
    page: 1,
    page_size: 20,
    total: 0,
    pages: 1
});

// Filters
const now = new Date();
const filters = reactive({
    periodo: `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`,
    ruc_empresa: '',
    status: '',
    search: ''
});

// Modal State
const showModal = ref(false);
const detailData = ref(null);

// Methods
const fetchCompanies = async () => {
    try {
        const res = await api.get('/empresas/');
        companies.value = res.data || [];
    } catch(e) { console.error("Error loading companies", e); }
};

const fetchItems = async () => {
    loading.value = true;
    try {
        const params = {
            page: pagination.page,
            page_size: pagination.page_size,
            periodo: filters.periodo,
            ruc_empresa: filters.ruc_empresa || null,
            status: filters.status || null,
            search: filters.search || null
        };
        const res = await api.get('/xml/repository', { params });
        const data = res.data; // { items: [], total: 0, page: 1, pages: 1 }
        
        items.value = data.items || [];
        pagination.total = data.total || 0;
        pagination.pages = data.pages || 1;
        pagination.page = data.page || 1;

    } catch (e) {
        console.error("Error fetching repository", e);
        // Mock data fallback if endpoint 404s for demo
        /*
        items.value = [];
        pagination.total = 0;
        */
        if (e.response && e.response.status === 404) {
             items.value = []; // Endpoint not ready
        }
    } finally {
        loading.value = false;
    }
};

const changePage = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.pages) {
        pagination.page = newPage;
        fetchItems();
    }
};

const getStatusBadge = (status) => {
     const map = {
        'OK': 'bg-green-900/30 text-green-400 border-green-900',
        'ERROR': 'bg-red-900/30 text-red-500 border-red-900',
        'NOT_FOUND': 'bg-gray-700 text-gray-400 border-gray-500',
        'MISSING': 'bg-gray-800 text-gray-500 border-gray-600',
        'AUTH': 'bg-orange-900/30 text-orange-400 border-orange-900'
    };
    return map[status] || 'bg-gray-800 text-gray-500';
};

const getDownloadLink = (path) => `/api/files/download?path=${encodeURIComponent(path)}`;

// Modal Logic
const openDetail = async (id) => {
    showModal.value = true;
    detailData.value = null;
    try {
        const res = await api.get('/xml/detalle', { params: { item_id: id }});
        detailData.value = res.data;
    } catch (e) {
         if (e.response && e.response.status === 404) {
             alert("Detalle no disponible (XML faltante o error).");
        } else {
             alert("Error: " + e.message);
        }
        showModal.value = false;
    }
};
const closeModal = () => showModal.value = false;

onMounted(async () => {
    await fetchCompanies();
    fetchItems();
});

</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up { animation: fade-in-up 0.3s ease-out; }
</style>
