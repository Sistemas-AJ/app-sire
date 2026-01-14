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
            <div class="col-span-3">Razón Social</div>
            <div class="col-span-2">Usuario SOL</div>
            <div class="col-span-2">Propuesta</div> <!-- New Column -->
            <div class="col-span-2">Estado Sesión</div>
            <div class="col-span-1 text-right">Acciones</div>
         </div>

         <!-- Table Body (Scrollable) -->
         <div class="overflow-y-auto flex-1 p-2 space-y-1">
             <div v-if="loading" class="text-center py-8 text-blue-400">Cargando empresas...</div>
             <div v-if="error" class="text-center py-8 text-red-500 font-bold bg-red-900/10 rounded m-2 border border-red-900/30">
                 {{ error }}
             </div>

             <div v-if="!loading && !error" v-for="company in companies" :key="company.ruc" class="grid grid-cols-12 items-center py-3 px-4 hover:bg-dark-border/30 rounded-lg transition-colors text-sm border border-transparent hover:border-dark-border/50">
                <div class="col-span-2 font-mono text-white">{{ company.ruc }}</div>
                <div class="col-span-3 font-medium text-gray-300 truncate pr-2">{{ company.razon_social }}</div>
                <div class="col-span-2">
                    <span v-if="company.usuario_sol" class="text-text-muted">{{ company.usuario_sol }}</span>
                    <span v-else class="text-red-500 text-xs bg-red-900/20 px-2 py-0.5 rounded">Faltante</span>
                </div>
                
                <!-- Propuesta Column -->
                <div class="col-span-2 flex items-center">
                    <div 
                        class="w-3 h-3 rounded-full mr-2"
                        :class="company.has_sire ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'"
                        :title="company.has_sire ? 'SIRE Configurado' : 'Sin credenciales SIRE'"
                    ></div>
                    <span class="text-xs text-secondary hidden xl:inline">{{ company.has_sire ? 'Activo' : 'Inactivo' }}</span>
                </div>

                <div class="col-span-2">
                    <span :class="getStatusClass(company.estado_sesion)" class="px-2 py-0.5 rounded-full text-xs font-semibold border inline-block text-center min-w-[80px]">
                        {{ company.estado_sesion || 'PENDIENTE' }}
                    </span>
                </div>
                <div class="col-span-1 text-right">
                    <button @click="editCompany(company)" class="text-primary hover:text-white transition-colors bg-dark p-1.5 rounded-md hover:bg-dark-border" title="Editar">
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

    <!-- Right Column: Registration/Edit Form (Fixed Width) -->
    <div class="w-full md:w-[380px] flex flex-col space-y-4 overflow-y-auto custom-scrollbar">
        
        <!-- Registration/Edit Card -->
        <div class="bg-white rounded-2xl p-6 shadow-xl h-auto relative">
            
            <!-- Cancel Edit Button (Top Right) -->
            <button v-if="isEditMode" @click="cancelEdit" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
            </button>

            <div class="text-center mb-6">
                <div class="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3 transition-colors"
                    :class="isEditMode ? 'bg-orange-100 text-orange-500' : 'bg-blue-100 text-primary'"
                >
                    <span v-if="isEditMode" class="text-2xl">✏️</span>
                    <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                </div>
                <h2 class="text-xl font-bold text-dark">{{ isEditMode ? 'Editar Empresa' : 'Registrar Empresa' }}</h2>
                <p class="text-xs text-secondary mt-1">{{ isEditMode ? 'Actualiza los datos o credenciales' : 'Ingresa los datos de la empresa' }}</p>
            </div>

            <!-- Form Start -->
            <form @submit.prevent="handleSubmit" class="space-y-4">
                
                <!-- Main Info Section -->
                <div class="space-y-4">
                    <div>
                        <label class="block text-xs font-bold text-gray-700 mb-1.5">RUC</label>
                         <div class="relative">
                            <span class="absolute left-3 top-2.5 text-gray-400">🔢</span>
                            <input v-model="form.ruc" required maxlength="11" placeholder="20123456789" 
                                :disabled="isEditMode"
                                :class="isEditMode ? 'bg-gray-200 cursor-not-allowed text-gray-500' : 'bg-gray-50 text-dark border-gray-200'"
                                class="w-full border rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-bold text-gray-700 mb-1.5">Razón Social</label>
                        <div class="relative">
                            <span class="absolute left-3 top-2.5 text-gray-400">🏢</span>
                            <input v-model="form.razon_social" required placeholder="Ej. Mi Empresa SAC" class="w-full bg-gray-50 border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm text-dark focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                        </div>
                    </div>

                    <div>
                         <label class="block text-xs font-bold text-gray-700 mb-1.5">Usuario SOL</label>
                         <div class="relative">
                            <span class="absolute left-3 top-2.5 text-gray-400">👤</span>
                            <input v-model="form.usuario_sol" placeholder="Usuario SOL" class="w-full bg-gray-50 border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm text-dark focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                        </div>
                    </div>
                     <div>
                         <label class="block text-xs font-bold text-gray-700 mb-1.5">Clave SOL</label>
                         <div class="relative">
                            <span class="absolute left-3 top-2.5 text-gray-400">🔑</span>
                            <input type="password" v-model="form.clave_sol" placeholder="••••••••" class="w-full bg-gray-50 border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm text-dark focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                        </div>
                    </div>

                    <button type="submit" class="w-full font-bold py-3 rounded-xl shadow-lg transition-all transform hover:scale-[1.02] mt-2 text-white"
                        :class="isEditMode ? 'bg-orange-500 hover:bg-orange-600 shadow-orange-500/30' : 'bg-primary hover:bg-primary-dark shadow-primary/30'">
                        {{ isEditMode ? 'Actualizar Datos Básicos' : 'Guardar Empresa' }}
                    </button>
                </div>
            </form>

            <!-- SIRE Credentials Section (Only in Edit Mode) -->
            <div v-if="isEditMode" class="mt-8 pt-6 border-t border-gray-200">
                <h3 class="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
                    🔐 Credenciales SIRE
                    <span class="text-[10px] bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full">Propuesta</span>
                </h3>
                
                <form @submit.prevent="updateSireCredentials" class="space-y-4">
                     <div>
                         <label class="block text-xs font-bold text-gray-700 mb-1.5">Client ID</label>
                         <input v-model="sireForm.sire_client_id" placeholder="id-xxxxx" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-dark focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                    </div>
                     <div>
                         <label class="block text-xs font-bold text-gray-700 mb-1.5">Client Secret</label>
                         <input type="password" v-model="sireForm.sire_client_secret" placeholder="secret-xxxxx" class="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-dark focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary" />
                    </div>
                    
                    <button type="submit" class="w-full bg-gray-800 hover:bg-gray-900 text-white font-bold py-2.5 rounded-lg shadow-md transition-all text-sm">
                        💾 Guardar Credenciales SIRE
                    </button>
                </form>
            </div>
            
            <!-- Delete Zone (Only in Edit Mode) -->
            <div v-if="isEditMode" class="mt-8 pt-6 border-t border-gray-200">
                <h3 class="text-sm font-bold text-red-600 mb-3">Zona de Peligro</h3>
                <button @click="deleteCompany" class="w-full border border-red-200 bg-red-50 hover:bg-red-100 text-red-600 font-bold py-2.5 rounded-lg transition-all text-sm flex items-center justify-center gap-2">
                    🗑️ Eliminar Empresa
                </button>
                <p class="text-[10px] text-gray-400 mt-2 text-center">Se borrará todo el historial y archivos asociados.</p>
            </div>

            <!-- Import Section (Only in Create Mode) -->
            <div v-if="!isEditMode" class="mt-6 pt-4 border-t border-gray-100 text-center">
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
import { ref, computed, onMounted } from 'vue';
import api from '../apiConfig';

