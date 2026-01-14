<template>
  <div class="p-8 h-full flex flex-col md:flex-row gap-8">
    
    <!-- Left Column: KPIs & Table (Fills remaining space) -->
    <div class="flex-1 flex flex-col space-y-6 min-h-0">
      
      <!-- KPI Stats -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Card 1: Total Empresas -->
        <div class="bg-dark-lighter p-5 rounded-xl border border-blue-500/30 relative overflow-hidden group">
          <div class="absolute right-0 top-0 h-full w-1 bg-primary"></div>
          <span class="text-gray-400 text-xs font-bold uppercase tracking-wider">Total Empresas</span>
          <p class="text-4xl font-bold text-white mt-1">{{ companies.length }}</p>
        </div>

        <!-- Card 2: Con Credenciales -->
        <div class="bg-dark-lighter p-5 rounded-xl border border-green-500/30 relative overflow-hidden">
           <div class="absolute right-0 top-0 h-full w-1 bg-green-500"></div>
            <span class="text-gray-400 text-xs font-bold uppercase tracking-wider">Con Credenciales</span>
            <p class="text-4xl font-bold text-green-400 mt-1">{{ companies.filter(c => c.usuario_sol).length }}</p>
        </div>

        <!-- Card 3: Problemas Login -->
        <div class="bg-dark-lighter p-5 rounded-xl border border-red-500/30 relative overflow-hidden">
             <div class="absolute right-0 top-0 h-full w-1 bg-red-500"></div>
            <span class="text-gray-400 text-xs font-bold uppercase tracking-wider">Problemas Login</span>
            <p class="text-4xl font-bold text-red-500 mt-1">{{ companies.filter(c => c.estado_sesion === 'ERROR').length }}</p>
        </div>
      </div>

      <!-- Table Section -->
      <div class="bg-dark-lighter rounded-xl border border-dark-border shadow-lg flex-1 overflow-hidden flex flex-col">
        <!-- Table Header -->
         <div class="grid grid-cols-12 bg-dark/50 text-xs uppercase text-text-muted font-semibold border-b border-dark-border py-4 px-6">
            <div class="col-span-2">RUC</div>
            <div class="col-span-4">Razón Social</div>
            <div class="col-span-2">Usuario SOL</div>
            <div class="col-span-2">Estado Sesión</div>
            <div class="col-span-2 text-right">Acciones</div>
         </div>

         <!-- Table Body (Scrollable) -->
         <div class="overflow-y-auto flex-1 p-2 space-y-1">
             <div v-if="loading" class="text-center py-8 text-blue-400">Cargando empresas...</div>
             <div v-if="error" class="text-center py-8 text-red-500 font-bold bg-red-900/10 rounded m-2 border border-red-900/30">
                 {{ error }}
             </div>

             <div v-if="!loading && !error" v-for="company in companies" :key="company.ruc" class="grid grid-cols-12 items-center py-3 px-4 hover:bg-dark-border/30 rounded-lg transition-colors text-sm border border-transparent hover:border-dark-border/50">
                <div class="col-span-2 font-mono text-white">{{ company.ruc }}</div>
                <div class="col-span-4 font-medium text-gray-300 truncate pr-2">{{ company.razon_social }}</div>
                <div class="col-span-2">
                    <span v-if="company.usuario_sol" class="text-text-muted">{{ company.usuario_sol }}</span>
                    <span v-else class="text-red-500 text-xs bg-red-900/20 px-2 py-0.5 rounded">Faltante</span>
                </div>
                <div class="col-span-2">
                    <span :class="getStatusClass(company.estado_sesion)" class="px-2 py-0.5 rounded-full text-xs font-semibold border inline-block text-center min-w-[80px]">
                        {{ company.estado_sesion || 'PENDIENTE' }}
                    </span>
                </div>
                <div class="col-span-2 text-right">
                    <button class="text-primary hover:text-white transition-colors bg-dark p-1.5 rounded-md hover:bg-dark-border" title="Editar">
                         ✏️
                    </button>
                </div>
             </div>
             
             <!-- Empty State -->
             <div v-if="!loading && !error && companies.length === 0" class="h-full flex flex-col items-center justify-center text-gray-500">
                <p>No hay empresas registradas.</p>
             </div>
         </div>
      </div>
    </div>

    <!-- Right Column: Registration Form (Fixed Width) -->
    <div class="w-full md:w-[360px] flex flex-col space-y-4">
        
        <!-- Registration Card -->
        <div class="bg-white rounded-2xl p-6 shadow-xl h-auto">
            <div class="text-center mb-6">
                <div class="w-12 h-12 bg-blue-100 text-primary rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                </div>
                <h2 class="text-xl font-bold text-dark">Registrar Empresa</h2>
                <p class="text-xs text-secondary mt-1">Ingresa los datos de la empresa</p>
            </div>

            <form @submit.prevent="saveCompany" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-gray-700 mb-1.5">Razón Social</label>
                    <div class="relative">
                        <span class="absolute left-3 top-2.5 text-gray-400">🏢</span>
                        <input v-model="form.razon_social" required placeholder="Ej. Mi Empresa SAC" class="w-full bg-gray-50 border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm text-dark focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-bold text-gray-700 mb-1.5">RUC</label>
                     <div class="relative">
                        <span class="absolute left-3 top-2.5 text-gray-400">🔢</span>
                        <input v-model="form.ruc" required maxlength="11" placeholder="20123456789" class="w-full bg-gray-50 border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm text-dark focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                    </div>
                </div>

                <div>
                     <label class="block text-xs font-bold text-gray-700 mb-1.5">Usuario</label>
                     <div class="relative">
                        <span class="absolute left-3 top-2.5 text-gray-400">👤</span>
                        <input v-model="form.usuario_sol" placeholder="Usuario SOL" class="w-full bg-gray-50 border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm text-dark focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                    </div>
                </div>
                 <div>
                     <label class="block text-xs font-bold text-gray-700 mb-1.5">Contraseña</label>
                     <div class="relative">
                        <span class="absolute left-3 top-2.5 text-gray-400">🔑</span>
                        <input type="password" v-model="form.clave_sol" placeholder="••••••••" class="w-full bg-gray-50 border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm text-dark focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                    </div>
                </div>

                <button type="submit" class="w-full bg-primary hover:bg-primary-dark text-white font-bold py-3 rounded-xl shadow-lg shadow-primary/30 transition-all transform hover:scale-[1.02] mt-2">
                    Guardar Empresa
                </button>
            </form>

            <div class="mt-6 pt-4 border-t border-gray-100 text-center">
                 <p class="text-xs text-gray-400 mb-3">O importa desde Excel</p>
                 <button @click="triggerFileInput" class="w-full border border-gray-200 hover:border-gray-400 text-gray-600 font-medium py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2">
                    <span class="text-lg">📤</span> Importar
                 </button>
                 <input type="file" ref="fileInput" @change="handleFileSelect" class="hidden" accept=".csv,.txt,.xlsx" />
                 <p v-if="importStatus" class="mt-2 text-xs" :class="importError ? 'text-red-500' : 'text-green-500'">{{ importStatus }}</p>
            </div>
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../apiConfig';

