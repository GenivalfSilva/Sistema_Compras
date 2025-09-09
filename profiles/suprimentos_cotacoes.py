"""
Módulo para gerenciar múltiplas cotações por solicitação no perfil Suprimentos
Permite adicionar, comparar e selecionar a melhor cotação entre fornecedores
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
from typing import Dict, List

def gerenciar_cotacoes(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Interface para gerenciar múltiplas cotações por solicitação"""
    
    st.markdown("## 💰 Gerenciar Cotações de Fornecedores")
    
    # Importa funções necessárias
    from app import save_data, format_brl
    from database_local import get_local_database as get_database
    
    if USE_DATABASE:
        db = get_database()
    
    # Filtra solicitações em etapa de cotação
    solicitacoes_cotacao = []
    for sol in data.get("solicitacoes", []):
        etapa_atual = sol.get("etapa_atual", sol.get("status", ""))
        if etapa_atual in ["Suprimentos", "Em Cotação"]:
            solicitacoes_cotacao.append(sol)
    
    if not solicitacoes_cotacao:
        st.info("📋 Não há solicitações disponíveis para cotação no momento.")
        return
    
    st.success(f"💰 {len(solicitacoes_cotacao)} solicitação(ões) disponível(eis) para cotação")
    
    # Seleção da solicitação
    opcoes_solicitacao = [
        f"#{sol.get('numero_solicitacao_estoque')} - {sol.get('solicitante', 'N/A')} - {sol.get('descricao', 'N/A')[:50]}..."
        for sol in solicitacoes_cotacao
    ]
    
    solicitacao_selecionada = st.selectbox(
        "📋 Selecione a Solicitação:",
        options=range(len(opcoes_solicitacao)),
        format_func=lambda x: opcoes_solicitacao[x]
    )
    
    if solicitacao_selecionada is not None:
        sol_dados = solicitacoes_cotacao[solicitacao_selecionada]
        numero_solicitacao = sol_dados.get('numero_solicitacao_estoque')
        
        # Exibe informações da solicitação
        with st.expander("📋 Detalhes da Solicitação", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Número:** {numero_solicitacao}")
                st.markdown(f"**Solicitante:** {sol_dados.get('solicitante', 'N/A')}")
                st.markdown(f"**Departamento:** {sol_dados.get('departamento', 'N/A')}")
            
            with col2:
                st.markdown(f"**Prioridade:** {sol_dados.get('prioridade', 'N/A')}")
                st.markdown(f"**Etapa Atual:** {sol_dados.get('etapa_atual', 'N/A')}")
                req_numero = sol_dados.get('numero_requisicao')
                st.markdown(f"**Req. Nº:** {req_numero if req_numero else 'N/A'}")
            
            with col3:
                valor_estimado = sol_dados.get('valor_estimado')
                st.markdown(f"**Valor Estimado:** {format_brl(valor_estimado) if valor_estimado else 'N/A'}")
                st.markdown(f"**Data Solicitação:** {sol_dados.get('data_solicitacao', 'N/A')}")
            
            # Descrição
            if sol_dados.get('descricao'):
                st.markdown("**Descrição:**")
                st.info(sol_dados.get('descricao'))
            
            # Itens solicitados
            try:
                itens = json.loads(sol_dados.get('itens', '[]'))
                if itens:
                    st.markdown("**📦 Itens Solicitados:**")
                    df_itens = pd.DataFrame(itens)
                    st.dataframe(df_itens, width='stretch')
            except:
                pass
        
        st.markdown("---")
        
        # Gerenciar cotações
        tabs = st.tabs(["💰 Cotações Atuais", "➕ Nova Cotação", "🏆 Comparar e Selecionar"])
        
        with tabs[0]:
            mostrar_cotacoes_atuais(sol_dados)
        
        with tabs[1]:
            adicionar_nova_cotacao(sol_dados, data, usuario, USE_DATABASE)
        
        with tabs[2]:
            comparar_selecionar_cotacao(sol_dados, data, usuario, USE_DATABASE)

def mostrar_cotacoes_atuais(sol_dados: Dict):
    """Mostra cotações já cadastradas para a solicitação"""
    
    st.markdown("### 💰 Cotações Cadastradas")
    
    try:
        cotacoes_str = sol_dados.get('cotacoes', '[]')
        cotacoes = json.loads(cotacoes_str) if cotacoes_str else []
    except:
        cotacoes = []
    
    if not cotacoes:
        st.info("📝 Nenhuma cotação cadastrada ainda.")
        return
    
    # Exibe cotações em cards
    for i, cotacao in enumerate(cotacoes):
        with st.expander(f"🏢 {cotacao.get('fornecedor', 'Fornecedor')} - {format_brl(cotacao.get('valor_total', 0))}", 
                        expanded=len(cotacoes) <= 3):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Fornecedor:** {cotacao.get('fornecedor', 'N/A')}")
                st.markdown(f"**Valor Total:** {format_brl(cotacao.get('valor_total', 0))}")
                st.markdown(f"**Prazo Entrega:** {cotacao.get('prazo_entrega', 'N/A')} dias")
            
            with col2:
                st.markdown(f"**Data Cotação:** {cotacao.get('data_cotacao', 'N/A')}")
                st.markdown(f"**Condições Pagamento:** {cotacao.get('condicoes_pagamento', 'N/A')}")
                st.markdown(f"**Status:** {cotacao.get('status', 'Pendente')}")
            
            if cotacao.get('observacoes'):
                st.markdown("**Observações:**")
                st.write(cotacao.get('observacoes'))
            
            # Itens da cotação
            if cotacao.get('itens_cotacao'):
                st.markdown("**📦 Itens Cotados:**")
                try:
                    df_itens = pd.DataFrame(cotacao['itens_cotacao'])
                    st.dataframe(df_itens, width='stretch')
                except:
                    pass

def adicionar_nova_cotacao(sol_dados: Dict, data: Dict, usuario: Dict, USE_DATABASE: bool):
    """Interface para adicionar nova cotação"""
    
    st.markdown("### ➕ Adicionar Nova Cotação")
    
    with st.form("nova_cotacao_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            fornecedor = st.text_input(
                "Fornecedor*",
                placeholder="Nome da empresa fornecedora"
            )
            
            valor_total = st.number_input(
                "Valor Total (R$)*",
                min_value=0.0,
                step=0.01,
                format="%.2f"
            )
            
            prazo_entrega = st.number_input(
                "Prazo de Entrega (dias)*",
                min_value=1,
                value=15
            )
        
        with col2:
            data_cotacao = st.date_input(
                "Data da Cotação*",
                value=date.today()
            )
            
            condicoes_pagamento = st.selectbox(
                "Condições de Pagamento*",
                ["À vista", "30 dias", "45 dias", "60 dias", "90 dias", "Parcelado"]
            )
            
            numero_cotacao = st.text_input(
                "Número da Cotação",
                placeholder="Ex: COT-2024-001"
            )
        
        observacoes = st.text_area(
            "Observações",
            placeholder="Informações adicionais sobre a cotação...",
            height=100
        )
        
        # Detalhamento por item (opcional)
        st.markdown("#### 📦 Detalhamento por Item (Opcional)")
        
        try:
            itens_solicitacao = json.loads(sol_dados.get('itens', '[]'))
            if itens_solicitacao:
                st.info("💡 Preencha os valores unitários para cada item ou deixe em branco para usar o valor total.")
                
                itens_cotacao = []
                for i, item in enumerate(itens_solicitacao):
                    col_item1, col_item2, col_item3 = st.columns(3)
                    
                    with col_item1:
                        st.write(f"**{item.get('codigo', 'N/A')}**")
                        st.write(f"{item.get('descricao', 'N/A')}")
                    
                    with col_item2:
                        qtd = item.get('quantidade', 1)
                        st.write(f"Qtd: {qtd}")
                    
                    with col_item3:
                        valor_unitario = st.number_input(
                            f"Valor Unit. (R$)",
                            min_value=0.0,
                            step=0.01,
                            key=f"valor_unit_{i}",
                            format="%.2f"
                        )
                        
                        if valor_unitario > 0:
                            itens_cotacao.append({
                                'codigo': item.get('codigo'),
                                'descricao': item.get('descricao'),
                                'quantidade': qtd,
                                'valor_unitario': valor_unitario,
                                'valor_total': valor_unitario * qtd
                            })
        except:
            itens_cotacao = []
        
        salvar_cotacao = st.form_submit_button(
            "💾 Salvar Cotação",
            type="primary"
        )
        
        if salvar_cotacao:
            if fornecedor and valor_total > 0:
                # Cria nova cotação
                nova_cotacao = {
                    'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                    'fornecedor': fornecedor,
                    'valor_total': valor_total,
                    'prazo_entrega': prazo_entrega,
                    'data_cotacao': data_cotacao.strftime('%d/%m/%Y'),
                    'condicoes_pagamento': condicoes_pagamento,
                    'numero_cotacao': numero_cotacao,
                    'observacoes': observacoes,
                    'status': 'Pendente',
                    'responsavel': usuario.get('nome', usuario.get('username')),
                    'data_cadastro': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'itens_cotacao': itens_cotacao if itens_cotacao else []
                }
                
                # Adiciona à lista de cotações
                try:
                    cotacoes_str = sol_dados.get('cotacoes', '[]')
                    cotacoes = json.loads(cotacoes_str) if cotacoes_str else []
                except:
                    cotacoes = []
                
                cotacoes.append(nova_cotacao)
                
                # Atualiza solicitação
                numero_solicitacao = sol_dados.get('numero_solicitacao_estoque')
                for i, s in enumerate(data["solicitacoes"]):
                    if s["numero_solicitacao_estoque"] == numero_solicitacao:
                        data["solicitacoes"][i]["cotacoes"] = json.dumps(cotacoes)
                        data["solicitacoes"][i]["etapa_atual"] = "Em Cotação"
                        data["solicitacoes"][i]["status"] = "Em Cotação"
                        break
                
                # Salva no banco se disponível
                if USE_DATABASE:
                    try:
                        from database_local import get_local_database
                        db = get_local_database()
                        if db.db_available:
                            updates = {
                                "cotacoes": json.dumps(cotacoes),
                                "etapa_atual": "Em Cotação",
                                "status": "Em Cotação"
                            }
                            db.update_solicitacao(numero_solicitacao, updates)
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
                
                save_data(data)
                st.success(f"✅ Cotação de {fornecedor} adicionada com sucesso!")
                st.rerun()
            else:
                st.error("❌ Preencha os campos obrigatórios (Fornecedor e Valor Total)")

def comparar_selecionar_cotacao(sol_dados: Dict, data: Dict, usuario: Dict, USE_DATABASE: bool):
    """Interface para comparar cotações e selecionar a melhor"""
    
    st.markdown("### 🏆 Comparar e Selecionar Melhor Cotação")
    
    try:
        cotacoes_str = sol_dados.get('cotacoes', '[]')
        cotacoes = json.loads(cotacoes_str) if cotacoes_str else []
    except:
        cotacoes = []
    
    if len(cotacoes) < 2:
        st.info("📝 É necessário ter pelo menos 2 cotações para fazer comparação.")
        return
    
    # Tabela comparativa
    st.markdown("#### 📊 Tabela Comparativa")
    
    dados_comparacao = []
    for i, cotacao in enumerate(cotacoes):
        dados_comparacao.append({
            'ID': i,
            'Fornecedor': cotacao.get('fornecedor', 'N/A'),
            'Valor Total': f"R$ {cotacao.get('valor_total', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'Prazo (dias)': cotacao.get('prazo_entrega', 'N/A'),
            'Condições': cotacao.get('condicoes_pagamento', 'N/A'),
            'Data Cotação': cotacao.get('data_cotacao', 'N/A'),
            'Status': cotacao.get('status', 'Pendente')
        })
    
    df_comparacao = pd.DataFrame(dados_comparacao)
    st.dataframe(df_comparacao, width='stretch')
    
    # Seleção da melhor cotação
    st.markdown("#### 🎯 Selecionar Cotação Vencedora")
    
    opcoes_cotacao = [
        f"{cotacao.get('fornecedor')} - {format_brl(cotacao.get('valor_total', 0))} - {cotacao.get('prazo_entrega')} dias"
        for cotacao in cotacoes
    ]
    
    cotacao_selecionada = st.selectbox(
        "Selecione a cotação vencedora:",
        options=range(len(opcoes_cotacao)),
        format_func=lambda x: opcoes_cotacao[x]
    )
    
    if cotacao_selecionada is not None:
        cotacao_vencedora = cotacoes[cotacao_selecionada]
        
        with st.expander("🏆 Cotação Selecionada", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Fornecedor:** {cotacao_vencedora.get('fornecedor')}")
                st.markdown(f"**Valor Total:** {format_brl(cotacao_vencedora.get('valor_total', 0))}")
                st.markdown(f"**Prazo:** {cotacao_vencedora.get('prazo_entrega')} dias")
            
            with col2:
                st.markdown(f"**Condições:** {cotacao_vencedora.get('condicoes_pagamento')}")
                st.markdown(f"**Data Cotação:** {cotacao_vencedora.get('data_cotacao')}")
        
        justificativa = st.text_area(
            "Justificativa da Escolha*",
            placeholder="Explique por que esta cotação foi selecionada...",
            height=100
        )
        
        if st.button("🏆 Confirmar Seleção e Enviar para Aprovação", type="primary"):
            if justificativa.strip():
                # Atualiza cotação selecionada
                for cotacao in cotacoes:
                    cotacao['status'] = 'Rejeitada'
                
                cotacoes[cotacao_selecionada]['status'] = 'Selecionada'
                
                # Atualiza solicitação
                numero_solicitacao = sol_dados.get('numero_solicitacao_estoque')
                for i, s in enumerate(data["solicitacoes"]):
                    if s["numero_solicitacao_estoque"] == numero_solicitacao:
                        data["solicitacoes"][i]["cotacoes"] = json.dumps(cotacoes)
                        data["solicitacoes"][i]["fornecedor_recomendado"] = cotacao_vencedora.get('fornecedor')
                        data["solicitacoes"][i]["valor_estimado"] = cotacao_vencedora.get('valor_total')
                        data["solicitacoes"][i]["etapa_atual"] = "Aguardando Aprovação"
                        data["solicitacoes"][i]["status"] = "Aguardando Aprovação"
                        data["solicitacoes"][i]["justificativa_cotacao"] = justificativa
                        
                        # Adiciona ao histórico
                        historico_atual = s.get('historico_etapas', '[]')
                        try:
                            historico = json.loads(historico_atual) if historico_atual else []
                        except:
                            historico = []
                        
                        historico.append({
                            'etapa': 'Aguardando Aprovação',
                            'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                            'usuario': usuario.get('nome', usuario.get('username')),
                            'observacao': f'Cotação selecionada: {cotacao_vencedora.get("fornecedor")} - {format_brl(cotacao_vencedora.get("valor_total", 0))}'
                        })
                        data["solicitacoes"][i]["historico_etapas"] = json.dumps(historico)
                        break
                
                # Salva no banco se disponível
                if USE_DATABASE:
                    try:
                        from database_local import get_local_database
                        db = get_local_database()
                        if db.db_available:
                            updates = {
                                "cotacoes": json.dumps(cotacoes),
                                "fornecedor_recomendado": cotacao_vencedora.get('fornecedor'),
                                "valor_estimado": cotacao_vencedora.get('valor_total'),
                                "etapa_atual": "Aguardando Aprovação",
                                "status": "Aguardando Aprovação",
                                "justificativa": justificativa,
                                "historico_etapas": json.dumps(historico)
                            }
                            db.update_solicitacao(numero_solicitacao, updates)
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
                
                save_data(data)
                st.success("🏆 Cotação selecionada! Solicitação enviada para aprovação da Diretoria.")
                st.rerun()
            else:
                st.error("❌ A justificativa da escolha é obrigatória.")
