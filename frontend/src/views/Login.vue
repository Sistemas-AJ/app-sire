<template>
  <div class="min-h-screen flex items-center justify-center bg-dark text-white relative overflow-hidden">
    <!-- Abstract Background -->
    <div class="absolute top-0 left-0 w-full h-full opacity-20 pointer-events-none">
        <div class="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary rounded-full blur-[150px]"></div>
        <div class="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-600 rounded-full blur-[150px]"></div>
    </div>

    <div class="relative z-10 w-full max-w-md p-8 bg-dark-lighter border border-gray-800 rounded-2xl shadow-2xl backdrop-blur-xl">
      <div class="flex flex-col items-center mb-8">
        <!-- Logo -->
        <h1 class="text-4xl font-extrabold tracking-tighter bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent mb-2">
            SIRE FLASH
        </h1>
        <p class="text-gray-400 text-sm">Ingreso al Sistema</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-400 mb-1">Usuario</label>
          <input 
            type="text" 
            v-model="username" 
            required
            class="w-full bg-dark border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-primary transition-colors"
            placeholder="admin"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-400 mb-1">Contraseña</label>
          <input 
            type="password" 
            v-model="password" 
            required
            class="w-full bg-dark border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-primary transition-colors"
            placeholder="••••••••"
          />
        </div>

        <div v-if="errorMsg" class="p-3 rounded bg-red-900/30 border border-red-800 text-red-300 text-sm text-center">
            {{ errorMsg }}
        </div>

        <button 
          type="submit" 
          :disabled="isLoading"
          class="w-full bg-primary hover:bg-blue-600 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-blue-600/20 transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
        >
          <span v-if="isLoading">Verificando...</span>
          <span v-else>Iniciar Sesión</span>
        </button>
      </form>
      
      <div class="mt-8 text-center text-xs text-gray-600">
        &copy; 2026 Sire Flash System
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../apiConfig';

const router = useRouter();
const username = ref('');
const password = ref('');
const isLoading = ref(false);
const errorMsg = ref('');

const handleLogin = async () => {
    isLoading.value = true;
    errorMsg.value = '';
    
    try {
        const payload = {
            username: username.value,
            password: password.value
        };
        
        const res = await api.post('/auth/login', payload);
        
        if (res.data.ok && res.data.token) {
            localStorage.setItem('token', res.data.token);
            // Optional: Store user info if needed
            // localStorage.setItem('user', JSON.stringify(res.data.user)); 
            router.push('/dashboard');
        } else {
            errorMsg.value = 'Credenciales inválidas o respuesta inesperada.';
        }
    } catch (e) {
        console.error(e);
        if (e.response && e.response.status === 401) {
             errorMsg.value = 'Usuario o contraseña incorrectos.';
        } else {
             errorMsg.value = 'Error de conexión con el servidor.';
        }
    } finally {
        isLoading.value = false;
    }
};
</script>
