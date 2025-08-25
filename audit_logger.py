"""
Sistema de Auditoria para Ações do Admin
Registra todas as ações administrativas para controle e rastreabilidade
"""

import streamlit as st
from database_local import get_local_database
from datetime import datetime
import json

class AdminAuditLogger:
    """Classe para logging de ações do Admin"""
    
    def __init__(self):
        self.db = get_local_database()
    
    def log_action(self, acao: str, modulo: str, detalhes: dict = None, solicitacao_id: int = None):
        """
        Registra uma ação do Admin
        
        Args:
            acao: Tipo de ação (ex: "CRIAR_SOLICITACAO", "APROVAR_PEDIDO", "MOVER_ETAPA")
            modulo: Módulo onde a ação ocorreu (ex: "SOLICITACOES", "APROVACOES", "USUARIOS")
            detalhes: Detalhes adicionais da ação
            solicitacao_id: ID da solicitação afetada (se aplicável)
        """
        try:
            # Pega informações do usuário da sessão
            usuario = st.session_state.get('username', 'admin')
            
            # Converte detalhes para JSON se fornecido
            detalhes_json = json.dumps(detalhes, ensure_ascii=False) if detalhes else None
            
            # Pega IP do usuário (simulado - Streamlit não expõe IP real)
            ip_address = st.session_state.get('client_ip', 'localhost')
            
            # Registra no banco
            success = self.db.log_admin_action(
                usuario=usuario,
                acao=acao,
                modulo=modulo,
                detalhes=detalhes_json,
                solicitacao_id=solicitacao_id,
                ip_address=ip_address
            )
            
            if success:
                # Mostra alerta discreto na interface
                st.toast(f"🔍 Ação registrada: {acao}", icon="📝")
            
            return success
            
        except Exception as e:
            st.error(f"❌ Erro ao registrar auditoria: {e}")
            return False
    
    def get_logs(self, limit: int = 50):
        """Recupera logs de auditoria"""
        return self.db.get_admin_audit_logs(limit=limit)

# Instância global do logger
audit_logger = AdminAuditLogger()

def log_admin_action(acao: str, modulo: str, detalhes: dict = None, solicitacao_id: int = None):
    """
    Função utilitária para logging rápido
    
    Exemplos de uso:
    - log_admin_action("CRIAR_SOLICITACAO", "SOLICITACOES", {"descricao": "Material de escritório"})
    - log_admin_action("APROVAR_PEDIDO", "APROVACOES", {"valor": 1500.00}, solicitacao_id=123)
    - log_admin_action("MOVER_ETAPA", "SUPRIMENTOS", {"de": "Cotação", "para": "Pedido"}, solicitacao_id=456)
    """
    return audit_logger.log_action(acao, modulo, detalhes, solicitacao_id)

def show_admin_warning():
    """Mostra aviso de auditoria para Admin"""
    if st.session_state.get('perfil') == 'Admin':
        st.info("🔍 **Modo Admin Ativo** - Todas as suas ações estão sendo registradas para auditoria.")
