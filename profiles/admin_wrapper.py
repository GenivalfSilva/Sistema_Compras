"""
Wrapper administrativo para acesso completo a todas as funcionalidades
Permite ao Admin acessar qualquer funcionalidade de qualquer perfil com privilégios elevados
"""

import streamlit as st
from typing import Dict, List

def show_admin_wrapper(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Interface principal do wrapper administrativo com acesso completo"""
    st.markdown("### 🔧 Painel Administrativo Completo")
    st.info("🚀 **Super Administrador**: Você tem acesso total e irrestrito a todas as funcionalidades do sistema.")
    
    # Tabs para organizar melhor o acesso
    tab1, tab2, tab3, tab4 = st.tabs(["🎭 Emular Perfis", "🔍 Acesso Direto", "📊 Visão Geral", "⚙️ Configurações Avançadas"])
    
    with tab1:
        show_profile_emulation(data, usuario, USE_DATABASE)
    
    with tab2:
        show_direct_access(data, usuario, USE_DATABASE)
    
    with tab3:
        show_admin_overview(data, usuario)
    
    with tab4:
        show_advanced_settings(data, usuario, USE_DATABASE)

def show_profile_emulation(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Permite ao admin emular qualquer perfil do sistema"""
    st.markdown("#### 🎭 Emulação de Perfis")
    st.info("Acesse todas as funcionalidades de qualquer perfil como se fosse esse usuário.")
    
    perfil_emulado = st.selectbox(
        "Escolha o perfil para emular:",
        ["Solicitante", "Estoque", "Suprimentos", "Diretoria"],
        key="admin_perfil_emulation"
    )
    
    if perfil_emulado:
        st.success(f"🎭 **Emulando perfil**: {perfil_emulado}")
        
        # Importa e executa o perfil selecionado
        if perfil_emulado == "Solicitante":
            from .solicitante import get_profile_options, handle_profile_option
        elif perfil_emulado == "Estoque":
            from .estoque import get_profile_options, handle_profile_option
        elif perfil_emulado == "Suprimentos":
            from .suprimentos import get_profile_options, handle_profile_option
        elif perfil_emulado == "Diretoria":
            from .diretoria import get_profile_options, handle_profile_option
        
        opcoes = get_profile_options()
        opcao_selecionada = st.selectbox(
            f"Funcionalidades do {perfil_emulado}:",
            opcoes,
            key=f"admin_emulation_{perfil_emulado.lower()}"
        )
        
        if st.button(f"🚀 Executar: {opcao_selecionada}", key=f"exec_emulation_{perfil_emulado.lower()}"):
            with st.spinner(f"Executando {opcao_selecionada} como {perfil_emulado}..."):
                handle_profile_option(opcao_selecionada, data, usuario, USE_DATABASE)

def show_direct_access(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Acesso direto a todas as funcionalidades sem emulação"""
    st.markdown("#### 🔍 Acesso Direto às Funcionalidades")
    st.info("Acesso direto a qualquer funcionalidade do sistema com privilégios administrativos.")
    
    all_functions = get_all_profile_functions()
    
    # Organiza por categoria
    categoria = st.selectbox(
        "Selecione a categoria:",
        list(all_functions.keys()),
        key="admin_direct_category"
    )
    
    if categoria:
        funcoes = all_functions[categoria]
        funcao_selecionada = st.selectbox(
            f"Funcionalidades de {categoria}:",
            funcoes,
            key=f"admin_direct_{categoria.lower()}"
        )
        
        if st.button(f"🎯 Executar: {funcao_selecionada}", key=f"exec_direct_{categoria.lower()}"):
            execute_function_directly(funcao_selecionada, categoria, data, usuario, USE_DATABASE)

def show_admin_overview(data: Dict, usuario: Dict):
    """Visão geral administrativa do sistema"""
    st.markdown("#### 📊 Visão Geral do Sistema")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_solicitacoes = len(data.get("solicitacoes", []))
        st.metric("Total Solicitações", total_solicitacoes)
    
    with col2:
        pendentes = len([s for s in data.get("solicitacoes", []) if s.get("status") != "Pedido Finalizado"])
        st.metric("Pendentes", pendentes)
    
    with col3:
        finalizadas = len([s for s in data.get("solicitacoes", []) if s.get("status") == "Pedido Finalizado"])
        st.metric("Finalizadas", finalizadas)
    
    with col4:
        usuarios_total = len(data.get("usuarios", []))
        st.metric("Usuários", usuarios_total)
    
    # Gráfico de status
    if data.get("solicitacoes"):
        st.markdown("##### 📈 Distribuição por Status")
        status_counts = {}
        for sol in data["solicitacoes"]:
            status = sol.get("status", "Desconhecido")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        import pandas as pd
        df_status = pd.DataFrame(list(status_counts.items()), columns=["Status", "Quantidade"])
        st.bar_chart(df_status.set_index("Status"))

def show_advanced_settings(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Configurações avançadas do sistema"""
    st.markdown("#### ⚙️ Configurações Avançadas do Sistema")
    
    # Configurações de SLA
    if st.button("🔧 Configurações SLA Avançadas"):
        from .admin_configuracoes import configuracoes_sla
        configuracoes_sla(data, usuario, USE_DATABASE)
    
    # Auditoria completa
    if st.button("🔍 Auditoria Completa do Sistema"):
        from .admin_auditoria import show_admin_auditoria
        show_admin_auditoria()
    
    # Gerenciamento de usuários
    if st.button("👥 Gerenciamento Avançado de Usuários"):
        from .admin_usuarios import gerenciar_usuarios
        gerenciar_usuarios(data, usuario, USE_DATABASE)
    
    # Backup e restauração
    st.markdown("##### 💾 Backup e Restauração")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Fazer Backup do Sistema"):
            create_system_backup(data)
    
    with col2:
        if st.button("📤 Restaurar Sistema"):
            restore_system_backup(data)

def execute_function_directly(funcao: str, categoria: str, data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Executa uma função diretamente baseada na categoria"""
    try:
        if categoria == "Solicitante":
            if funcao == "📝 Nova Solicitação":
                from .solicitante_nova import nova_solicitacao
                nova_solicitacao(data, usuario, USE_DATABASE)
            elif funcao == "📋 Minhas Solicitações":
                from .solicitante_minhas import minhas_solicitacoes
                minhas_solicitacoes(data, usuario, USE_DATABASE)
        
        elif categoria == "Estoque":
            if funcao == "📋 Gestão de Requisições":
                from .estoque_requisicoes import show_estoque_requisicoes
                show_estoque_requisicoes()
        
        elif categoria == "Suprimentos":
            if funcao == "🏭 Processar Requisições":
                from .suprimentos_requisicoes import show_suprimentos_requisicoes
                show_suprimentos_requisicoes()
            elif funcao == "💰 Gerenciar Cotações":
                from .suprimentos_cotacoes import gerenciar_cotacoes
                gerenciar_cotacoes(data, usuario, USE_DATABASE)
            elif funcao == "🔄 Mover para Próxima Etapa":
                from .suprimentos_mover import mover_etapa
                mover_etapa(data, usuario, USE_DATABASE)
            elif funcao == "📦 Catálogo de Produtos":
                from .suprimentos_catalogo import catalogo_produtos
                catalogo_produtos(data, usuario, USE_DATABASE)
        
        elif categoria == "Diretoria":
            if funcao == "📱 Aprovações":
                from .diretoria_aprovacoes import aprovacoes
                aprovacoes(data, usuario, USE_DATABASE)
        
        # Funcionalidades comuns
        if funcao == "📊 Dashboard SLA":
            from .common_dashboard import dashboard_sla
            dashboard_sla(data, usuario)
        elif funcao == "📚 Histórico por Etapa":
            from .common_historico import historico_por_etapa
            historico_por_etapa(data, usuario)
        
        st.success(f"✅ Função '{funcao}' executada com sucesso!")
        
    except Exception as e:
        st.error(f"❌ Erro ao executar função '{funcao}': {str(e)}")

def get_all_profile_functions() -> Dict[str, List[str]]:
    """Retorna todas as funcionalidades de todos os perfis organizadas"""
    return {
        "Solicitante": [
            "📝 Nova Solicitação",
            "📋 Minhas Solicitações", 
            "📊 Dashboard SLA",
            "📚 Histórico por Etapa"
        ],
        "Estoque": [
            "📋 Gestão de Requisições",
            "📊 Dashboard SLA",
            "📚 Histórico por Etapa"
        ],
        "Suprimentos": [
            "🏭 Processar Requisições",
            "💰 Gerenciar Cotações",
            "📑 Requisição (Estoque) - Legado",
            "🔄 Mover para Próxima Etapa",
            "📊 Dashboard SLA",
            "📚 Histórico por Etapa",
            "📦 Catálogo de Produtos"
        ],
        "Diretoria": [
            "📱 Aprovações",
            "📊 Dashboard SLA",
            "📚 Histórico por Etapa"
        ],
        "Admin Exclusivo": [
            "⚙️ Configurações SLA",
            "🔍 Auditoria",
            "👥 Gerenciar Usuários"
        ]
    }

def create_system_backup(data: Dict):
    """Cria backup completo do sistema"""
    try:
        import json
        from datetime import datetime
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "data": data
        }
        
        backup_filename = f"sistema_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        st.success(f"✅ Backup criado com sucesso: {backup_filename}")
        
        # Disponibiliza para download
        with open(backup_filename, 'rb') as f:
            st.download_button(
                label="📥 Baixar Backup",
                data=f.read(),
                file_name=backup_filename,
                mime="application/json"
            )
            
    except Exception as e:
        st.error(f"❌ Erro ao criar backup: {str(e)}")

def restore_system_backup(data: Dict):
    """Restaura sistema a partir de backup"""
    st.warning("⚠️ Funcionalidade de restauração em desenvolvimento.")
    st.info("Esta funcionalidade permitirá restaurar o sistema a partir de um arquivo de backup.")
    
    uploaded_file = st.file_uploader(
        "Selecione o arquivo de backup:",
        type=['json'],
        key="backup_restore"
    )
    
    if uploaded_file:
        if st.button("🔄 Restaurar Sistema", key="restore_confirm"):
            st.info("🚧 Funcionalidade em implementação. Contate o desenvolvedor para restauração manual.")
