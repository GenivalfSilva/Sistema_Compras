"""
Módulo para funcionalidades do perfil Solicitante
Contém: Nova Solicitação, Dashboard SLA, Histórico por Etapa
"""

import streamlit as st
from typing import Dict, List

def get_profile_options() -> List[str]:
    """Retorna as opções de menu disponíveis para o perfil Solicitante"""
    return [
        "📝 Nova Solicitação",
        "📋 Minhas Solicitações",
        "📊 Dashboard SLA", 
        "📚 Histórico por Etapa"
    ]

def handle_profile_option(opcao: str, data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Roteador principal para as opções do perfil Solicitante"""
    if opcao == "📝 Nova Solicitação":
        from .solicitante_nova import nova_solicitacao
        nova_solicitacao(data, usuario, USE_DATABASE)
    elif opcao == "📋 Minhas Solicitações":
        from .solicitante_minhas import minhas_solicitacoes
        minhas_solicitacoes(data, usuario, USE_DATABASE)
    elif opcao == "📊 Dashboard SLA":
        from .common_dashboard import dashboard_sla
        dashboard_sla(data, usuario)
    elif opcao == "📚 Histórico por Etapa":
        from .common_historico import historico_por_etapa
        historico_por_etapa(data, usuario)
    else:
        st.error("❌ Opção não implementada ainda.")
