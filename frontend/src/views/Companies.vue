<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-3xl font-bold text-white">Gestión de Empresas</h2>
      <div class="flex gap-3">
        <button @click="showImportModal = true" class="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-gray-600 flex items-center gap-2">
            📂 Importar Excel/CSV
        </button>
        <button @click="openModal()" class="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 shadow-lg shadow-primary/20">
            ✨ Nueva Empresa
        </button>
      </div>
    </div>

    <!-- Stats Rapidas -->
    <div class="grid grid-cols-3 gap-6 mb-6">
        <div class="bg-dark-lighter p-4 rounded-lg border border-gray-800">
            <span class="text-gray-500 text-xs">TOTAL EMPRESAS</span>
            <p class="text-2xl font-bold text-white">{{ companies.length }}</p>
        </div>
        <div class="bg-dark-lighter p-4 rounded-lg border border-gray-800">
            <span class="text-gray-500 text-xs">CON CREDENCIALES</span>
            <p class="text-2xl font-bold text-green-400">{{ companies.filter(c => c.usuario_sol).length }}</p>
        </div>
        <div class="bg-dark-lighter p-4 rounded-lg border border-gray-800">
            <span class="text-gray-500 text-xs">PROBLEMAS LOGIN</span>
            <p class="text-2xl font-bold text-red-400">{{ companies.filter(c => c.estado_sesion === 'ERROR').length }}</p>
        </div>
    </div>

    <!-- Tabla -->
    <div class="bg-dark-lighter rounded-xl border border-gray-800 shadow-lg overflow-hidden">
        <table class="w-full text-left text-sm text-gray-400">
            <thead class="bg-gray-800/50 text-xs uppercase text-gray-300">
                <tr>
                    <th class="px-6 py-3 font-medium">RUC</th>
                    <th class="px-6 py-3 font-medium">Razón Social</th>
                    <th class="px-6 py-3 font-medium">Usuario SOL</th>
                    <th class="px-6 py-3 font-medium">Estado Sesión</th>
                    <th class="px-6 py-3 font-medium text-right">Acciones</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-800">
                <tr v-for="company in companies" :key="company.ruc" class="hover:bg-gray-800/30 transition-colors">
                    <td class="px-6 py-4 font-mono text-white">{{ company.ruc }}</td>
                    <td class="px-6 py-4 font-medium">{{ company.razon_social }}</td>
                    <td class="px-6 py-4">
                        <span v-if="company.usuario_sol" class="text-gray-300">{{ company.usuario_sol }}</span>
                        <span v-else class="text-red-500 text-xs bg-red-900/20 px-2 py-1 rounded">Faltante</span>
                    </td>
                    <td class="px-6 py-4">
                        <span :class="getStatusClass(company.estado_sesion)" class="px-2 py-1 rounded-full text-xs font-semibold border">
                            {{ company.estado_sesion || 'PENDIENTE' }}
                        </span>
                    </td>
                    <td class="px-6 py-4 text-right">
                        <!-- TODO: Edit Functionality -->
                        <button class="text-primary hover:text-white transition-colors">✏️</button>
                    </td>
                </tr>
                <tr v-if="companies.length === 0">
                    <td colspan="5" class="px-6 py-8 text-center text-gray-600">
                        No hay empresas registradas. Importa una lista o crea una manualmente.
                    </td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Modal Crear -->
    <div v-if="showModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div class="bg-dark-lighter rounded-xl border border-gray-700 shadow-2xl w-full max-w-md p-6">
            <h3 class="text-xl font-bold text-white mb-4">Nueva Empresa</h3>
            <form @submit.prevent="saveCompany" class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1">RUC</label>
                    <input v-model="form.ruc" required maxlength="11" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary" />
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1">Razón Social</label>
                    <input v-model="form.razon_social" required class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary" />
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-medium text-gray-500 mb-1">Usuario SOL</label>
                        <input v-model="form.usuario_sol" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary" />
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-500 mb-1">Clave SOL</label>
                        <input type="password" v-model="form.clave_sol" class="w-full bg-dark border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary" />
                    </div>
                </div>
                
                <div class="flex justify-end gap-3 mt-6">
                    <button type="button" @click="showModal = false" class="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white transition-colors">Cancelar</button>
                    <button type="submit" class="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                        Guardar
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal Import -->
    <div v-if="showImportModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div class="bg-dark-lighter rounded-xl border border-gray-700 shadow-2xl w-full max-w-md p-6">
            <h3 class="text-xl font-bold text-white mb-4">Importar Masivo</h3>
            <div class="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center" @dragover.prevent @drop.prevent="handleDrop">
                <p class="text-gray-400 mb-2">Arrastra tu archivo CSV, TXT o XLSX aquí</p>
                <input type="file" ref="fileInput" @change="handleFileSelect" class="hidden" accept=".csv,.txt,.xlsx" />
                 <button @click="$refs.fileInput.click()" class="text-primary hover:underline text-sm">o selecciona un archivo</button>
            </div>
             <p v-if="importStatus" class="mt-4 text-sm" :class="importError ? 'text-red-400' : 'text-green-400'">{{ importStatus }}</p>
             
             <div class="flex justify-end mt-6">
                <button @click="showImportModal = false" class="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white">Cerrar</button>
             </div>
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../apiConfig';

const companies = ref([]);
const showModal = ref(false);
const showImportModal = ref(false);
const form = ref({ ruc: '', razon_social: '', usuario_sol: '', clave_sol: '' });
const importStatus = ref('');
const importError = ref(false);

const fetchCompanies = async () => {
    try {
        const res = await api.get('/empresas/');
        companies.value = res.data;
    } catch (e) {
        console.error("Error loading companies", e);
    }
};

const openModal = () => {
    form.value = { ruc: '', razon_social: '', usuario_sol: '', clave_sol: '' };
    showModal.value = true;
};

const saveCompany = async () => {
    try {
        await api.post('/empresas/', form.value);
        showModal.value = false;
        fetchCompanies();
    } catch (e) {
        alert("Error guardando empresa: " + (e.response?.data?.detail || e.message));
    }
};

const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if(file) await uploadFile(file);
};

const handleDrop = async (e) => {
    const file = e.dataTransfer.files[0];
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
        case 'ERROR': return 'bg-red-900/30 text-red-400 border-red-900';
        default: return 'bg-gray-800 text-gray-400 border-gray-700';
    }
};

onMounted(fetchCompanies);
</script>
