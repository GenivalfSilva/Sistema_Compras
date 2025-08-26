"""
Módulo para funcionalidades do perfil Suprimentos
Contém: Requisição (Estoque), Mover para Próxima Etapa, Dashboard SLA, Histórico por Etapa, Catálogo de Produtos
"""

import streamlit as st
from typing import Dict, List

def get_profile_options() -> List[str]:
    """Retorna as opções de menu disponíveis para o perfil Suprimentos"""
    return [
        "🏭 Processar Requisições",
        "💰 Gerenciar Cotações",
        "📑 Requisição (Estoque) - Legado",
        "🔄 Mover para Próxima Etapa",
        "📊 Dashboard SLA",
        "📚 Histórico por Etapa",
        "📦 Catálogo de Produtos"
    ]

def handle_profile_option(opcao: str, data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Roteador principal para as opções do perfil Suprimentos"""
    if opcao == "🏭 Processar Requisições":
        from .suprimentos_requisicoes import show_suprimentos_requisicoes
        show_suprimentos_requisicoes()
    elif opcao == "💰 Gerenciar Cotações":
        from .suprimentos_cotacoes import gerenciar_cotacoes
        gerenciar_cotacoes(data, usuario, USE_DATABASE)
    elif opcao == "📑 Requisição (Estoque) - Legado":
        from .suprimentos_requisicao import requisicao_estoque
        requisicao_estoque(data, usuario, USE_DATABASE)
    elif opcao == "🔄 Mover para Próxima Etapa":
        from .suprimentos_mover import mover_etapa
        mover_etapa(data, usuario, USE_DATABASE)
    elif opcao == "📊 Dashboard SLA":
        from .common_dashboard import dashboard_sla
        dashboard_sla(data, usuario)
    elif opcao == "📚 Histórico por Etapa":
        from .common_historico import historico_por_etapa
        historico_por_etapa(data, usuario)
    elif opcao == "📦 Catálogo de Produtos":
        from .suprimentos_catalogo import catalogo_produtos
        catalogo_produtos(data, usuario, USE_DATABASE)
    else:
        st.error("❌ Opção não implementada ainda.")
