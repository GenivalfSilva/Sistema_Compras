"""
Wrapper para integrar auditoria nas ações do Admin
Intercepta e registra todas as ações administrativas
"""

import streamlit as st
from audit_logger import log_admin_action, show_admin_warning

def with_audit_log(acao: str, modulo: str):
    """
    Decorator para adicionar auditoria a funções do Admin
    
    Args:
        acao: Tipo de ação (ex: "CRIAR_SOLICITACAO")
        modulo: Módulo da ação (ex: "SOLICITACOES")
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Só registra se for Admin
            if st.session_state.get('perfil') == 'Admin':
                # Extrai detalhes dos argumentos se possível
                detalhes = {}
                if args and isinstance(args[0], dict):
                    # Primeiro argumento é geralmente o data dict
                    data = args[0]
                    if 'descricao' in data:
                        detalhes['descricao'] = data['descricao'][:100]  # Limita tamanho
                    if 'prioridade' in data:
                        detalhes['prioridade'] = data['prioridade']
                
                # Registra a ação
                log_admin_action(acao, modulo, detalhes)
            
            # Executa a função original
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def audit_admin_action(acao: str, modulo: str, detalhes: dict = None, solicitacao_id: int = None):
    """
    Função para registrar ações específicas do Admin
    Usar em pontos críticos das operações
    """
    if st.session_state.get('perfil') == 'Admin':
        log_admin_action(acao, modulo, detalhes, solicitacao_id)

# Exemplos de uso das funções de auditoria
AUDIT_ACTIONS = {
    # Solicitações
    'CRIAR_SOLICITACAO': 'Criar nova solicitação',
    'EDITAR_SOLICITACAO': 'Editar solicitação existente',
    'EXCLUIR_SOLICITACAO': 'Excluir solicitação',
    
    # Requisições
    'CRIAR_REQUISICAO': 'Criar nova requisição',
    'PROCESSAR_REQUISICAO': 'Processar requisição',
    
    # Suprimentos
    'MOVER_ETAPA': 'Mover solicitação entre etapas',
    'CRIAR_PEDIDO': 'Criar pedido de compras',
    'ATUALIZAR_COTACAO': 'Atualizar cotação',
    
    # Aprovações
    'APROVAR_PEDIDO': 'Aprovar pedido de compras',
    'REPROVAR_PEDIDO': 'Reprovar pedido de compras',
    
    # Administração
    'CRIAR_USUARIO': 'Criar novo usuário',
    'EDITAR_USUARIO': 'Editar usuário existente',
    'EXCLUIR_USUARIO': 'Excluir usuário',
    'ALTERAR_CONFIGURACAO': 'Alterar configuração do sistema',
    
    # Catálogo
    'ADICIONAR_PRODUTO': 'Adicionar produto ao catálogo',
    'EDITAR_PRODUTO': 'Editar produto do catálogo',
    'REMOVER_PRODUTO': 'Remover produto do catálogo'
}

AUDIT_MODULES = {
    'SOLICITACOES': 'Módulo de Solicitações',
    'REQUISICOES': 'Módulo de Requisições', 
    'SUPRIMENTOS': 'Módulo de Suprimentos',
    'APROVACOES': 'Módulo de Aprovações',
    'USUARIOS': 'Módulo de Usuários',
    'CONFIGURACOES': 'Módulo de Configurações',
    'CATALOGO': 'Módulo de Catálogo'
}
