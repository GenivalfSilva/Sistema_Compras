import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import api from '../../services/api';
import type { Tokens, UserProfile } from './types';

export interface AuthState {
  tokens: Tokens | null;
  profile: UserProfile | null;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  tokens: null,
  profile: null,
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (payload: { username: string; password: string }, { rejectWithValue }) => {
    try {
      const res = await api.post('/usuarios/auth/login/', payload);
      const tokens: Tokens = res.data;
      localStorage.setItem('access', tokens.access);
      if (tokens.refresh) localStorage.setItem('refresh', tokens.refresh);

      const profRes = await api.get('/usuarios/auth/profile/');
      const profile: UserProfile = profRes.data;
      return { tokens, profile };
    } catch (err: any) {
      return rejectWithValue(err?.response?.data || 'Login failed');
    }
  }
);

export const logout = createAsyncThunk('auth/logout', async () => {
  try {
    const refresh = localStorage.getItem('refresh');
    await api.post('/usuarios/auth/logout/', { refresh });
  } catch {}
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setTokens(state, action: PayloadAction<Tokens | null>) {
      state.tokens = action.payload;
    },
    setProfile(state, action: PayloadAction<UserProfile | null>) {
      state.profile = action.payload;
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
      .addCase(logout.fulfilled, (state) => {
        state.tokens = null;
        state.profile = null;
      });
  },
});

export const { setTokens, setProfile } = authSlice.actions;
export default authSlice.reducer;
