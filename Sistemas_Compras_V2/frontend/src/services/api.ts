import axios from 'axios';

const api = axios.create({
  baseURL: (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
});

api.interceptors.request.use((config: any) => {
  const token = localStorage.getItem('access');
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res: any) => res,
  (err: any) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem('access');
      localStorage.removeItem('refresh');
      if (location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

export default api;
