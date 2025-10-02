import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import api from '../../services/api';
import type { Tokens, UserProfile } from './types';
import { authStorage } from './authStorage';

export interface AuthState {
  tokens: Tokens | null;
  profile: UserProfile | null;
  loading: boolean;
  error: string | null;
}

// Inicializa o estado com os dados do localStorage
const initialState: AuthState = {
  tokens: authStorage.getTokens(),
  profile: authStorage.getProfile(),
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (payload: { username: string; password: string }, { rejectWithValue }) => {
    try {
      const res = await api.post('/usuarios/auth/login/', payload);
      const tokens: Tokens = res.data;
      
      // Salva os tokens no localStorage usando authStorage
      authStorage.saveTokens(tokens);

      const profRes = await api.get('/usuarios/auth/profile/');
      const profile: UserProfile = profRes.data;
      
      // Salva o perfil no localStorage
      authStorage.saveProfile(profile);
      
      return { tokens, profile };
    } catch (err: any) {
      return rejectWithValue(err?.response?.data || 'Login failed');
    }
  }
);

export const fetchProfile = createAsyncThunk(
  'auth/fetchProfile',
  async (_, { rejectWithValue }) => {
    try {
      console.log('Carregando perfil do usuário...');
      const profRes = await api.get('/usuarios/auth/profile/');
      const profile: UserProfile = profRes.data;
      
      // Salva o perfil no localStorage
      authStorage.saveProfile(profile);
      
      return profile;
    } catch (err: any) {
      // Se o erro for 401, não é necessário mostrar mensagem de erro
      // pois o interceptor já vai redirecionar para o login
      if (err?.response?.status === 401) {
        // Limpa os dados de autenticação
        authStorage.clearAuth();
        return rejectWithValue('Sessão expirada');
      }
      return rejectWithValue(err?.response?.data?.detail || err?.message || 'Falha ao carregar perfil');
    }
  }
);

export const logout = createAsyncThunk('auth/logout', async () => {
  try {
    // Obter o token de refresh do authStorage
    const tokens = authStorage.getTokens();
    if (tokens?.refresh) {
      // Enviar o token no formato correto esperado pelo backend
      await api.post('/usuarios/auth/logout/', { refresh_token: tokens.refresh });
    }
  } catch (error) {
    console.error('Erro ao fazer logout:', error);
  }
  
  // Limpa todos os dados de autenticação independentemente do resultado
  authStorage.clearAuth();
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setTokens(state, action: PayloadAction<Tokens | null>) {
      state.tokens = action.payload;
      authStorage.saveTokens(action.payload);
    },
    setProfile(state, action: PayloadAction<UserProfile | null>) {
      state.profile = action.payload;
      authStorage.saveProfile(action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.tokens = action.payload.tokens;
        state.profile = action.payload.profile;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = (action.payload as string) || action.error.message || 'Falha no login';
      })
      .addCase(fetchProfile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.profile = action.payload as UserProfile;
      })
      .addCase(fetchProfile.rejected, (state, action) => {
        state.loading = false;
        // não derruba a sessão; apenas mantém o profile nulo
        state.error = (action.payload as string) || action.error.message || null;
      })
      .addCase(logout.fulfilled, (state) => {
        state.tokens = null;
        state.profile = null;
      });
  },
});

export const { setTokens, setProfile } = authSlice.actions;
export default authSlice.reducer;
