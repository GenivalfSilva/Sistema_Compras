"""
Módulo comum para Histórico por Etapa - usado por todos os perfis
"""

import streamlit as st
import pandas as pd
import datetime
import io
from typing import Dict

def historico_por_etapa(data: Dict, usuario: Dict):
    """Renderiza o Histórico por Etapa"""
    from style import get_section_header_html, get_info_box_html
    
    ETAPAS_PROCESSO = ["Solicitação", "Suprimentos", "Em Cotação", "Aguardando Aprovação", "Aprovado", "Reprovado", "Pedido Finalizado"]
    DEPARTAMENTOS = ["Manutenção", "TI", "RH", "Financeiro", "Marketing", "Operações", "Outro"]
    PRIORIDADES = ["Normal", "Urgente", "Baixa", "Alta"]
    
    st.markdown(get_section_header_html('📚 Histórico por Etapa'), unsafe_allow_html=True)
    st.markdown(get_info_box_html('📋 <strong>Histórico completo com informações detalhadas</strong>'), unsafe_allow_html=True)
    
    if not data["solicitacoes"]:
        st.warning("📋 Não há dados para exibir.")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        etapa_filtro = st.selectbox("Filtrar por Etapa:", ["Todas"] + ETAPAS_PROCESSO)
    with col2:
        departamento_filtro = st.selectbox("Filtrar por Departamento:", ["Todos"] + DEPARTAMENTOS)
    with col3:
        prioridade_filtro = st.selectbox("Filtrar por Prioridade:", ["Todas"] + PRIORIDADES)
    
    # Aplica filtros
    solicitacoes_filtradas = data["solicitacoes"]
    
    if etapa_filtro != "Todas":
        solicitacoes_filtradas = [s for s in solicitacoes_filtradas if s["status"] == etapa_filtro]
    if departamento_filtro != "Todos":
        solicitacoes_filtradas = [s for s in solicitacoes_filtradas if s["departamento"] == departamento_filtro]
    if prioridade_filtro != "Todas":
        solicitacoes_filtradas = [s for s in solicitacoes_filtradas if s["prioridade"] == prioridade_filtro]
    
    # Cria DataFrame para exibição
    if solicitacoes_filtradas:
        historico_df = []
        for sol in solicitacoes_filtradas:
            carimbo = sol["carimbo_data_hora"]
            if isinstance(carimbo, str):
                data_criacao = datetime.datetime.fromisoformat(carimbo).strftime('%d/%m/%Y %H:%M')
            elif isinstance(carimbo, datetime.datetime):
                data_criacao = carimbo.strftime('%d/%m/%Y %H:%M')
            else:
                data_criacao = 'Data inválida'
            
            # Campos adicionais solicitados pelo cliente
            data_requisicao = "N/A"
            if sol.get('data_requisicao_interna'):
                try:
                    data_requisicao = datetime.datetime.fromisoformat(sol['data_requisicao_interna']).strftime('%d/%m/%Y')
                except:
                    data_requisicao = sol.get('data_requisicao_interna', 'N/A')
            
            data_pedido = "N/A"
            if sol.get('data_finalizacao'):
                try:
                    data_pedido = datetime.datetime.fromisoformat(sol['data_finalizacao']).strftime('%d/%m/%Y')
                except:
                    data_pedido = sol.get('data_finalizacao', 'N/A')
            elif sol.get('data_numero_pedido'):
                try:
                    data_pedido = datetime.datetime.fromisoformat(sol['data_numero_pedido']).strftime('%d/%m/%Y')
                except:
                    data_pedido = sol.get('data_numero_pedido', 'N/A')
            
            historico_df.append({
                "Solicitação": f"#{sol['numero_solicitacao_estoque']}",
                "Data da Solicitação": data_criacao,
                "Solicitante": sol["solicitante"],
                "Departamento": sol["departamento"],
                "Prioridade": sol["prioridade"],
                "Descrição": sol["descricao"][:50] + "..." if len(sol["descricao"]) > 50 else sol["descricao"],
                "Status": sol["status"],
                "Requisição": sol.get("numero_requisicao_interno", "N/A"),
                "Data da Requisição": data_requisicao,
                "Pedido de Compra": str(sol.get("numero_pedido", sol.get("numero_pedido_compras", "N/A")) or "N/A"),
                "Data do Pedido de Compra": data_pedido,
                "SLA (dias)": sol["sla_dias"],
                "Dias Atendimento": sol.get("dias_atendimento", "N/A"),
                "SLA Cumprido": sol.get("sla_cumprido", "N/A"),
                "Valor Final": f"R$ {sol.get('valor_final', 0):,.2f}".replace(',', '_').replace('.', ',').replace('_', '.') if sol.get('valor_final') else "N/A",
                "Fornecedor": sol.get('fornecedor_final', sol.get('fornecedor_recomendado', 'N/A')),
                "Data Entrega": datetime.datetime.fromisoformat(sol["data_entrega"]).strftime('%d/%m/%Y') if sol.get("data_entrega") else "N/A"
            })
        
        df_historico = pd.DataFrame(historico_df)
        st.dataframe(df_historico, use_container_width=True)
        
        # Botões para download
        # Criar cópia do DataFrame para formatação de exportação
        df_export = df_historico.copy()
        
        # Normalizar caracteres especiais para evitar problemas de codificação
        import unicodedata
        for col in df_export.select_dtypes(include=['object']).columns:
            df_export[col] = df_export[col].astype(str).apply(
                lambda x: unicodedata.normalize('NFC', x) if x != 'nan' else x
            )
            
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Historico')
            xlsx_data = output.getvalue()
            st.download_button(
                label="📥 Download Excel (.xlsx)",
                data=xlsx_data,
                file_name=f"historico_compras_sla_{datetime.datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception:
            st.caption("Não foi possível gerar Excel (.xlsx). Verifique a dependência 'openpyxl'.")
    else:
        st.info("📋 Nenhuma solicitação encontrada com os filtros aplicados.")
