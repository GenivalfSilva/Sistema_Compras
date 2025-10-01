import api from './api';

export interface AuditoriaAdminLog {
  id: number;
  usuario: string;
  acao: string;
  acao_display?: string;
  modulo: string;
  detalhes: string; // JSON string
  solicitacao_id?: number | null;
  ip_address?: string;
  timestamp: string;
}

export interface HistoricoLoginLog {
  id: number;
  usuario?: number | null;
  usuario_nome?: string | null;
  username_tentativa: string;
  status: string;
  status_display?: string;
  ip_address?: string;
  user_agent?: string;
  motivo_falha?: string;
  sessao_id?: string;
  timestamp: string;
}

export const AuditoriaAPI = {
  async listAdmin(params?: any) {
    const { data } = await api.get<AuditoriaAdminLog[]>('/auditoria/admin/', { params });
    return data;
  },
  async listLogin(params?: any) {
    const { data } = await api.get<HistoricoLoginLog[]>('/auditoria/login/', { params });
    return data;
  },
};
