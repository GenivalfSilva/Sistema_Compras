"""
Módulo para funcionalidades do perfil Admin
Contém: Todas as funcionalidades + Configurações SLA, Gerenciar Usuários
"""

import streamlit as st
from typing import Dict, List

def get_profile_options() -> List[str]:
    """Retorna as opções de menu disponíveis para o perfil Admin"""
    return [
        "📝 Nova Solicitação",
        "📑 Requisição (Estoque)",
        "🔄 Mover para Próxima Etapa",
        "📱 Aprovações",
        "📊 Dashboard SLA",
        "📚 Histórico por Etapa",
        "📦 Catálogo de Produtos",
        "⚙️ Configurações SLA",
        "👥 Gerenciar Usuários"
    ]

def handle_profile_option(opcao: str, data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Roteador principal para as opções do perfil Admin"""
    if opcao == "📝 Nova Solicitação":
        from .solicitante_nova import nova_solicitacao
        nova_solicitacao(data, usuario, USE_DATABASE)
    elif opcao == "📑 Requisição (Estoque)":
        from .suprimentos_requisicao import requisicao_estoque
        requisicao_estoque(data, usuario, USE_DATABASE)
    elif opcao == "🔄 Mover para Próxima Etapa":
        from .suprimentos_mover import mover_etapa
        mover_etapa(data, usuario, USE_DATABASE)
    elif opcao == "📱 Aprovações":
        from .diretoria_aprovacoes import aprovacoes
        aprovacoes(data, usuario, USE_DATABASE)
    elif opcao == "📊 Dashboard SLA":
        from .common_dashboard import dashboard_sla
        dashboard_sla(data, usuario)
    elif opcao == "📚 Histórico por Etapa":
        from .common_historico import historico_por_etapa
        historico_por_etapa(data, usuario)
    elif opcao == "📦 Catálogo de Produtos":
        from .suprimentos_catalogo import catalogo_produtos
        catalogo_produtos(data, usuario, USE_DATABASE)
    elif opcao == "⚙️ Configurações SLA":
        from .admin_configuracoes import configuracoes_sla
        configuracoes_sla(data, usuario, USE_DATABASE)
    elif opcao == "👥 Gerenciar Usuários":
        from .admin_usuarios import gerenciar_usuarios
        gerenciar_usuarios(data, usuario, USE_DATABASE)
    else:
        st.error("❌ Opção não implementada ainda.")