const companies = ref([]);
const fileInput = ref(null);
const importStatus = ref('');
const importError = ref(false);
const loading = ref(false);
const error = ref(null);

// Form States
const form = ref({ ruc: '', razon_social: '', usuario_sol: '', clave_sol: '' });
const sireForm = ref({ sire_client_id: '', sire_client_secret: '' });

const editingCompanyRuc = ref(null);
const isEditMode = computed(() => !!editingCompanyRuc.value);

const fetchCompanies = async () => {
    loading.value = true;
    error.value = null;
    try {
        const res = await api.get('/empresas/');
        if (Array.isArray(res.data)) {
            companies.value = res.data;
        } else {
            throw new Error("La respuesta del servidor no es válida (se esperaba una lista).");
        }
    } catch (e) {
        console.error("Error loading companies", e);
        error.value = "Error al cargar empresas: " + (e.message || e);
    } finally {
        loading.value = false;
    }
};

const handleSubmit = async () => {
    if (isEditMode.value) {
        await updateCompany();
    } else {
        await createCompany();
    }
};

// CREATE
const createCompany = async () => {
    try {
        await api.post('/empresas/', {
            ...form.value,
            activo: true
        });
        resetForm();
        fetchCompanies();
        alert("Empresa registrada correctamente");
    } catch (e) {
        alert("Error registrando empresa: " + (e.response?.data?.detail || e.message));
    }
};

