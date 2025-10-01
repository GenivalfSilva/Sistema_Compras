export const STATUS_TRANSITIONS: Record<string, string[]> = {
  'Solicitação': ['Requisição'],
  'Requisição': ['Suprimentos'],
  'Suprimentos': ['Em Cotação'],
  'Em Cotação': ['Pedido de Compras'],
  'Pedido de Compras': ['Aguardando Aprovação'],
  'Aguardando Aprovação': ['Aprovado', 'Reprovado'],
  'Aprovado': ['Compra feita'],
  'Compra feita': ['Aguardando Entrega'],
  'Aguardando Entrega': ['Pedido Finalizado'],
};

export function getAllowedTransitions(current: string): string[] {
  return STATUS_TRANSITIONS[current] || [];
}
