"""
Módulo para visualização das solicitações do usuário logado
Contém: Lista filtrada por solicitante, acompanhamento de status
"""

import streamlit as st
import pandas as pd
import datetime
from typing import Dict

def minhas_solicitacoes(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Renderiza a página de Minhas Solicitações para o solicitante"""
    from style import get_section_header_html, get_info_box_html, get_stats_card_html
    from app import format_brl
    
    st.markdown(get_section_header_html('📋 Minhas Solicitações'), unsafe_allow_html=True)
    st.markdown(get_info_box_html('👤 <strong>Visualizando apenas suas solicitações</strong>'), unsafe_allow_html=True)
    
    # Filtra solicitações do usuário logado
    nome_usuario = usuario.get('nome', usuario.get('username', ''))
    minhas_sols = []
    
    for sol in data.get("solicitacoes", []):
        # Compara com nome ou username do solicitante
        solicitante = sol.get('solicitante', '')
        if solicitante.lower() == nome_usuario.lower() or solicitante.lower() == usuario.get('username', '').lower():
            minhas_sols.append(sol)
    
    if not minhas_sols:
        st.info("📋 Você ainda não possui solicitações criadas.")
        st.markdown("💡 Use a opção **'📝 Nova Solicitação'** para criar sua primeira solicitação.")
        return
    
    # Métricas do usuário
    st.markdown("### 📊 Resumo das Suas Solicitações")
    col1, col2, col3, col4 = st.columns(4)
    
    total_minhas = len(minhas_sols)
    pendentes = len([s for s in minhas_sols if s.get('status') not in ['Pedido Finalizado', 'Reprovado']])
    aprovadas = len([s for s in minhas_sols if s.get('status') == 'Aprovado'])
    finalizadas = len([s for s in minhas_sols if s.get('status') == 'Pedido Finalizado'])
    
    with col1:
        st.markdown(get_stats_card_html(str(total_minhas), "📋 Total"), unsafe_allow_html=True)
    with col2:
        st.markdown(get_stats_card_html(str(pendentes), "⏳ Em Andamento"), unsafe_allow_html=True)
    with col3:
        st.markdown(get_stats_card_html(str(aprovadas), "✅ Aprovadas"), unsafe_allow_html=True)
    with col4:
        st.markdown(get_stats_card_html(str(finalizadas), "🏁 Finalizadas"), unsafe_allow_html=True)
    
    # Filtros
    st.markdown("### 🔍 Filtros")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filtro = st.selectbox("Status:", 
            ["Todos", "Solicitação", "Suprimentos", "Em Cotação", "Aguardando Aprovação", "Aprovado", "Reprovado", "Pedido Finalizado"])
    with col2:
        prioridade_filtro = st.selectbox("Prioridade:", ["Todas", "Urgente", "Alta", "Normal", "Baixa"])
    with col3:
        # Ordenação
        ordenacao = st.selectbox("Ordenar por:", ["Mais Recente", "Mais Antiga", "Prioridade", "Status"])
    
    # Aplica filtros
    sols_filtradas = minhas_sols.copy()
    
    if status_filtro != "Todos":
        sols_filtradas = [s for s in sols_filtradas if s.get('status') == status_filtro]
    if prioridade_filtro != "Todas":
        sols_filtradas = [s for s in sols_filtradas if s.get('prioridade') == prioridade_filtro]
    
    # Aplica ordenação
    if ordenacao == "Mais Recente":
        sols_filtradas.sort(key=lambda x: x.get('carimbo_data_hora', ''), reverse=True)
    elif ordenacao == "Mais Antiga":
        sols_filtradas.sort(key=lambda x: x.get('carimbo_data_hora', ''))
    elif ordenacao == "Prioridade":
        prioridade_ordem = {"Urgente": 0, "Alta": 1, "Normal": 2, "Baixa": 3}
        sols_filtradas.sort(key=lambda x: prioridade_ordem.get(x.get('prioridade', 'Normal'), 2))
    elif ordenacao == "Status":
        sols_filtradas.sort(key=lambda x: x.get('status', ''))
    
    # Lista as solicitações
    st.markdown(f"### 📋 Suas Solicitações ({len(sols_filtradas)} encontrada(s))")
    
    if not sols_filtradas:
        st.info("🔍 Nenhuma solicitação encontrada com os filtros aplicados.")
        return
    
    for sol in sols_filtradas:
        numero = sol.get('numero_solicitacao_estoque')
        status = sol.get('status', 'N/A')
        prioridade = sol.get('prioridade', 'Normal')
        
        # Define cor do status
        status_colors = {
            'Solicitação': '🟡',
            'Suprimentos': '🔵', 
            'Em Cotação': '🟠',
            'Aguardando Aprovação': '🟣',
            'Aprovado': '🟢',
            'Reprovado': '🔴',
            'Pedido Finalizado': '✅'
        }
        
        # Define cor da prioridade
        prioridade_colors = {
            'Urgente': '🚨',
            'Alta': '🔴',
            'Normal': '🟡',
            'Baixa': '🟢'
        }
        
        status_icon = status_colors.get(status, '⚪')
        prioridade_icon = prioridade_colors.get(prioridade, '🟡')
        
        with st.expander(f"{status_icon} Solicitação #{numero} - {prioridade_icon} {prioridade}", 
                        expanded=False):
            
            # Informações principais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**📅 Data:** {sol.get('carimbo_data_hora', 'N/A')[:10] if sol.get('carimbo_data_hora') else 'N/A'}")
                st.markdown(f"**🏢 Departamento:** {sol.get('departamento', 'N/A')}")
                st.markdown(f"**📍 Local:** {sol.get('local_aplicacao', 'N/A')}")
            
            with col2:
                st.markdown(f"**📊 Status:** {status}")
                st.markdown(f"**⚡ Prioridade:** {prioridade}")
                req_interno = sol.get('numero_requisicao_interno')
                st.markdown(f"**📋 Req. Interna:** {req_interno if req_interno else 'Não lançada'}")
            
            with col3:
                valor_est = sol.get('valor_estimado') or sol.get('valor_final')
                st.markdown(f"**💰 Valor:** {format_brl(valor_est) if valor_est else 'N/A'}")
                sla_dias = sol.get('sla_dias', 0)
                st.markdown(f"**⏱️ SLA:** {sla_dias} dias úteis")
                
                # Calcula dias decorridos
                try:
                    if sol.get('carimbo_data_hora'):
                        from app import calcular_dias_uteis
                        data_inicio = datetime.datetime.fromisoformat(sol['carimbo_data_hora'])
                        dias_decorridos = calcular_dias_uteis(data_inicio)
                        
                        if status not in ['Pedido Finalizado', 'Reprovado']:
                            if dias_decorridos > sla_dias:
                                st.markdown(f"**⚠️ Dias:** {dias_decorridos} (Em atraso)")
                            else:
                                st.markdown(f"**📅 Dias:** {dias_decorridos}")
                        else:
                            sla_cumprido = sol.get('sla_cumprido', 'N/A')
                            st.markdown(f"**✅ SLA:** {sla_cumprido}")
                except:
                    st.markdown("**📅 Dias:** N/A")
            
            # Descrição
            if sol.get('descricao'):
                st.markdown("**📝 Descrição:**")
                st.info(sol['descricao'])
            
            # Itens (resumo)
            if sol.get('itens'):
                st.markdown("**📦 Itens Solicitados:**")
                total_itens = len(sol['itens'])
                st.write(f"• {total_itens} item(ns) solicitado(s)")
                
                # Mostra primeiros 3 itens
                for i, item in enumerate(sol['itens'][:3]):
                    nome_item = item.get('nome', item.get('codigo', 'Item'))
                    qtd = item.get('quantidade', 1)
                    unidade = item.get('unidade', 'UN')
                    st.write(f"  - {nome_item}: {qtd} {unidade}")
                
                if total_itens > 3:
                    st.write(f"  ... e mais {total_itens - 3} item(ns)")
            
            # Histórico de etapas (resumo)
            if sol.get('historico_etapas'):
                with st.expander("📚 Histórico de Etapas"):
                    for etapa in sol['historico_etapas']:
                        data_etapa = etapa.get('data_entrada', '')
                        if data_etapa:
                            try:
                                data_formatada = datetime.datetime.fromisoformat(data_etapa).strftime("%d/%m/%Y %H:%M")
                            except:
                                data_formatada = data_etapa
                        else:
                            data_formatada = 'N/A'
                        
                        usuario_etapa = etapa.get('usuario', 'Sistema')
                        obs_etapa = etapa.get('observacoes', '')
                        
                        st.markdown(f"• **{etapa.get('etapa', 'N/A')}** - {data_formatada} - {usuario_etapa}")
                        if obs_etapa:
                            st.markdown(f"  *{obs_etapa}*")
            
            # Aprovações (se houver)
            if sol.get('aprovacoes'):
                with st.expander("✅ Aprovações"):
                    for aprov in sol['aprovacoes']:
                        nome_aprovador = aprov.get('nome_aprovador', 'N/A')
                        status_aprov = aprov.get('status', 'N/A')
                        data_aprov = aprov.get('data_aprovacao', '')
                        
                        if data_aprov:
                            try:
                                data_formatada = datetime.datetime.fromisoformat(data_aprov).strftime("%d/%m/%Y %H:%M")
                            except:
                                data_formatada = data_aprov
                        else:
                            data_formatada = 'N/A'
                        
                        icon_aprov = "✅" if status_aprov == "Aprovado" else "❌"
                        st.markdown(f"{icon_aprov} **{status_aprov}** por {nome_aprovador} - {data_formatada}")
                        
                        if aprov.get('observacoes'):
                            st.markdown(f"*{aprov['observacoes']}*")
    
    # Estatísticas adicionais
    if len(minhas_sols) > 0:
        st.markdown("---")
        st.markdown("### 📈 Suas Estatísticas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição por status
            status_count = {}
            for sol in minhas_sols:
                status = sol.get('status', 'N/A')
                status_count[status] = status_count.get(status, 0) + 1
            
            if status_count:
                st.markdown("**📊 Por Status:**")
                for status, count in sorted(status_count.items()):
                    st.write(f"• {status}: {count}")
        
        with col2:
            # Distribuição por prioridade
            prioridade_count = {}
            for sol in minhas_sols:
                prioridade = sol.get('prioridade', 'Normal')
                prioridade_count[prioridade] = prioridade_count.get(prioridade, 0) + 1
            
            if prioridade_count:
                st.markdown("**⚡ Por Prioridade:**")
                for prioridade, count in sorted(prioridade_count.items()):
                    st.write(f"• {prioridade}: {count}")
