"""
Módulo comum para Dashboard SLA - usado por todos os perfis
"""

import streamlit as st
import pandas as pd
import datetime
from typing import Dict

def calcular_dias_uteis(data_inicio, data_fim=None):
    """Calcula dias úteis entre duas datas"""
    if data_fim is None:
        data_fim = datetime.datetime.now()
    try:
        if isinstance(data_inicio, str):
            data_inicio = datetime.datetime.fromisoformat(data_inicio)
        if isinstance(data_fim, str):
            data_fim = datetime.datetime.fromisoformat(data_fim)
        data_atual = data_inicio.date()
        data_final = data_fim.date()
        dias_uteis = 0
        while data_atual <= data_final:
            if data_atual.weekday() < 5:
                dias_uteis += 1
            data_atual += datetime.timedelta(days=1)
        return max(0, dias_uteis - 1)
    except:
        return 0

def obter_sla_por_prioridade(prioridade: str, departamento: str = None) -> int:
    """Obtém SLA baseado na prioridade"""
    SLA_PADRAO = {"Urgente": 1, "Alta": 2, "Normal": 3, "Baixa": 5}
    return SLA_PADRAO.get(prioridade, 3)

def dashboard_sla(data: Dict, usuario: Dict):
    """Renderiza o Dashboard SLA"""
    from style import get_section_header_html, get_info_box_html, get_stats_card_html
    
    def format_brl(valor) -> str:
        """Formata número para moeda BRL (pt-BR) ex.: R$ 1.234,56"""
        if valor is None:
            return "N/A"
        try:
            s = f"{float(valor):,.2f}"
            s = s.replace(",", "_").replace(".", ",").replace("_", ".")
            return f"R$ {s}"
        except Exception:
            return "N/A"

    ETAPAS_PROCESSO = ["Solicitação", "Suprimentos", "Em Cotação", "Aguardando Aprovação", "Aprovado", "Reprovado", "Pedido Finalizado"]
    
    st.markdown(get_section_header_html('📊 Dashboard SLA'), unsafe_allow_html=True)
    st.markdown(get_info_box_html('📈 <strong>Painel de controle e métricas do sistema</strong>'), unsafe_allow_html=True)
    
    if not data["solicitacoes"]:
        warning_content = '📋 <strong>Não há dados para exibir no dashboard.</strong><br>💡 Crie algumas solicitações primeiro!'
        st.markdown(get_info_box_html(warning_content, "warning"), unsafe_allow_html=True)
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    total_solicitacoes = len(data["solicitacoes"])
    pendentes = len([s for s in data["solicitacoes"] if s["status"] not in ["Aprovado", "Reprovado", "Pedido Finalizado"]])
    aprovadas = len([s for s in data["solicitacoes"] if s["status"] == "Aprovado"])
    em_atraso = len([
        s for s in data["solicitacoes"]
        if s["status"] not in ["Aprovado", "Reprovado", "Pedido Finalizado"]
        and calcular_dias_uteis(s.get("carimbo_data_hora")) > (s.get("sla_dias") or obter_sla_por_prioridade(s.get("prioridade", "Normal")))
    ])
    
    with col1:
        st.markdown(get_stats_card_html(str(total_solicitacoes), "📋 Total de Solicitações"), unsafe_allow_html=True)
    with col2:
        st.markdown(get_stats_card_html(str(pendentes), "⏳ Pendentes"), unsafe_allow_html=True)
    with col3:
        st.markdown(get_stats_card_html(str(aprovadas), "✅ Aprovadas"), unsafe_allow_html=True)
    with col4:
        st.markdown(get_stats_card_html(str(em_atraso), "🚨 Em Atraso"), unsafe_allow_html=True)

    # Métricas secundárias
    st.markdown('<h3 style="color: var(--ziran-gray); margin-top: 2rem; margin-bottom: 1rem;">📈 Métricas Detalhadas</h3>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    finalizadas = len([s for s in data["solicitacoes"] if s["status"] == "Pedido Finalizado"])
    em_andamento = total_solicitacoes - finalizadas
    slas_cumpridos = len([s for s in data["solicitacoes"] if s.get("sla_cumprido") == "Sim"])
    
    with col1:
        st.markdown(get_stats_card_html(str(finalizadas), "🏁 Finalizadas"), unsafe_allow_html=True)
    with col2:
        st.markdown(get_stats_card_html(str(em_andamento), "⚡ Em Andamento"), unsafe_allow_html=True)
    with col3:
        st.markdown(get_stats_card_html(str(slas_cumpridos), "✅ SLA Cumprido"), unsafe_allow_html=True)
    with col4:
        if finalizadas > 0:
            taxa_sla = (slas_cumpridos / finalizadas) * 100
            taxa_display = f"{taxa_sla:.1f}%"
        else:
            taxa_display = "N/A"
        st.markdown(get_stats_card_html(taxa_display, "📊 Taxa SLA"), unsafe_allow_html=True)

    # Distribuição por etapa
    st.subheader("🔄 Distribuição por Etapa")
    etapas_count = {}
    for etapa in ETAPAS_PROCESSO:
        etapas_count[etapa] = len([s for s in data["solicitacoes"] if s["status"] == etapa])
    
    items = list(etapas_count.items())
    for start in range(0, len(items), 4):
        chunk = items[start:start+4]
        cols = st.columns(len(chunk))
        for col, (etapa, count) in zip(cols, chunk):
            with col:
                st.metric(etapa, count)
    
    # Performance por colaborador (conforme solicitado pelo cliente)
    st.subheader("👥 Performance por Colaborador")
    
    colaborador_stats = {}
    for sol in data["solicitacoes"]:
        solicitante = sol.get('solicitante', 'N/A')
        if solicitante not in colaborador_stats:
            colaborador_stats[solicitante] = {
                'total': 0,
                'finalizadas': 0,
                'aprovadas': 0,
                'em_andamento': 0,
                'sla_cumprido': 0,
                'valor_total': 0
            }
        
        stats = colaborador_stats[solicitante]
        stats['total'] += 1
        
        status = sol.get('status', '')
        if status == 'Pedido Finalizado':
            stats['finalizadas'] += 1
            if sol.get('sla_cumprido') == 'Sim':
                stats['sla_cumprido'] += 1
        elif status == 'Aprovado':
            stats['aprovadas'] += 1
        elif status not in ['Reprovado']:
            stats['em_andamento'] += 1
        
        valor = sol.get('valor_final') or sol.get('valor_estimado') or 0
        stats['valor_total'] += valor
    
    if colaborador_stats:
        perf_df = []
        for colaborador, stats in colaborador_stats.items():
            taxa_finalizacao = (stats['finalizadas'] / stats['total'] * 100) if stats['total'] > 0 else 0
            taxa_sla = (stats['sla_cumprido'] / stats['finalizadas'] * 100) if stats['finalizadas'] > 0 else 0
            
            perf_df.append({
                'Colaborador': colaborador,
                'Total Solicitações': stats['total'],
                'Finalizadas': stats['finalizadas'],
                'Em Andamento': stats['em_andamento'],
                'Taxa Finalização': f"{taxa_finalizacao:.1f}%",
                'Taxa SLA': f"{taxa_sla:.1f}%",
                'Valor Total': format_brl(stats['valor_total'])
            })
        
        df_performance = pd.DataFrame(perf_df).sort_values('Total Solicitações', ascending=False)
        st.dataframe(df_performance, width='stretch')
    else:
        st.info("📊 Não há dados suficientes para análise de performance.")
    
    # Solicitações com SLA em risco
    st.subheader("⚠️ Solicitações com SLA em Risco")
    
    solicitacoes_risco = []
    for sol in data["solicitacoes"]:
        if sol["status"] != "Pedido Finalizado":
            carimbo = sol["carimbo_data_hora"]
            if isinstance(carimbo, str):
                data_criacao = datetime.datetime.fromisoformat(carimbo)
            elif isinstance(carimbo, datetime.datetime):
                data_criacao = carimbo
            else:
                continue
            dias_decorridos = calcular_dias_uteis(data_criacao)
            
            if dias_decorridos >= sol["sla_dias"]:
                solicitacoes_risco.append({
                    "Número": f"#{sol['numero_solicitacao_estoque']}",
                    "Solicitante": sol["solicitante"],
                    "Departamento": sol["departamento"],
                    "Prioridade": sol["prioridade"],
                    "Status": sol["status"],
                    "SLA (dias)": sol["sla_dias"],
                    "Dias Decorridos": dias_decorridos,
                    "Atraso": dias_decorridos - sol["sla_dias"]
                })
    
    if solicitacoes_risco:
        df_risco = pd.DataFrame(solicitacoes_risco)
        st.dataframe(df_risco, width='stretch')
    else:
        st.success("✅ Nenhuma solicitação com SLA em risco!")
