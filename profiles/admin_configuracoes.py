"""
Módulo para configurações SLA do perfil Admin
Contém: Configuração de SLA por departamento, limites de aprovação, configurações gerais
"""

import streamlit as st
import pandas as pd
from typing import Dict

def configuracoes_sla(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Página de configurações SLA para administradores"""
    st.markdown("## ⚙️ Configurações SLA")
    
    # Importa funções necessárias
    from app import save_data
    from database_local import get_local_database as get_database
    
    config = data.get("configuracoes", {})
    
    # Tabs para organizar configurações
    tab1, tab2, tab3 = st.tabs(["🎯 SLA por Departamento", "💰 Limites de Aprovação", "⚙️ Configurações Gerais"])
    
    with tab1:
        st.markdown("### 🎯 Configuração de SLA por Departamento")
        st.info("Configure prazos específicos de SLA para cada departamento (em dias úteis)")
        
        departamentos = ["Manutenção", "TI", "RH", "Financeiro", "Marketing", "Operações", "Outro"]
        prioridades = ["Urgente", "Alta", "Normal", "Baixa"]
        
        sla_config = config.get("sla_por_departamento", {})
        
        # Cria DataFrame para edição
        sla_data = []
        for dept in departamentos:
            for prio in prioridades:
                key = f"{dept}_{prio}"
                valor_atual = sla_config.get(dept, {}).get(prio, 
                    {"Urgente": 1, "Alta": 2, "Normal": 3, "Baixa": 5}[prio])
                sla_data.append({
                    "Departamento": dept,
                    "Prioridade": prio,
                    "SLA (dias)": valor_atual
                })
        
        df_sla = pd.DataFrame(sla_data)
        
        # Editor de dados
        try:
            edited_df = st.data_editor(
                df_sla,
                column_config={
                    "SLA (dias)": st.column_config.NumberColumn(
                        "SLA (dias)",
                        help="Prazo em dias úteis",
                        min_value=1,
                        max_value=30,
                        step=1
                    )
                },
                width='stretch',
                key="sla_editor"
            )
        except:
            edited_df = df_sla
            st.dataframe(df_sla, width='stretch')
            st.warning("Editor não disponível. Dados em modo somente leitura.")
        
        if st.button("💾 Salvar Configurações SLA", type="primary"):
            # Atualiza configurações
            new_sla_config = {}
            for _, row in edited_df.iterrows():
                dept = row["Departamento"]
                prio = row["Prioridade"]
                dias = int(row["SLA (dias)"])
                
                if dept not in new_sla_config:
                    new_sla_config[dept] = {}
                new_sla_config[dept][prio] = dias
            
            config["sla_por_departamento"] = new_sla_config
            
            # Salva no banco ou JSON
            if USE_DATABASE:
                try:
                    db = get_database()
                    if db.db_available:
                        db.set_config("sla_por_departamento", str(new_sla_config))
                except Exception as e:
                    st.error(f"Erro ao salvar no banco: {e}")
            
            save_data(data)
            st.success("✅ Configurações SLA salvas com sucesso!")
            st.rerun()
    
    with tab2:
        st.markdown("### 💰 Limites de Aprovação")
        st.info("Configure os valores limite para aprovação por nível hierárquico")
        
        col1, col2 = st.columns(2)
        
        with col1:
            limite_gerencia = st.number_input(
                "Limite Gerência (R$)",
                min_value=0.0,
                value=float(config.get("limite_gerencia", 5000.0)),
                step=100.0,
                help="Valores acima deste limite precisam de aprovação da diretoria"
            )
        
        with col2:
            limite_diretoria = st.number_input(
                "Limite Diretoria (R$)",
                min_value=limite_gerencia,
                value=float(config.get("limite_diretoria", 15000.0)),
                step=100.0,
                help="Valores acima deste limite precisam de aprovação especial"
            )
        
        if st.button("💾 Salvar Limites", type="primary"):
            config["limite_gerencia"] = limite_gerencia
            config["limite_diretoria"] = limite_diretoria
            
            if USE_DATABASE:
                try:
                    db = get_database()
                    if db.db_available:
                        db.set_config("limite_gerencia", str(limite_gerencia))
                        db.set_config("limite_diretoria", str(limite_diretoria))
                except Exception as e:
                    st.error(f"Erro ao salvar no banco: {e}")
            
            save_data(data)
            st.success("✅ Limites de aprovação salvos com sucesso!")
    
    with tab3:
        st.markdown("### ⚙️ Configurações Gerais do Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📁 Upload e Armazenamento")
            upload_dir = st.text_input(
                "Diretório de Upload",
                value=config.get("upload_dir", "uploads"),
                help="Pasta onde os arquivos anexados serão salvos"
            )
            
            st.markdown("#### 📋 Suprimentos")
            min_cotacoes = st.number_input(
                "Mínimo de Cotações",
                min_value=1,
                max_value=10,
                value=int(config.get("suprimentos_min_cotacoes", 1)),
                help="Número mínimo de cotações necessárias"
            )
        
        with col2:
            st.markdown("#### 📎 Anexos")
            anexo_obrigatorio = st.checkbox(
                "Anexo Obrigatório em Suprimentos",
                value=config.get("suprimentos_anexo_obrigatorio", True),
                help="Torna obrigatório anexar arquivos nas etapas de suprimentos"
            )
            
            st.markdown("#### 🔢 Numeração")
            col_a, col_b = st.columns(2)
            with col_a:
                prox_sol = st.number_input(
                    "Próximo Nº Solicitação",
                    min_value=1,
                    value=int(config.get("proximo_numero_solicitacao", 1))
                )
            with col_b:
                prox_ped = st.number_input(
                    "Próximo Nº Pedido",
                    min_value=1,
                    value=int(config.get("proximo_numero_pedido", 1))
                )
        
        if st.button("💾 Salvar Configurações Gerais", type="primary"):
            config.update({
                "upload_dir": upload_dir,
                "suprimentos_min_cotacoes": min_cotacoes,
                "suprimentos_anexo_obrigatorio": anexo_obrigatorio,
                "proximo_numero_solicitacao": prox_sol,
                "proximo_numero_pedido": prox_ped
            })
            
            if USE_DATABASE:
                try:
                    db = get_database()
                    if db.db_available:
                        for key, value in config.items():
                            if key != "sla_por_departamento":
                                db.set_config(key, str(value))
                except Exception as e:
                    st.error(f"Erro ao salvar no banco: {e}")
            
            save_data(data)
            st.success("✅ Configurações gerais salvas com sucesso!")
    
    # Seção de informações do sistema
    st.markdown("---")
    st.markdown("### 📊 Informações do Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Solicitações", len(data.get("solicitacoes", [])))
    
    with col2:
        usuarios_count = len(data.get("usuarios", []))
        if USE_DATABASE:
            try:
                db = get_database()
                if db.db_available:
                    usuarios_count = len(db.get_all_users())
            except:
                pass
        st.metric("Total de Usuários", usuarios_count)
    
    with col3:
        st.metric("Notificações Ativas", len([n for n in data.get("notificacoes", []) if not n.get("lida")]))
