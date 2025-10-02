"""
Módulo para funcionalidades do perfil Estoque
Contém: Gestão de Requisições, Dashboard SLA, Histórico por Etapa
"""

import streamlit as st
from typing import Dict, List

def get_profile_options() -> List[str]:
    """Retorna as opções de menu disponíveis para o perfil Estoque"""
    return [
        "📋 Gestão de Requisições",
        "📊 Dashboard SLA",
        "📚 Histórico por Etapa"
    ]

def handle_profile_option(opcao: str, data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Roteador principal para as opções do perfil Estoque"""
    if opcao == "📋 Gestão de Requisições":
        from .estoque_requisicoes import show_estoque_requisicoes
        show_estoque_requisicoes()
    elif opcao == "📊 Dashboard SLA":
        from .common_dashboard import dashboard_sla
        dashboard_sla(data, usuario)
    elif opcao == "📚 Histórico por Etapa":
        from .common_historico import historico_por_etapa
        historico_por_etapa(data, usuario)
    else:
        st.error("❌ Opção não implementada ainda.")
