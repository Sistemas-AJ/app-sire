import axios from 'axios';

// En producción (docker/nginx): el frontend y el backend viven bajo el mismo host (IP del servidor)
// Nginx manda /api -> backend:8654
export const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' }
});

// Request Interceptor: Attach Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => Promise.reject(error));

// Response Interceptor: Handle 401
api.interceptors.response.use(response => response, error => {
  if (error.response && error.response.status === 401) {
    localStorage.removeItem('token');
    // Force redirect to login
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }
  return Promise.reject(error);
});

export default api;
