import axios from 'axios';
import { authStorage } from '../features/auth/authStorage';

const api = axios.create({
  baseURL: (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
});

// Flag para evitar múltiplas tentativas de refresh simultâneas
let isRefreshing = false;
// Fila de requisições que aguardam o refresh do token
let failedQueue: { resolve: (value: unknown) => void; reject: (reason?: any) => void }[] = [];

// Função para processar a fila de requisições após o refresh do token
const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

// Interceptor para adicionar o token de acesso às requisições
api.interceptors.request.use((config: any) => {
  const tokens = authStorage.getTokens();
  if (tokens?.access) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

// Interceptor para tratar erros de resposta
api.interceptors.response.use(
  (res: any) => res,
  async (err: any) => {
    const originalRequest = err.config;
    
    // Se o erro for 401 (Não autorizado) e não for uma requisição de refresh
    if (err?.response?.status === 401 && !originalRequest._retry) {
      // Verifica se a URL é de login ou refresh
      const isAuthUrl = originalRequest.url?.includes('/auth/login/') || 
                       originalRequest.url?.includes('/auth/refresh/');
      
      // Se for uma URL de autenticação, não tenta refresh
      if (isAuthUrl) {
        return Promise.reject(err);
      }
      
      // Se já estiver tentando fazer refresh, adiciona à fila
      if (isRefreshing) {
        try {
          // Espera o refresh do token
          await new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });
          // Refaz a requisição original com o novo token
          const token = localStorage.getItem('access');
          originalRequest.headers['Authorization'] = `Bearer ${token}`;
          return axios(originalRequest);
        } catch (error) {
          return Promise.reject(error);
        }
      }
      
      // Marca a requisição como retry para evitar loop infinito
      originalRequest._retry = true;
      isRefreshing = true;
      
      // Tenta fazer refresh do token
      const tokens = authStorage.getTokens();
      const refreshToken = tokens?.refresh || localStorage.getItem('refresh');
      
      if (!refreshToken) {
        // Se não tiver refresh token, redireciona para login
        processQueue(new Error('No refresh token'));
        authStorage.clearAuth();
        if (location.pathname !== '/login') {
          console.log('Redirecionando para login (sem refresh token)');
          window.location.href = '/login';
        }
        return Promise.reject(err);
      }
      
      try {
        console.log('Tentando renovar o token...');
        // Tenta renovar o token
        const res = await axios.post(
          `${api.defaults.baseURL}/usuarios/auth/refresh/`,
          { refresh_token: refreshToken }
        );
        
        const { access } = res.data;
        // Atualiza apenas o token de acesso, mantendo o refresh token
        const tokens = authStorage.getTokens() || { access: '' };
        authStorage.saveTokens({ ...tokens, access });
        console.log('Token renovado com sucesso!');
        
        // Atualiza o token na requisição original
        originalRequest.headers['Authorization'] = `Bearer ${access}`;
        
        // Processa a fila de requisições pendentes
        processQueue(null, access);
        
        // Refaz a requisição original
        return axios(originalRequest);
      } catch (refreshError: any) {
        // Se falhar o refresh, limpa tudo e redireciona para login
        console.error('Falha ao renovar token:', refreshError?.message);
        processQueue(refreshError);
        authStorage.clearAuth();
        
        // Redireciona para login apenas se não estiver já na página de login
        if (location.pathname !== '/login') {
          console.log('Redirecionando para login (falha no refresh)');
          // Usar setTimeout para evitar problemas com o React Router
          setTimeout(() => {
            window.location.href = '/login';
          }, 100);
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    return Promise.reject(err);
  }
);

export default api;
