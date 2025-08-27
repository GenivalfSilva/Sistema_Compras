"""
Módulo para funcionalidades do perfil Admin
Contém: TODAS as funcionalidades de TODOS os perfis + Configurações SLA, Gerenciar Usuários
"""

import streamlit as st
from typing import Dict, List

def get_profile_options() -> List[str]:
    """Retorna as opções de menu disponíveis para o perfil Admin - ACESSO COMPLETO A TODOS OS PERFIS"""
    return [
        # === FUNCIONALIDADES DO SOLICITANTE ===
        "📝 Nova Solicitação",
        "📋 Minhas Solicitações",
        
        # === FUNCIONALIDADES DO ESTOQUE ===
        "📋 Gestão de Requisições (Estoque)",
        
        # === FUNCIONALIDADES DO SUPRIMENTOS ===
        "🏭 Processar Requisições (Suprimentos)",
        "💰 Gerenciar Cotações (Suprimentos)",
        "📑 Requisição (Estoque) - Legado",
        "🔄 Mover para Próxima Etapa (Suprimentos)",
        "📦 Catálogo de Produtos (Suprimentos)",
        
        # === FUNCIONALIDADES DA DIRETORIA ===
        "📱 Aprovações (Diretoria)",
        
        # === FUNCIONALIDADES COMUNS ===
        "📊 Dashboard SLA",
        "📚 Histórico por Etapa",
        
        # === FUNCIONALIDADES EXCLUSIVAS DO ADMIN ===
        "⚙️ Configurações SLA",
        "🔍 Auditoria",
        "👥 Gerenciar Usuários",
        
        # === ACESSO DIRETO A PERFIS (MODO ADMIN) ===
        "🎭 Modo Solicitante",
        "🎭 Modo Estoque", 
        "🎭 Modo Suprimentos",
        "🎭 Modo Diretoria",
        
        # === PAINEL ADMINISTRATIVO AVANÇADO ===
        "🚀 Painel Administrativo Completo"
    ]

