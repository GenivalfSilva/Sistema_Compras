"""
Interface de Auditoria para Admin
Visualização de logs de ações administrativas
"""

import streamlit as st
import pandas as pd
from database_local import get_local_database
from datetime import datetime, timedelta
import json

def show_admin_auditoria():
    """Interface para visualizar logs de auditoria do Admin"""
    
    st.title("🔍 Auditoria de Ações Administrativas")
    
    # Aviso sobre auditoria
    st.info("📋 **Registro de Auditoria** - Todas as ações administrativas são registradas automaticamente para controle e rastreabilidade.")
    
    db = get_local_database()
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        limite_registros = st.selectbox(
            "📊 Registros por página:",
            [25, 50, 100, 200],
            index=1
        )
    
    with col2:
        filtro_modulo = st.selectbox(
            "🏷️ Filtrar por módulo:",
            ["Todos", "SOLICITACOES", "REQUISICOES", "SUPRIMENTOS", "APROVACOES", "USUARIOS", "CONFIGURACOES"],
            index=0
        )
    
    with col3:
        filtro_periodo = st.selectbox(
            "📅 Período:",
            ["Últimas 24h", "Última semana", "Último mês", "Todos"],
            index=0
        )
    
    # Buscar logs
    try:
        logs = db.get_admin_audit_logs(limit=limite_registros)
        
        if not logs:
            st.warning("📝 Nenhum log de auditoria encontrado.")
            return
        
        # Converter para DataFrame
        df_logs = pd.DataFrame(logs)
        
        # Aplicar filtros
        if filtro_modulo != "Todos":
            df_logs = df_logs[df_logs['modulo'] == filtro_modulo]
        
        # Filtro de período
        if filtro_periodo != "Todos":
            now = datetime.now()
            if filtro_periodo == "Últimas 24h":
                cutoff = now - timedelta(days=1)
            elif filtro_periodo == "Última semana":
                cutoff = now - timedelta(weeks=1)
            elif filtro_periodo == "Último mês":
                cutoff = now - timedelta(days=30)
            
            df_logs = df_logs[pd.to_datetime(df_logs['timestamp']) >= cutoff]
        
        if df_logs.empty:
            st.warning("📝 Nenhum log encontrado com os filtros aplicados.")
            return
        
        # Estatísticas
        st.subheader("📊 Estatísticas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Ações", len(df_logs))
        
        with col2:
            ações_hoje = len(df_logs[pd.to_datetime(df_logs['timestamp']).dt.date == datetime.now().date()])
            st.metric("Ações Hoje", ações_hoje)
        
        with col3:
            módulos_únicos = df_logs['modulo'].nunique()
            st.metric("Módulos Acessados", módulos_únicos)
        
        with col4:
            if 'solicitacao_id' in df_logs.columns:
                solicitações_afetadas = df_logs['solicitacao_id'].dropna().nunique()
                st.metric("Solicitações Afetadas", solicitações_afetadas)
        
        # Gráfico de ações por módulo
        st.subheader("📈 Ações por Módulo")
        ações_por_modulo = df_logs['modulo'].value_counts()
        st.bar_chart(ações_por_modulo)
        
        # Tabela de logs
        st.subheader("📋 Registro Detalhado")
        
        # Preparar dados para exibição
        df_display = df_logs.copy()
        df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
        
        # Expandir detalhes JSON
        def format_detalhes(detalhes_json):
            if pd.isna(detalhes_json) or detalhes_json is None:
                return "-"
            try:
                detalhes = json.loads(detalhes_json)
                return ", ".join([f"{k}: {v}" for k, v in detalhes.items()])
            except:
                return str(detalhes_json)
        
        if 'detalhes' in df_display.columns:
            df_display['detalhes_formatados'] = df_display['detalhes'].apply(format_detalhes)
        
        # Selecionar colunas para exibição
        colunas_exibir = ['timestamp', 'usuario', 'acao', 'modulo']
        if 'solicitacao_id' in df_display.columns:
            colunas_exibir.append('solicitacao_id')
        if 'detalhes_formatados' in df_display.columns:
            colunas_exibir.append('detalhes_formatados')
        if 'ip_address' in df_display.columns:
            colunas_exibir.append('ip_address')
        
        # Renomear colunas para português
        df_display_renamed = df_display[colunas_exibir].rename(columns={
            'timestamp': 'Data/Hora',
            'usuario': 'Usuário',
            'acao': 'Ação',
            'modulo': 'Módulo',
            'solicitacao_id': 'ID Solicitação',
            'detalhes_formatados': 'Detalhes',
            'ip_address': 'IP'
        })
        
        # Mostrar tabela
        st.dataframe(
            df_display_renamed,
            use_container_width=True,
            hide_index=True
        )
        
        # Botão de exportação
        if st.button("📥 Exportar Logs"):
            csv_data = df_display_renamed.to_csv(index=False, encoding='utf-8-sig', sep=';')
            st.download_button(
                label="💾 Download CSV",
                data=csv_data,
                file_name=f"auditoria_admin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Detalhes expandidos
        st.subheader("🔍 Detalhes da Última Ação")
        if not df_logs.empty:
            ultima_acao = df_logs.iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Usuário:** {ultima_acao['usuario']}")
                st.write(f"**Ação:** {ultima_acao['acao']}")
                st.write(f"**Módulo:** {ultima_acao['modulo']}")
            
            with col2:
                st.write(f"**Data/Hora:** {ultima_acao['timestamp']}")
                if ultima_acao.get('solicitacao_id'):
                    st.write(f"**ID Solicitação:** {ultima_acao['solicitacao_id']}")
                if ultima_acao.get('ip_address'):
                    st.write(f"**IP:** {ultima_acao['ip_address']}")
            
            if ultima_acao.get('detalhes'):
                st.write("**Detalhes:**")
                try:
                    detalhes = json.loads(ultima_acao['detalhes'])
                    st.json(detalhes)
                except:
                    st.write(ultima_acao['detalhes'])
    
    except Exception as e:
        st.error(f"❌ Erro ao carregar logs de auditoria: {e}")

if __name__ == "__main__":
    show_admin_auditoria()
