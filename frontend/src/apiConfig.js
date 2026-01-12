import axios from 'axios';

// En producción (docker/nginx): el frontend y el backend viven bajo el mismo host (IP del servidor)
// Nginx manda /api -> backend:8654
export const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

export default api;
