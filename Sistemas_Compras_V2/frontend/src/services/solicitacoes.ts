import api from './api';

// Tipos básicos
export interface SolicitacaoListItem {
  id: number;
  numero_solicitacao_estoque: number;
  solicitante: string;
  departamento: string;
  prioridade: string;
  status: string;
  descricao: string;
  valor_estimado?: number;
  valor_final?: number;
  created_at: string;
  status_display?: string;
  prioridade_display?: string;
  departamento_display?: string;
}

export interface Cotacao {
  id?: number;
  solicitacao_id: number;
  fornecedor: string;
  valor_unitario: number;
  valor_total: number;
  prazo_entrega: number; // em dias
  condicoes_pagamento: string;
  observacoes?: string;
  selecionada?: boolean;
  data_cotacao?: string;
}

export interface SolicitacaoDetail extends SolicitacaoListItem {
  local_aplicacao?: string;
  observacoes?: string;
  numero_requisicao?: string;
  data_requisicao?: string;
  responsavel_suprimentos?: string;
  numero_pedido_compras?: string;
  fornecedor_recomendado?: string;
  fornecedor_final?: string;
  data_entrega_prevista?: string;
  data_entrega_real?: string;
  nota_fiscal?: string;
  entrega_conforme?: boolean;
  responsavel_recebimento?: string;
  justificativa?: string;
  tipo_solicitacao?: string;
  itens?: any;
  cotacoes?: Cotacao[];
  aprovacoes?: any;
  anexos_requisicao?: any;
  historico_etapas?: any;
  sla_info?: any;
  proxima_acao?: string | null;
}

export interface CreateSolicitacaoPayload {
  departamento: string;
  prioridade: string;
  descricao: string;
  local_aplicacao?: string;
  observacoes?: string;
  valor_estimado?: number;
  itens?: any;
  anexos_requisicao?: any;
}

export interface StatusUpdatePayload {
  novo_status: string;
  observacoes?: string;
}

export interface ApprovalPayload {
  acao: 'aprovar' | 'reprovar';
  observacoes?: string;
}

export interface DashboardResumo {
  total: number;
  pendentes: number;
  aprovadas: number;
  reprovadas: number;
  finalizadas: number;
}

export interface DashboardSLA {
  vencidas: number;
  proximo_vencimento: number;
  ok: number;
}

export interface SolicitacoesDashboard {
  resumo: DashboardResumo;
  sla: DashboardSLA;
  por_status: Record<string, number>;
  por_prioridade: Record<string, number>;
  solicitacoes_recentes: SolicitacaoListItem[];
}

export interface CotacaoPayload {
  fornecedor: string;
  valor_unitario: number;
  valor_total: number;
  prazo_entrega: number;
  condicoes_pagamento: string;
  observacoes?: string;
  selecionada?: boolean;
}

export const SolicitacoesAPI = {
  async list(params?: any) {
    const { data } = await api.get<any>('/solicitacoes/', { params });
    // Se houver paginação global no DRF, virá como { count, next, previous, results }
    if (Array.isArray(data)) return data as SolicitacaoListItem[];
    if (data && Array.isArray(data.results)) return data.results as SolicitacaoListItem[];
    return [] as SolicitacaoListItem[];
  },
  async dashboard() {
    const { data } = await api.get<SolicitacoesDashboard>('/solicitacoes/dashboard/');
    return data;
  },
  async get(id: number) {
    const { data } = await api.get<SolicitacaoDetail>(`/solicitacoes/${id}/`);
    return data;
  },
  async create(payload: CreateSolicitacaoPayload) {
    const { data } = await api.post<SolicitacaoDetail>('/solicitacoes/', payload);
    return data;
  },
  async update(id: number, partial: Partial<SolicitacaoDetail>) {
    const { data } = await api.patch<SolicitacaoDetail>(`/solicitacoes/${id}/`, partial);
    return data;
  },
  async updateStatus(id: number, payload: StatusUpdatePayload) {
    const { data } = await api.post(`/solicitacoes/${id}/update-status/`, payload);
    return data;
  },
  async approval(id: number, payload: ApprovalPayload) {
    const { data } = await api.post(`/solicitacoes/${id}/approval/`, payload);
    return data;
  },
  async addCotacao(solicitacaoId: number, cotacao: CotacaoPayload) {
    const { data } = await api.post(`/solicitacoes/${solicitacaoId}/cotacoes/`, cotacao);
    return data;
  },
  async getCotacoes(solicitacaoId: number) {
    const { data } = await api.get(`/solicitacoes/${solicitacaoId}/cotacoes/`);
    return data as Cotacao[];
  },
  async selectCotacao(solicitacaoId: number, cotacaoId: number) {
    const { data } = await api.post(`/solicitacoes/${solicitacaoId}/cotacoes/${cotacaoId}/select/`);
    return data;
  },
};