const companies = ref([]);
const form = ref({ ruc: '', razon_social: '', usuario_sol: '', clave_sol: '' });
const fileInput = ref(null);
const importStatus = ref('');
const importError = ref(false);
const loading = ref(false);
const error = ref(null);

const fetchCompanies = async () => {
    try {
        const res = await api.get('/empresas/');
        if (Array.isArray(res.data)) {
            companies.value = res.data;
        } else {
            throw new Error("La respuesta del servidor no es válida (se esperaba una lista).");
        }
    } catch (e) {
        console.error("Error loading companies", e);
    }
};

const saveCompany = async () => {
    try {
        await api.post('/empresas/', form.value);
        // Reset form
        form.value = { ruc: '', razon_social: '', usuario_sol: '', clave_sol: '' };
        fetchCompanies();
        alert("Empresa guardada correctamente");
    } catch (e) {
        alert("Error guardando empresa: " + (e.response?.data?.detail || e.message));
    }
};

const triggerFileInput = () => {
    fileInput.value.click();
}

const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if(file) await uploadFile(file);
};

const uploadFile = async (file) => {
    importStatus.value = "Subiendo...";
    importError.value = false;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const res = await api.post('/empresas/import', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        let msg = res.data.message;
        if(res.data.errors && res.data.errors.length > 0) {
            msg += `. ${res.data.errors.length} errores (ver consola)`;
            console.warn("Import errors:", res.data.errors);
        }
        
        importStatus.value = msg;
        fetchCompanies();
    } catch(e) {
        importError.value = true;
        importStatus.value = "Error: " + (e.response?.data?.detail || e.message);
    }
}

const getStatusClass = (status) => {
    switch(status) {
        case 'OK': return 'bg-green-900/30 text-green-400 border-green-900';
        case 'ERROR': return 'bg-red-900/30 text-red-500 border-red-900';
        default: return 'bg-gray-700 text-gray-400 border-gray-600';
    }
};

onMounted(fetchCompanies);
</script>
