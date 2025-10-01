import api from './api';

export interface Configuracao {
  id: number;
  chave: string;
  valor: string;
  tipo?: string;
  descricao?: string;
  updated_at?: string;
  valor_typed?: any;
}

export interface ConfiguracaoSLA {
  id: number;
  departamento: string;
  sla_urgente: number;
  sla_alta: number;
  sla_normal: number;
  sla_baixa: number;
  ativo: boolean;
}

export interface LimiteAprovacao {
  id: number;
  nome: string;
  valor_minimo: number;
  valor_maximo: number;
  aprovador: string; // Ex.: 'Gerência', 'Diretoria'
  ativo: boolean;
}

export const ConfiguracoesAPI = {
  // Configurações gerais
  async listConfigs() {
    const { data } = await api.get<Configuracao[]>('/configuracoes/');
    return data;
  },
  async updateConfig(id: number, partial: Partial<Configuracao>) {
    const { data } = await api.put<Configuracao>(`/configuracoes/${id}/`, partial);
    return data;
  },
  async bulkUpdate(configs: Array<{ chave: string; valor: string; tipo?: string; descricao?: string }>) {
    const { data } = await api.post('/configuracoes/bulk-update/', { configuracoes: configs });
    return data;
  },

  // SLA
  async listSLA() {
    const { data } = await api.get<ConfiguracaoSLA[]>('/configuracoes/sla/');
    return data;
  },
  async createSLA(payload: Omit<ConfiguracaoSLA, 'id'>) {
    const { data } = await api.post<ConfiguracaoSLA>('/configuracoes/sla/', payload);
    return data;
  },
  async updateSLA(id: number, partial: Partial<ConfiguracaoSLA>) {
    const { data } = await api.put<ConfiguracaoSLA>(`/configuracoes/sla/${id}/`, partial);
    return data;
  },

  // Limites
  async listLimits() {
    const { data } = await api.get<LimiteAprovacao[]>('/configuracoes/limites/');
    return data;
  },
  async createLimit(payload: Omit<LimiteAprovacao, 'id'>) {
    const { data } = await api.post<LimiteAprovacao>('/configuracoes/limites/', payload);
    return data;
  },
  async updateLimit(id: number, partial: Partial<LimiteAprovacao>) {
    const { data } = await api.put<LimiteAprovacao>(`/configuracoes/limites/${id}/`, partial);
    return data;
  },
};
