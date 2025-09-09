"""
Módulo para aprovações do perfil Diretoria (Gerência&Diretoria)
Contém: Visualizar solicitações pendentes, aprovar/reprovar, histórico de aprovações
"""

import streamlit as st
import pandas as pd
import datetime
from typing import Dict

def aprovacoes(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Página de aprovações para perfil Gerência&Diretoria"""
    st.markdown("## 📱 Aprovações")
    
    # Importa funções necessárias
    from app import save_data, add_notification, format_brl
    
    # Importação condicional do banco
    if USE_DATABASE:
        try:
            from database_local import get_local_database as get_database
        except ImportError:
            USE_DATABASE = False
    
    # Busca solicitações do banco ou JSON
    solicitacoes_todas = []
    if USE_DATABASE:
        try:
            db = get_database()
            if db.db_available:
                solicitacoes_todas = db.get_all_solicitacoes()
        except Exception as e:
            st.warning(f"⚠️ Erro ao acessar banco de dados: {e}")
            USE_DATABASE = False
    
    if not USE_DATABASE:
        solicitacoes_todas = data.get("solicitacoes", [])
    
    # Filtra solicitações que precisam de aprovação
    solicitacoes_aprovacao = []
    for sol in solicitacoes_todas:
        if sol.get("status") == "Aguardando Aprovação" or sol.get("etapa_atual") == "Aguardando Aprovação":
            solicitacoes_aprovacao.append(sol)
    
    # Ordena por prioridade conforme solicitado pelo cliente
    # Urgente > Alta > Normal > Baixa
    prioridade_ordem = {"Urgente": 0, "Alta": 1, "Normal": 2, "Baixa": 3}
    solicitacoes_aprovacao.sort(key=lambda x: prioridade_ordem.get(x.get('prioridade', 'Normal'), 2))
    
    if not solicitacoes_aprovacao:
        st.info("✅ Não há solicitações pendentes de aprovação no momento.")
        
        # Mostra histórico de aprovações recentes
        st.markdown("### 📚 Histórico Recente de Aprovações")
        historico_aprovacoes = []
        for sol in data.get("solicitacoes", []):
            for aprovacao in sol.get("aprovacoes", []):
                if aprovacao.get("aprovador") == usuario.get("username"):
                    historico_aprovacoes.append({
                        "Solicitação": sol.get("numero_solicitacao_estoque"),
                        "Data": aprovacao.get("data_aprovacao", ""),
                        "Decisão": aprovacao.get("status", ""),
                        "Valor": format_brl(sol.get("valor_estimado")),
                        "Solicitante": sol.get("solicitante", "")
                    })
        
        if historico_aprovacoes:
            df_historico = pd.DataFrame(historico_aprovacoes[-10:])  # Últimas 10
            st.dataframe(df_historico, width='stretch')
        else:
            st.info("Nenhuma aprovação realizada ainda.")
        return
    
    st.success(f"📋 {len(solicitacoes_aprovacao)} solicitação(ões) aguardando aprovação")
    if solicitacoes_aprovacao:
        st.info("💡 **Solicitações ordenadas por prioridade:** Urgente → Alta → Normal → Baixa")
    
    # Tabs para organizar aprovações
    tab1, tab2 = st.tabs(["🔍 Pendentes de Aprovação", "📊 Resumo Financeiro"])
    
    with tab1:
        for i, sol in enumerate(solicitacoes_aprovacao):
            # Adiciona indicador visual de prioridade
            prioridade = sol.get('prioridade', 'Normal')
            prioridade_icons = {
                'Urgente': '🚨',
                'Alta': '🔴', 
                'Normal': '🟡',
                'Baixa': '🟢'
            }
            prioridade_icon = prioridade_icons.get(prioridade, '🟡')
            
            with st.expander(f"{prioridade_icon} **{prioridade}** - Solicitação #{sol.get('numero_solicitacao_estoque')} - {sol.get('solicitante', 'N/A')}", expanded=i==0):
                
                # Informações básicas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Solicitante:** {sol.get('solicitante', 'N/A')}")
                    st.markdown(f"**Departamento:** {sol.get('departamento', 'N/A')}")
                    st.markdown(f"**Data:** {sol.get('data_solicitacao', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Prioridade:** {sol.get('prioridade', 'N/A')}")
                    st.markdown(f"**Tipo:** {sol.get('tipo_solicitacao', 'N/A')}")
                    valor_est = sol.get('valor_estimado')
                    st.markdown(f"**Valor Estimado:** {format_brl(valor_est) if valor_est else 'N/A'}")
                
                with col3:
                    st.markdown(f"**Status Atual:** {sol.get('status', 'N/A')}")
                    st.markdown(f"**Etapa:** {sol.get('etapa_atual', 'N/A')}")
                    req_interno = sol.get('numero_requisicao_interno')
                    st.markdown(f"**Req. Interna:** {req_interno if req_interno else 'N/A'}")
                
                # Descrição e justificativa
                st.markdown("**Descrição:**")
                st.info(sol.get('descricao', 'Sem descrição'))
                
                if sol.get('justificativa'):
                    st.markdown("**Justificativa:**")
                    st.info(sol.get('justificativa'))
                
                # Itens solicitados
                if sol.get('itens'):
                    st.markdown("**📦 Itens Solicitados:**")
                    itens_df = []
                    for idx, item in enumerate(sol['itens'], 1):
                        itens_df.append({
                            "Item": idx,
                            "Código": item.get('codigo', 'N/A'),
                            "Descrição": item.get('descricao', 'N/A'),
                            "Quantidade": item.get('quantidade', 'N/A'),
                            "Unidade": item.get('unidade', 'N/A'),
                            "Valor Unit.": format_brl(item.get('valor_unitario')) if item.get('valor_unitario') else 'N/A',
                            "Valor Total": format_brl(item.get('valor_total')) if item.get('valor_total') else 'N/A'
                        })
                    if itens_df:
                        st.dataframe(pd.DataFrame(itens_df), width='stretch')
                
                # Cotações (se houver)
                if sol.get('cotacoes'):
                    st.markdown("**💰 Cotações Recebidas:**")
                    cotacoes_df = []
                    for idx, cot in enumerate(sol['cotacoes'], 1):
                        cotacoes_df.append({
                            "Cotação": idx,
                            "Fornecedor": cot.get('fornecedor', 'N/A'),
                            "Valor": format_brl(cot.get('valor')),
                            "Prazo": f"{cot.get('prazo_entrega', 'N/A')} dias",
                            "Observações": cot.get('observacoes', '')[:50] + '...' if len(cot.get('observacoes', '')) > 50 else cot.get('observacoes', '')
                        })
                    if cotacoes_df:
                        st.dataframe(pd.DataFrame(cotacoes_df), width='stretch')
                        
                        # Recomendação do suprimentos
                        fornecedor_rec = sol.get('fornecedor_recomendado')
                        if fornecedor_rec:
                            st.success(f"🎯 **Recomendação Suprimentos:** {fornecedor_rec}")
                
                # Histórico de etapas
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
                            
                            st.markdown(f"• **{etapa.get('etapa', 'N/A')}** - {data_formatada} - {etapa.get('usuario', 'Sistema')}")
                
                # Formulário de aprovação
                st.markdown("---")
                st.markdown("### 🎯 Decisão de Aprovação")
                
                with st.form(f"aprovacao_form_{sol.get('numero_solicitacao_estoque')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        decisao = st.radio(
                            "Decisão:",
                            ["Aprovar", "Reprovar"],
                            key=f"decisao_{sol.get('numero_solicitacao_estoque')}"
                        )
                    
                    with col2:
                        observacoes_aprovacao = st.text_area(
                            "Observações:",
                            height=100,
                            placeholder="Comentários sobre a decisão...",
                            key=f"obs_{sol.get('numero_solicitacao_estoque')}"
                        )
                    
                    confirmar_decisao = st.form_submit_button(
                        f"✅ Confirmar {decisao}",
                        type="primary" if decisao == "Aprovar" else "secondary"
                    )
                
                if confirmar_decisao:
                    # Processa a aprovação/reprovação
                    numero_sol = sol.get('numero_solicitacao_estoque')
                    nome_aprovador = usuario.get('nome', usuario.get('username', 'Diretor'))
                    
                    # Atualiza a solicitação
                    for j, s in enumerate(data["solicitacoes"]):
                        if s["numero_solicitacao_estoque"] == numero_sol:
                            # Adiciona registro de aprovação
                            aprovacao_registro = {
                                "nivel": "Gerência&Diretoria",
                                "aprovador": usuario.get('username'),
                                "nome_aprovador": nome_aprovador,
                                "status": "Aprovado" if decisao == "Aprovar" else "Reprovado",
                                "data_aprovacao": datetime.datetime.now().isoformat(),
                                "observacoes": observacoes_aprovacao
                            }
                            
                            data["solicitacoes"][j].setdefault("aprovacoes", []).append(aprovacao_registro)
                            
                            # Atualiza status e etapa com transição automática
                            if decisao == "Aprovar":
                                # Aprovação: transição automática para Compra feita
                                data["solicitacoes"][j]["status"] = "Compra feita"
                                data["solicitacoes"][j]["etapa_atual"] = "Compra feita"
                                nova_etapa = "Compra feita"
                                mensagem_notif = f"Solicitação aprovada por {nome_aprovador} - Compra autorizada e realizada"
                                
                                # Adiciona etapa intermediária "Aprovado" no histórico
                                data["solicitacoes"][j]["historico_etapas"].append({
                                    "etapa": "Aprovado",
                                    "data_entrada": datetime.datetime.now().isoformat(),
                                    "usuario": nome_aprovador,
                                    "observacoes": f"Aprovado - {observacoes_aprovacao}"
                                })
                            else:
                                # Reprovação: processo encerrado
                                data["solicitacoes"][j]["status"] = "Reprovado"
                                data["solicitacoes"][j]["etapa_atual"] = "Reprovado"
                                nova_etapa = "Reprovado"
                                mensagem_notif = f"Solicitação reprovada por {nome_aprovador}"
                            
                            # Adiciona ao histórico de etapas
                            data["solicitacoes"][j]["historico_etapas"].append({
                                "etapa": nova_etapa,
                                "data_entrada": datetime.datetime.now().isoformat(),
                                "usuario": nome_aprovador,
                                "observacoes": observacoes_aprovacao
                            })
                            
                            # Notifica solicitante e suprimentos
                            try:
                                add_notification(data, "Solicitante", numero_sol, mensagem_notif)
                                add_notification(data, "Suprimentos", numero_sol, mensagem_notif)
                            except:
                                pass
                            
                            # Salva no banco se disponível
                            if USE_DATABASE:
                                try:
                                    db = get_database()
                                    if db.db_available:
                                        updates = {
                                            "status": data["solicitacoes"][j]["status"],
                                            "etapa_atual": data["solicitacoes"][j]["etapa_atual"],
                                            "aprovacoes": data["solicitacoes"][j]["aprovacoes"],
                                            "historico_etapas": data["solicitacoes"][j]["historico_etapas"]
                                        }
                                        db.update_solicitacao(numero_sol, updates)
                                except Exception as e:
                                    st.error(f"Erro ao salvar no banco: {e}")
                            
                            break
                    
                    # Salva dados
                    save_data(data)
                    
                    if decisao == "Aprovar":
                        st.success(f"✅ Solicitação #{numero_sol} aprovada com sucesso!")
                        st.info(f"🔄 Status automaticamente alterado para 'Compra feita' - Aguardando próxima etapa de entrega.")
                    else:
                        st.warning(f"❌ Solicitação #{numero_sol} reprovada.")
                    
                    st.rerun()
    
    with tab2:
        st.markdown("### 📊 Resumo Financeiro das Aprovações Pendentes")
        
        # Calcula totais
        valor_total_pendente = 0
        valores_por_prioridade = {"Urgente": 0, "Alta": 0, "Normal": 0, "Baixa": 0}
        valores_por_departamento = {}
        
        for sol in solicitacoes_aprovacao:
            valor = sol.get('valor_estimado', 0) or 0
            valor_total_pendente += valor
            
            prioridade = sol.get('prioridade', 'Normal')
            if prioridade in valores_por_prioridade:
                valores_por_prioridade[prioridade] += valor
            
            dept = sol.get('departamento', 'Outro')
            valores_por_departamento[dept] = valores_por_departamento.get(dept, 0) + valor
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Pendente", format_brl(valor_total_pendente))
        with col2:
            st.metric("Solicitações", len(solicitacoes_aprovacao))
        with col3:
            urgentes = len([s for s in solicitacoes_aprovacao if s.get('prioridade') == 'Urgente'])
            st.metric("Urgentes", urgentes)
        with col4:
            altas = len([s for s in solicitacoes_aprovacao if s.get('prioridade') == 'Alta'])
            st.metric("Alta Prioridade", altas)
        
        # Gráficos por prioridade
        if valores_por_prioridade:
            st.markdown("#### 📈 Valores por Prioridade")
            prioridade_df = pd.DataFrame([
                {"Prioridade": k, "Valor": v, "Valor_Formatado": format_brl(v)}
                for k, v in valores_por_prioridade.items() if v > 0
            ])
            if not prioridade_df.empty:
                st.bar_chart(prioridade_df.set_index("Prioridade")["Valor"])
        
        # Valores por departamento
        if valores_por_departamento:
            st.markdown("#### 🏢 Valores por Departamento")
            dept_df = pd.DataFrame([
                {"Departamento": k, "Valor": format_brl(v), "Valor_Num": v}
                for k, v in valores_por_departamento.items()
            ]).sort_values("Valor_Num", ascending=False)
            st.dataframe(dept_df[["Departamento", "Valor"]], width='stretch')