// UPDATE BASIC INFO
const updateCompany = async () => {
    try {
        // PUT /empresas/{ruc}
        // Body: razon_social, usuario_sol, clave_sol, activo
        await api.put(`/empresas/${form.value.ruc}`, {
            razon_social: form.value.razon_social,
            usuario_sol: form.value.usuario_sol,
            clave_sol: form.value.clave_sol,
            activo: true
        });
        fetchCompanies();
        alert("Datos de empresa actualizados");
    } catch (e) {
        alert("Error actualizando empresa: " + (e.response?.data?.detail || e.message));
    }
};

// UPDATE SIRE CREDENTIALS
const updateSireCredentials = async () => {
    if (!form.value.ruc) return;
    try {
        // POST /empresas/{ruc}/credenciales
        // Body needs: usuario_sol, clave_sol, sire_client_id, sire_client_secret, activo
        // Note: The endpoint seems to require re-sending SOL credentials too according to user request,
        // or maybe it's using them to validate? We will send what we have in the form.
        await api.post(`/empresas/${form.value.ruc}/credenciales`, {
            usuario_sol: form.value.usuario_sol,
            clave_sol: form.value.clave_sol,
            sire_client_id: sireForm.value.sire_client_id,
            sire_client_secret: sireForm.value.sire_client_secret,
            activo: true
        });
        fetchCompanies(); // Refresh to update "has_sire" status
        alert("Credenciales SIRE guardadas exitosamente y validadas.");
    } catch (e) {
        alert("Error guardando credenciales SIRE: " + (e.response?.data?.detail || e.message));
    }
};

// DELETE
const deleteCompany = async () => {
    if(!confirm(`⚠️ ELIMINAR EMPRESA ${form.value.ruc}\n\n¿Estás seguro? Se eliminarán TODOS los registros, archivos e historial asociados a esta empresa. Esta acción no se puede deshacer.`)) return;

    try {
        await api.delete(`/empresas/${form.value.ruc}`);
        resetForm();
        fetchCompanies();
        alert("Empresa eliminada permanentemente.");
    } catch (e) {
         alert("Error eliminando empresa: " + (e.response?.data?.detail || e.message));
    }
};

// Edit Actions
const editCompany = (company) => {
    editingCompanyRuc.value = company.ruc;
    form.value = {
        ruc: company.ruc,
        razon_social: company.razon_social,
        usuario_sol: company.usuario_sol,
        clave_sol: company.clave_sol || '' // Usually hidden/empty from backend?
    };
    // Clean SIRE form as we might not get these secrets back, or we want to overwrite them
    sireForm.value = {
        sire_client_id: '',
        sire_client_secret: ''
    };
};

const cancelEdit = () => {
    resetForm();
};

const resetForm = () => {
    editingCompanyRuc.value = null;
    form.value = { ruc: '', razon_social: '', usuario_sol: '', clave_sol: '' };
    sireForm.value = { sire_client_id: '', sire_client_secret: '' };
}

// File Import
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

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent; 
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1; 
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8; 
}
</style>
