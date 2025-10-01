import api from './api';

export interface UsuarioV1 {
  id: number;
  username: string;
  nome: string;
  perfil: string;
  departamento: string;
  created_at?: string;
}

export interface UsuarioDjango {
  id: number;
  username: string;
  email?: string;
  nome?: string;
  perfil?: string;
  departamento?: string;
  is_active?: boolean;
}

export const UsuariosAPI = {
  async listV1() {
    const { data } = await api.get<UsuarioV1[]>('/usuarios/v1/');
    return data;
  },
  async listDjango() {
    const { data } = await api.get<UsuarioDjango[]>('/usuarios/');
    return data;
  },
};