def handle_profile_option(opcao: str, data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Roteador principal para as opções do perfil Admin - ACESSO COMPLETO A TODOS OS PERFIS"""
    
    # === FUNCIONALIDADES DO SOLICITANTE ===
    if opcao == "📝 Nova Solicitação":
        from .solicitante_nova import nova_solicitacao
        nova_solicitacao(data, usuario, USE_DATABASE)
    elif opcao == "📋 Minhas Solicitações":
        from .solicitante_minhas import minhas_solicitacoes
        minhas_solicitacoes(data, usuario, USE_DATABASE)
    
    # === FUNCIONALIDADES DO ESTOQUE ===
    elif opcao == "📋 Gestão de Requisições (Estoque)":
        from .estoque_requisicoes import show_estoque_requisicoes
        show_estoque_requisicoes()
    
    # === FUNCIONALIDADES DO SUPRIMENTOS ===
    elif opcao == "🏭 Processar Requisições (Suprimentos)":
        from .suprimentos_requisicoes import show_suprimentos_requisicoes
        show_suprimentos_requisicoes()
    elif opcao == "💰 Gerenciar Cotações (Suprimentos)":
        from .suprimentos_cotacoes import gerenciar_cotacoes
        gerenciar_cotacoes(data, usuario, USE_DATABASE)
    elif opcao == "📑 Requisição (Estoque) - Legado":
        from .suprimentos_requisicao import requisicao_estoque
        requisicao_estoque(data, usuario, USE_DATABASE)
    elif opcao == "🔄 Mover para Próxima Etapa (Suprimentos)":
        from .suprimentos_mover import mover_etapa
        mover_etapa(data, usuario, USE_DATABASE)
    elif opcao == "📦 Catálogo de Produtos (Suprimentos)":
        from .suprimentos_catalogo import catalogo_produtos
        catalogo_produtos(data, usuario, USE_DATABASE)
    
    # === FUNCIONALIDADES DA DIRETORIA ===
    elif opcao == "📱 Aprovações (Diretoria)":
        from .diretoria_aprovacoes import aprovacoes
        aprovacoes(data, usuario, USE_DATABASE)
    
    # === FUNCIONALIDADES COMUNS ===
    elif opcao == "📊 Dashboard SLA":
        from .common_dashboard import dashboard_sla
        dashboard_sla(data, usuario)
    elif opcao == "📚 Histórico por Etapa":
        from .common_historico import historico_por_etapa
        historico_por_etapa(data, usuario)
    
    # === FUNCIONALIDADES EXCLUSIVAS DO ADMIN ===
    elif opcao == "⚙️ Configurações SLA":
        from .admin_configuracoes import configuracoes_sla
        configuracoes_sla(data, usuario, USE_DATABASE)
    elif opcao == "🔍 Auditoria":
        from .admin_auditoria import show_admin_auditoria
        show_admin_auditoria()
    elif opcao == "👥 Gerenciar Usuários":
        from .admin_usuarios import gerenciar_usuarios
        gerenciar_usuarios(data, usuario, USE_DATABASE)
    
    # === ACESSO DIRETO A PERFIS (MODO ADMIN) ===
    elif opcao == "🎭 Modo Solicitante":
        show_profile_mode("Solicitante", data, usuario, USE_DATABASE)
    elif opcao == "🎭 Modo Estoque":
        show_profile_mode("Estoque", data, usuario, USE_DATABASE)
    elif opcao == "🎭 Modo Suprimentos":
        show_profile_mode("Suprimentos", data, usuario, USE_DATABASE)
    elif opcao == "🎭 Modo Diretoria":
        show_profile_mode("Diretoria", data, usuario, USE_DATABASE)
    
    # === PAINEL ADMINISTRATIVO AVANÇADO ===
    elif opcao == "🚀 Painel Administrativo Completo":
        from .admin_wrapper import show_admin_wrapper
        show_admin_wrapper(data, usuario, USE_DATABASE)
    
    else:
        st.error("❌ Opção não implementada ainda.")

def show_profile_mode(profile_name: str, data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Exibe interface completa de um perfil específico para o Admin"""
    st.markdown(f"### 🎭 Modo {profile_name} - Acesso Administrativo")
    st.info(f"🔧 **Modo Administrador**: Você está acessando todas as funcionalidades do perfil **{profile_name}** com privilégios administrativos.")
    
    # Importa e executa o perfil específico
    if profile_name == "Solicitante":
        from .solicitante import get_profile_options, handle_profile_option
        opcoes = get_profile_options()
        st.markdown("#### 📝 Funcionalidades do Solicitante:")
        opcao_selecionada = st.selectbox("Escolha uma funcionalidade:", opcoes, key=f"admin_modo_{profile_name.lower()}")
        if st.button(f"Executar {opcao_selecionada}", key=f"exec_admin_{profile_name.lower()}"):
            handle_profile_option(opcao_selecionada, data, usuario, USE_DATABASE)
    
    elif profile_name == "Estoque":
        from .estoque import get_profile_options, handle_profile_option
        opcoes = get_profile_options()
        st.markdown("#### 📋 Funcionalidades do Estoque:")
        opcao_selecionada = st.selectbox("Escolha uma funcionalidade:", opcoes, key=f"admin_modo_{profile_name.lower()}")
        if st.button(f"Executar {opcao_selecionada}", key=f"exec_admin_{profile_name.lower()}"):
            handle_profile_option(opcao_selecionada, data, usuario, USE_DATABASE)
    
    elif profile_name == "Suprimentos":
        from .suprimentos import get_profile_options, handle_profile_option
        opcoes = get_profile_options()
        st.markdown("#### 🏭 Funcionalidades do Suprimentos:")
        opcao_selecionada = st.selectbox("Escolha uma funcionalidade:", opcoes, key=f"admin_modo_{profile_name.lower()}")
        if st.button(f"Executar {opcao_selecionada}", key=f"exec_admin_{profile_name.lower()}"):
            handle_profile_option(opcao_selecionada, data, usuario, USE_DATABASE)
    
    elif profile_name == "Diretoria":
        from .diretoria import get_profile_options, handle_profile_option
        opcoes = get_profile_options()
        st.markdown("#### 📱 Funcionalidades da Diretoria:")
        opcao_selecionada = st.selectbox("Escolha uma funcionalidade:", opcoes, key=f"admin_modo_{profile_name.lower()}")
        if st.button(f"Executar {opcao_selecionada}", key=f"exec_admin_{profile_name.lower()}"):
            handle_profile_option(opcao_selecionada, data, usuario, USE_DATABASE)
    
    st.markdown("---")
    st.success(f"✅ **Acesso Completo**: Como Admin, você tem acesso total às funcionalidades do perfil {profile_name}.")
