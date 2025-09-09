"""
Módulo para requisição de estoque do perfil Suprimentos
Contém: Visualizar solicitações, lançar requisição interna, gerenciar cotações
"""

import streamlit as st
import pandas as pd
import datetime
from datetime import date
from typing import Dict

def requisicao_estoque(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Página de requisição de estoque para perfil Suprimentos"""
    st.markdown("## 📑 Requisição (Estoque)")
    
    # Importa funções necessárias
    from app import save_data, add_notification, format_brl
    from database_local import get_local_database as get_database
    
    # Filtra solicitações na etapa de Suprimentos
    solicitacoes_suprimentos = []
    for sol in data.get("solicitacoes", []):
        if sol.get("status") == "Suprimentos" or sol.get("etapa_atual") == "Suprimentos":
            solicitacoes_suprimentos.append(sol)
    
    if not solicitacoes_suprimentos:
        st.info("📋 Não há solicitações na etapa de Suprimentos no momento.")
        return
    
    st.success(f"📋 {len(solicitacoes_suprimentos)} solicitação(ões) na etapa de Suprimentos")
    
    # Tabs para organizar funcionalidades
    tab1, tab2 = st.tabs(["📑 Lançar Requisições", "💰 Gerenciar Cotações"])
    
    with tab1:
        st.markdown("### 📑 Lançar Requisições Internas")
        
        for sol in solicitacoes_suprimentos:
            numero_solicitacao = sol.get("numero_solicitacao_estoque")
            
            with st.expander(f"📄 Solicitação #{numero_solicitacao} - {sol.get('solicitante', 'N/A')}", 
                           expanded=not sol.get('numero_requisicao_interno')):
                
                # Informações da solicitação
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
                    req_interno = sol.get('numero_requisicao_interno')
                    status_req = "✅ Lançada" if req_interno else "⏳ Pendente"
                    st.markdown(f"**Req. Interna:** {req_interno if req_interno else 'Não lançada'}")
                    st.markdown(f"**Status:** {status_req}")
                    st.markdown(f"**Local Aplicação:** {sol.get('local_aplicacao', 'N/A')}")
                
                # Descrição
                st.markdown("**Descrição:**")
                st.info(sol.get('descricao', 'Sem descrição'))
                
                # Itens solicitados
                if sol.get('itens'):
                    st.markdown("### 📦 Itens Solicitados")
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
                
                # Anexos
                if sol.get('anexos_requisicao'):
                    st.markdown("### 📎 Anexos da Requisição")
                    st.info(f"📁 {len(sol['anexos_requisicao'])} arquivo(s) anexado(s)")
                    for anexo in sol['anexos_requisicao']:
                        st.write(f"• {anexo}")
                
                st.markdown("---")
                
                # Formulário para lançar requisição interna
                if not sol.get('numero_requisicao_interno'):
                    st.markdown("### 📝 Lançar Requisição Interna")
                    
                    # Chave única para o formulário baseada na solicitação
                    form_key = f"lancar_requisicao_form_{numero_solicitacao}"
                    
                    with st.form(form_key):
                        col1, col2 = st.columns(2)
                        with col1:
                            # Limpa o campo se uma nova solicitação foi selecionada
                            default_req = ""
                            if f"selected_sol_{numero_solicitacao}" not in st.session_state:
                                st.session_state[f"selected_sol_{numero_solicitacao}"] = True
                            
                            num_req = st.text_input("Nº Requisição Interna*", 
                                                   value=default_req,
                                                   placeholder="Ex: REQ-2024-001",
                                                   key=f"num_req_{numero_solicitacao}")
                            data_req = st.date_input("Data Requisição*", 
                                                    value=date.today(),
                                                    key=f"data_req_{numero_solicitacao}")
                        with col2:
                            resp = st.text_input("Responsável (Suprimentos)", 
                                                value=usuario.get('nome', ''),
                                                key=f"resp_{numero_solicitacao}")
                            obs_req = st.text_area("Observações", height=100,
                                                 placeholder="Observações sobre a requisição...",
                                                 key=f"obs_req_{numero_solicitacao}")
                        
                        confirmar = st.form_submit_button("💾 Salvar e Enviar para Cotação", 
                                                         type="primary")
                    
                    if confirmar:
                        if num_req.strip():
                            # Atualiza a solicitação
                            for i, s in enumerate(data["solicitacoes"]):
                                if s["numero_solicitacao_estoque"] == numero_solicitacao:
                                    data["solicitacoes"][i]["numero_requisicao_interno"] = num_req.strip()
                                    data["solicitacoes"][i]["data_requisicao_interna"] = data_req.isoformat()
                                    if resp:
                                        data["solicitacoes"][i]["responsavel_suprimentos"] = resp
                                    data["solicitacoes"][i]["observacoes"] = obs_req or s.get("observacoes")
                                    
                                    # Muda etapa para Em Cotação
                                    data["solicitacoes"][i]["status"] = "Em Cotação"
                                    data["solicitacoes"][i]["etapa_atual"] = "Em Cotação"
                                    data["solicitacoes"][i]["historico_etapas"].append({
                                        "etapa": "Em Cotação",
                                        "data_entrada": datetime.datetime.now().isoformat(),
                                        "usuario": usuario.get('nome', usuario.get('username'))
                                    })
                                    
                                    # Limpa os campos do formulário após salvar
                                    for key in list(st.session_state.keys()):
                                        if key.startswith(f"num_req_{numero_solicitacao}") or \
                                           key.startswith(f"data_req_{numero_solicitacao}") or \
                                           key.startswith(f"obs_req_{numero_solicitacao}"):
                                            del st.session_state[key]
                                    
                                    try:
                                        add_notification(data, "Suprimentos", numero_solicitacao, 
                                                       "Requisição interna lançada e disponível para cotação.")
                                    except:
                                        pass
                                    
                                    # Salva no banco se disponível
                                    if USE_DATABASE:
                                        try:
                                            db = get_database()
                                            if db.db_available:
                                                updates = {
                                                    "numero_requisicao_interno": data["solicitacoes"][i]["numero_requisicao_interno"],
                                                    "data_requisicao_interna": data["solicitacoes"][i]["data_requisicao_interna"],
                                                    "status": "Em Cotação",
                                                    "etapa_atual": "Em Cotação",
                                                    "historico_etapas": data["solicitacoes"][i]["historico_etapas"]
                                                }
                                                if resp:
                                                    updates["responsavel_suprimentos"] = resp
                                                if obs_req:
                                                    updates["observacoes"] = obs_req
                                                db.update_solicitacao(numero_solicitacao, updates)
                                        except Exception as e:
                                            st.error(f"Erro ao salvar no banco: {e}")
                                    
                                    break
                            
                            save_data(data)
                            st.success(f"✅ Requisição interna #{num_req} lançada com sucesso!")
                            st.rerun()
                        else:
                            st.error("❌ Digite o número da requisição interna.")
                else:
                    # Mostra informações da requisição já lançada
                    st.markdown("### ✅ Requisição Interna Lançada")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**Nº Requisição:** {sol.get('numero_requisicao_interno')}")
                        st.info(f"**Data:** {sol.get('data_requisicao_interna', 'N/A')}")
                    with col2:
                        st.info(f"**Responsável:** {sol.get('responsavel_suprimentos', 'N/A')}")
                        if sol.get('observacoes'):
                            st.info(f"**Observações:** {sol.get('observacoes')}")
    
    with tab2:
        st.markdown("### 💰 Gerenciar Cotações")
        
        # Filtra solicitações em cotação
        solicitacoes_cotacao = []
        for sol in data.get("solicitacoes", []):
            if sol.get("status") == "Em Cotação" or sol.get("etapa_atual") == "Em Cotação":
                solicitacoes_cotacao.append(sol)
        
        if not solicitacoes_cotacao:
            st.info("📋 Não há solicitações em processo de cotação no momento.")
            return
        
        st.success(f"💰 {len(solicitacoes_cotacao)} solicitação(ões) em processo de cotação")
        
        for sol in solicitacoes_cotacao:
            numero_solicitacao = sol.get("numero_solicitacao_estoque")
            
            with st.expander(f"💰 Cotação #{numero_solicitacao} - {sol.get('solicitante', 'N/A')}"):
                
                # Informações básicas
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Req. Interna:** {sol.get('numero_requisicao_interno', 'N/A')}")
                    st.markdown(f"**Solicitante:** {sol.get('solicitante', 'N/A')}")
                    st.markdown(f"**Departamento:** {sol.get('departamento', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Prioridade:** {sol.get('prioridade', 'N/A')}")
                    valor_est = sol.get('valor_estimado')
                    st.markdown(f"**Valor Estimado:** {format_brl(valor_est) if valor_est else 'N/A'}")
                    cotacoes_count = len(sol.get('cotacoes', []))
                    st.markdown(f"**Cotações:** {cotacoes_count}")
                
                # Cotações existentes
                cotacoes = sol.get('cotacoes', [])
                if cotacoes:
                    st.markdown("#### 📋 Cotações Recebidas")
                    cotacoes_df = []
                    for idx, cot in enumerate(cotacoes, 1):
                        cotacoes_df.append({
                            "Nº": idx,
                            "Fornecedor": cot.get('fornecedor', 'N/A'),
                            "Valor": format_brl(cot.get('valor')),
                            "Prazo": f"{cot.get('prazo_entrega', 'N/A')} dias",
                            "Data": cot.get('data_cotacao', 'N/A')[:10] if cot.get('data_cotacao') else 'N/A',
                            "Observações": cot.get('observacoes', '')[:30] + '...' if len(cot.get('observacoes', '')) > 30 else cot.get('observacoes', '')
                        })
                    st.dataframe(pd.DataFrame(cotacoes_df), width='stretch')
                
                # Formulário para adicionar nova cotação
                st.markdown("#### ➕ Adicionar Nova Cotação")
                
                with st.form(f"nova_cotacao_form_{numero_solicitacao}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        fornecedor = st.text_input("Fornecedor*", placeholder="Nome do fornecedor")
                        valor_cotacao = st.number_input("Valor Total (R$)*", min_value=0.0, step=0.01)
                    
                    with col2:
                        prazo_entrega = st.number_input("Prazo Entrega (dias)*", min_value=1, step=1)
                        data_cotacao = st.date_input("Data da Cotação", value=date.today())
                    
                    with col3:
                        observacoes_cot = st.text_area("Observações", height=100,
                                                     placeholder="Condições, observações...")
                    
                    adicionar_cotacao = st.form_submit_button("➕ Adicionar Cotação", type="primary")
                
                if adicionar_cotacao:
                    if fornecedor.strip() and valor_cotacao > 0 and prazo_entrega > 0:
                        # Adiciona nova cotação
                        nova_cotacao = {
                            "fornecedor": fornecedor.strip(),
                            "valor": valor_cotacao,
                            "prazo_entrega": prazo_entrega,
                            "data_cotacao": data_cotacao.isoformat(),
                            "observacoes": observacoes_cot.strip(),
                            "usuario_cotacao": usuario.get('nome', usuario.get('username'))
                        }
                        
                        for i, s in enumerate(data["solicitacoes"]):
                            if s["numero_solicitacao_estoque"] == numero_solicitacao:
                                data["solicitacoes"][i].setdefault("cotacoes", []).append(nova_cotacao)
                                
                                # Salva no banco se disponível
                                if USE_DATABASE:
                                    try:
                                        db = get_database()
                                        if db.db_available:
                                            updates = {
                                                "cotacoes": data["solicitacoes"][i]["cotacoes"]
                                            }
                                            db.update_solicitacao(numero_solicitacao, updates)
                                    except Exception as e:
                                        st.error(f"Erro ao salvar no banco: {e}")
                                
                                break
                        
                        save_data(data)
                        st.success(f"✅ Cotação de {fornecedor} adicionada com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios.")
                
                # Botão para enviar para aprovação (se tiver cotações suficientes)
                min_cotacoes = data.get("configuracoes", {}).get("suprimentos_min_cotacoes", 1)
                cotacoes_atuais = len(sol.get('cotacoes', []))
                
                if cotacoes_atuais >= min_cotacoes:
                    st.markdown("---")
                    st.markdown("#### 🎯 Finalizar Cotação")
                    
                    # Seleção do fornecedor recomendado
                    fornecedores = [cot.get('fornecedor', '') for cot in sol.get('cotacoes', [])]
                    if fornecedores:
                        with st.form(f"finalizar_cotacao_form_{numero_solicitacao}"):
                            fornecedor_recomendado = st.selectbox(
                                "Fornecedor Recomendado*",
                                fornecedores,
                                help="Selecione o fornecedor recomendado para aprovação"
                            )
                            
                            justificativa_recomendacao = st.text_area(
                                "Justificativa da Recomendação",
                                height=100,
                                placeholder="Explique por que este fornecedor foi escolhido..."
                            )
                            
                            enviar_aprovacao = st.form_submit_button(
                                "📤 Enviar para Aprovação",
                                type="primary"
                            )
                        
                        if enviar_aprovacao and fornecedor_recomendado:
                            # Atualiza solicitação para aprovação
                            for i, s in enumerate(data["solicitacoes"]):
                                if s["numero_solicitacao_estoque"] == numero_solicitacao:
                                    data["solicitacoes"][i]["fornecedor_recomendado"] = fornecedor_recomendado
                                    data["solicitacoes"][i]["justificativa_recomendacao"] = justificativa_recomendacao
                                    data["solicitacoes"][i]["status"] = "Aguardando Aprovação"
                                    data["solicitacoes"][i]["etapa_atual"] = "Aguardando Aprovação"
                                    
                                    # Adiciona ao histórico
                                    data["solicitacoes"][i]["historico_etapas"].append({
                                        "etapa": "Aguardando Aprovação",
                                        "data_entrada": datetime.datetime.now().isoformat(),
                                        "usuario": usuario.get('nome', usuario.get('username')),
                                        "observacoes": f"Fornecedor recomendado: {fornecedor_recomendado}"
                                    })
                                    
                                    # Notifica diretoria
                                    try:
                                        add_notification(data, "Gerência&Diretoria", numero_solicitacao,
                                                       f"Solicitação com cotações finalizadas aguarda aprovação. Fornecedor recomendado: {fornecedor_recomendado}")
                                    except:
                                        pass
                                    
                                    # Salva no banco se disponível
                                    if USE_DATABASE:
                                        try:
                                            db = get_database()
                                            if db.db_available:
                                                updates = {
                                                    "fornecedor_recomendado": fornecedor_recomendado,
                                                    "justificativa_recomendacao": justificativa_recomendacao,
                                                    "status": "Aguardando Aprovação",
                                                    "etapa_atual": "Aguardando Aprovação",
                                                    "historico_etapas": data["solicitacoes"][i]["historico_etapas"]
                                                }
                                                db.update_solicitacao(numero_solicitacao, updates)
                                        except Exception as e:
                                            st.error(f"Erro ao salvar no banco: {e}")
                                    
                                    break
                            
                            save_data(data)
                            st.success(f"✅ Solicitação #{numero_solicitacao} enviada para aprovação!")
                            st.rerun()
                else:
                    st.warning(f"⚠️ Necessário pelo menos {min_cotacoes} cotação(ões) para enviar para aprovação. Atual: {cotacoes_atuais}")
