import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
from database_local import get_local_database as get_database
from style import get_custom_css, get_section_header_html, get_form_container_start, get_form_container_end

def show_suprimentos_requisicoes():
    """Interface para Suprimentos - Processamento de Requisições"""
    
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Header da seção
    st.markdown(get_section_header_html("🏭 Suprimentos - Processamento de Requisições"), unsafe_allow_html=True)
    
    # Tabs para organizar as funcionalidades
    tab1, tab2, tab3 = st.tabs(["📋 Requisições Pendentes", "💰 Criar Pedido de Compras", "📊 Dashboard"])
    
    with tab1:
        show_requisicoes_pendentes()
    
    with tab2:
        show_criar_pedido_compras()
    
    with tab3:
        show_dashboard_suprimentos()

def show_requisicoes_pendentes():
    """Mostra requisições pendentes de processamento"""
    
    st.markdown("### 📋 Requisições Aguardando Processamento")
    st.markdown("**Fluxo:** Solicitação → Requisição → **Suprimentos** → Em Cotação → Pedido de Compras")
    
    db = get_database()
    if not db.db_available:
        st.error("❌ Banco de dados não disponível")
        return
    
    # Buscar requisições na etapa "Requisição" (aguardando processamento por suprimentos)
    solicitacoes = db.get_all_solicitacoes()
    requisicoes_pendentes = [s for s in solicitacoes if s.get('etapa_atual') == 'Requisição']
    
    if not requisicoes_pendentes:
        st.info("✅ Não há requisições pendentes de processamento no momento.")
        return
    
    st.success(f"📋 {len(requisicoes_pendentes)} requisição(ões) aguardando processamento")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_prioridade = st.selectbox(
            "Filtrar por Prioridade:",
            options=["Todas", "Urgente", "Alta", "Normal", "Baixa"],
            key="filtro_prior_req_pend"
        )
    
    with col2:
        filtro_departamento = st.selectbox(
            "Filtrar por Departamento:",
            options=["Todos"] + list(set([r.get('departamento', '') for r in requisicoes_pendentes])),
            key="filtro_dept_req_pend"
        )
    
    with col3:
        ordenar_por = st.selectbox(
            "Ordenar por:",
            options=["Prioridade", "Data Requisição", "Solicitante"],
            key="ordenar_req_pend"
        )
    
    # Aplicar filtros
    requisicoes_filtradas = requisicoes_pendentes
    if filtro_prioridade != "Todas":
        requisicoes_filtradas = [r for r in requisicoes_filtradas if r.get('prioridade') == filtro_prioridade]
    if filtro_departamento != "Todos":
        requisicoes_filtradas = [r for r in requisicoes_filtradas if r.get('departamento') == filtro_departamento]
    
    # Ordenar por prioridade (Urgente primeiro)
    if ordenar_por == "Prioridade":
        ordem_prioridade = {"Urgente": 0, "Alta": 1, "Normal": 2, "Baixa": 3}
        requisicoes_filtradas.sort(key=lambda x: ordem_prioridade.get(x.get('prioridade', 'Normal'), 2))
    elif ordenar_por == "Data Requisição":
        requisicoes_filtradas.sort(key=lambda x: x.get('data_requisicao', ''), reverse=True)
    else:  # Solicitante
        requisicoes_filtradas.sort(key=lambda x: x.get('solicitante', ''))
    
    # Exibir requisições
    for req in requisicoes_filtradas:
        numero_solicitacao = req.get('numero_solicitacao_estoque')
        numero_requisicao = req.get('numero_requisicao')
        prioridade_icon = {"Urgente": "🔴", "Alta": "🟡", "Normal": "🔵", "Baixa": "🟢"}.get(req.get('prioridade', 'Normal'), "🔵")
        
        with st.expander(f"{prioridade_icon} Req. {numero_requisicao} - Sol. {numero_solicitacao} - {req.get('solicitante')}", 
                       expanded=len(requisicoes_filtradas) <= 3):
            
            # Informações da requisição
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📋 Dados da Solicitação:**")
                st.write(f"**Número Solicitação:** {numero_solicitacao}")
                st.write(f"**Solicitante:** {req.get('solicitante')}")
                st.write(f"**Departamento:** {req.get('departamento')}")
                st.write(f"**Prioridade:** {prioridade_icon} {req.get('prioridade')}")
                st.write(f"**Data Solicitação:** {req.get('carimbo_data_hora', '')[:10]}")
            
            with col2:
                st.markdown("**🏭 Dados da Requisição:**")
                st.write(f"**Número Requisição:** {numero_requisicao}")
                st.write(f"**Data Requisição:** {req.get('data_requisicao', '')}")
                st.write(f"**Responsável Estoque:** {req.get('responsavel_estoque', '')}")
                st.write(f"**Local Aplicação:** {req.get('local_aplicacao')}")
                st.write(f"**SLA:** {req.get('sla_dias')} dias")
            
            # Descrição
            st.markdown("**📝 Descrição:**")
            st.info(req.get('descricao', ''))
            
            # Observações da requisição
            if req.get('observacoes_requisicao'):
                st.markdown("**💬 Observações da Requisição:**")
                st.info(req.get('observacoes_requisicao'))
            
            # Mostrar itens se existirem
            if req.get('itens'):
                try:
                    itens = json.loads(req.get('itens', '[]')) if isinstance(req.get('itens'), str) else req.get('itens', [])
                    if itens:
                        st.markdown("**📦 Itens Solicitados:**")
                        df_itens = pd.DataFrame(itens)
                        st.dataframe(df_itens, use_container_width=True)
                except:
                    pass
            
            st.markdown("---")
            
            # Formulário para processar requisição
            st.markdown("### 🏭 Processar Requisição")
            
            with st.form(f"processar_requisicao_{numero_solicitacao}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    responsavel_suprimentos = st.text_input(
                        "Responsável Suprimentos:",
                        value=st.session_state.get('user_data', {}).get('nome', ''),
                        help="Nome do responsável de suprimentos que processará a requisição"
                    )
                    
                    valor_estimado = st.number_input(
                        "Valor Estimado (R$):",
                        min_value=0.0,
                        value=float(req.get('valor_estimado', 0)) if req.get('valor_estimado') else 0.0,
                        step=0.01,
                        help="Estimativa inicial de valor para a cotação"
                    )
                
                with col2:
                    proxima_etapa = st.selectbox(
                        "Próxima Etapa:",
                        options=["Suprimentos", "Em Cotação"],
                        index=0,
                        help="Para onde enviar a requisição após processamento"
                    )
                    
                    min_cotacoes = st.number_input(
                        "Mínimo de Cotações:",
                        min_value=1,
                        max_value=5,
                        value=3,
                        help="Número mínimo de cotações necessárias"
                    )
                
                observacoes_suprimentos = st.text_area(
                    "Observações do Processamento:",
                    placeholder="Observações sobre o processamento da requisição...",
                    help="Informações adicionais sobre o processamento"
                )
                
                processar_req = st.form_submit_button(
                    f"🏭 Processar Requisição → {proxima_etapa}",
                    type="primary"
                )
                
                if processar_req:
                    if responsavel_suprimentos.strip():
                        # Atualizar requisição
                        updates = {
                            'responsavel_suprimentos': responsavel_suprimentos.strip(),
                            'valor_estimado': valor_estimado,
                            'etapa_atual': proxima_etapa,
                            'status': f'Em {proxima_etapa}'
                        }
                        
                        if observacoes_suprimentos:
                            updates['observacoes'] = observacoes_suprimentos
                        
                        # Atualizar histórico
                        historico_atual = req.get('historico_etapas', '[]')
                        try:
                            historico = json.loads(historico_atual) if historico_atual else []
                        except:
                            historico = []
                        
                        historico.append({
                            'etapa': proxima_etapa,
                            'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                            'usuario': responsavel_suprimentos,
                            'observacao': f'Requisição processada por suprimentos - Min. {min_cotacoes} cotações'
                        })
                        updates['historico_etapas'] = json.dumps(historico)
                        
                        # Salvar no banco
                        if db.update_solicitacao(numero_solicitacao, updates):
                            st.success(f"✅ Requisição {numero_requisicao} processada com sucesso!")
                            st.success(f"📤 Enviada para: {proxima_etapa}")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao processar requisição")
                    else:
                        st.error("❌ Preencha o responsável de suprimentos")

def show_criar_pedido_compras():
    """Interface para criar pedido de compras após cotação"""
    
    st.markdown("### 💰 Criar Pedido de Compras")
    st.markdown("**Fluxo:** Em Cotação → **Pedido de Compras** → Aguardando Aprovação")
    
    db = get_database()
    if not db.db_available:
        st.error("❌ Banco de dados não disponível")
        return
    
    # Buscar solicitações em cotação
    solicitacoes = db.get_all_solicitacoes()
    em_cotacao = [s for s in solicitacoes if s.get('etapa_atual') == 'Em Cotação']
    
    if not em_cotacao:
        st.info("📋 Não há cotações prontas para gerar pedido de compras.")
        return
    
    st.success(f"💰 {len(em_cotacao)} cotação(ões) disponível(eis) para pedido de compras")
    
    # Seletor de cotação
    opcoes_cotacao = []
    for cot in em_cotacao:
        prioridade_icon = {"Urgente": "🔴", "Alta": "🟡", "Normal": "🔵", "Baixa": "🟢"}.get(cot.get('prioridade', 'Normal'), "🔵")
        opcoes_cotacao.append(f"{prioridade_icon} Req. {cot.get('numero_requisicao')} - {cot.get('solicitante')} - {cot.get('descricao', '')[:50]}...")
    
    cotacao_selecionada = st.selectbox(
        "Selecione a cotação para criar pedido:",
        options=range(len(opcoes_cotacao)),
        format_func=lambda x: opcoes_cotacao[x]
    )
    
    if cotacao_selecionada is not None:
        cot_dados = em_cotacao[cotacao_selecionada]
        numero_solicitacao = cot_dados.get('numero_solicitacao_estoque')
        
        # Mostrar detalhes da cotação
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📋 Dados da Requisição:**")
            st.write(f"**Requisição:** {cot_dados.get('numero_requisicao')}")
            st.write(f"**Solicitante:** {cot_dados.get('solicitante')}")
            st.write(f"**Departamento:** {cot_dados.get('departamento')}")
            st.write(f"**Prioridade:** {cot_dados.get('prioridade')}")
        
        with col2:
            st.write(f"**Responsável Suprimentos:** {cot_dados.get('responsavel_suprimentos')}")
            st.write(f"**Valor Estimado:** R$ {cot_dados.get('valor_estimado', 0):,.2f}")
            st.write(f"**Data Requisição:** {cot_dados.get('data_requisicao', '')}")
        
        st.markdown("**Descrição:**")
        st.info(cot_dados.get('descricao', ''))
        
        st.markdown("---")
        
        # Formulário para criar pedido de compras
        st.markdown("### 💰 Dados do Pedido de Compras")
        
        with st.form(f"criar_pedido_compras_{numero_solicitacao}"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Gerar próximo número de pedido
                proximo_pedido = db.get_next_numero_pedido()
                numero_pedido_compras = st.number_input(
                    "Número do Pedido de Compras:",
                    value=proximo_pedido,
                    min_value=1,
                    help="Número do pedido de compras no sistema"
                )
                
                fornecedor_recomendado = st.text_input(
                    "Fornecedor Recomendado:",
                    placeholder="Nome do fornecedor selecionado",
                    help="Fornecedor escolhido após processo de cotação"
                )
            
            with col2:
                valor_final = st.number_input(
                    "Valor Final (R$):",
                    min_value=0.0,
                    value=float(cot_dados.get('valor_estimado', 0)) if cot_dados.get('valor_estimado') else 0.0,
                    step=0.01,
                    help="Valor final após cotação"
                )
                
                data_pedido = st.date_input(
                    "Data do Pedido:",
                    value=date.today(),
                    help="Data de criação do pedido de compras"
                )
            
            # Informações de cotação
            st.markdown("**📊 Informações da Cotação:**")
            col1, col2 = st.columns(2)
            
            with col1:
                num_cotacoes = st.number_input(
                    "Número de Cotações Realizadas:",
                    min_value=1,
                    value=3,
                    help="Quantas cotações foram realizadas"
                )
            
            with col2:
                criterio_escolha = st.selectbox(
                    "Critério de Escolha:",
                    options=["Menor Preço", "Melhor Prazo", "Qualidade", "Preço + Prazo", "Outros"],
                    help="Critério usado para escolher o fornecedor"
                )
            
            observacoes_pedido = st.text_area(
                "Observações do Pedido:",
                placeholder="Detalhes sobre a cotação, fornecedores consultados, critérios de escolha...",
                help="Informações detalhadas sobre o processo de cotação e criação do pedido"
            )
            
            criar_pedido = st.form_submit_button(
                "💰 Criar Pedido de Compras",
                type="primary"
            )
            
            if criar_pedido:
                if numero_pedido_compras and fornecedor_recomendado.strip() and valor_final > 0:
                    # Atualizar solicitação com dados do pedido
                    updates = {
                        'numero_pedido_compras': numero_pedido_compras,
                        'data_numero_pedido': data_pedido.strftime('%d/%m/%Y'),
                        'fornecedor_recomendado': fornecedor_recomendado.strip(),
                        'valor_final': valor_final,
                        'observacoes_pedido_compras': observacoes_pedido,
                        'etapa_atual': 'Pedido de Compras',
                        'status': 'Pedido de Compras Criado'
                    }
                    
                    # Atualizar histórico
                    historico_atual = cot_dados.get('historico_etapas', '[]')
                    try:
                        historico = json.loads(historico_atual) if historico_atual else []
                    except:
                        historico = []
                    
                    historico.append({
                        'etapa': 'Pedido de Compras',
                        'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                        'usuario': st.session_state.get('user_data', {}).get('nome', 'Suprimentos'),
                        'observacao': f'Pedido {numero_pedido_compras} criado - Fornecedor: {fornecedor_recomendado} - Valor: R$ {valor_final:,.2f}'
                    })
                    updates['historico_etapas'] = json.dumps(historico)
                    
                    # Salvar no banco
                    if db.update_solicitacao(numero_solicitacao, updates):
                        st.success(f"✅ Pedido de Compras {numero_pedido_compras} criado com sucesso!")
                        st.success(f"📤 Enviado para Aguardando Aprovação")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao criar pedido de compras")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios")

def show_dashboard_suprimentos():
    """Dashboard para suprimentos com métricas e estatísticas"""
    
    st.markdown("### 📊 Dashboard Suprimentos")
    
    db = get_database()
    if not db.db_available:
        st.error("❌ Banco de dados não disponível")
        return
    
    # Buscar todas as solicitações
    solicitacoes = db.get_all_solicitacoes()
    
    if not solicitacoes:
        st.info("📋 Nenhuma solicitação encontrada.")
        return
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        requisicoes_pendentes = len([s for s in solicitacoes if s.get('etapa_atual') == 'Requisição'])
        st.metric("Requisições Pendentes", requisicoes_pendentes)
    
    with col2:
        em_cotacao = len([s for s in solicitacoes if s.get('etapa_atual') == 'Em Cotação'])
        st.metric("Em Cotação", em_cotacao)
    
    with col3:
        pedidos_criados = len([s for s in solicitacoes if s.get('numero_pedido_compras')])
        st.metric("Pedidos Criados", pedidos_criados)
    
    with col4:
        valor_total = sum([s.get('valor_final', s.get('valor_estimado', 0)) or 0 for s in solicitacoes if s.get('etapa_atual') not in ['Solicitação', 'Requisição']])
        st.metric("Valor Total Processado", f"R$ {valor_total:,.2f}")
    
    # Gráfico de distribuição por etapas
    st.markdown("### 📈 Distribuição por Etapas")
    
    etapas_count = {}
    for sol in solicitacoes:
        etapa = sol.get('etapa_atual', 'Indefinido')
        etapas_count[etapa] = etapas_count.get(etapa, 0) + 1
    
    if etapas_count:
        df_etapas = pd.DataFrame([
            {"Etapa": etapa, "Quantidade": qtd}
            for etapa, qtd in etapas_count.items()
        ]).sort_values("Quantidade", ascending=True)
        
        st.bar_chart(df_etapas.set_index("Etapa")["Quantidade"])
    
    # Tabela de requisições por prioridade
    st.markdown("### 🎯 Requisições por Prioridade")
    
    requisicoes_ativas = [s for s in solicitacoes if s.get('etapa_atual') in ['Requisição', 'Suprimentos', 'Em Cotação', 'Pedido de Compras']]
    
    if requisicoes_ativas:
        dados_prioridade = []
        for req in requisicoes_ativas:
            prioridade_icon = {"Urgente": "🔴", "Alta": "🟡", "Normal": "🔵", "Baixa": "🟢"}.get(req.get('prioridade', 'Normal'), "🔵")
            
            dados_prioridade.append({
                "Prioridade": f"{prioridade_icon} {req.get('prioridade')}",
                "Requisição": req.get('numero_requisicao', 'N/A'),
                "Solicitação": req.get('numero_solicitacao_estoque'),
                "Solicitante": req.get('solicitante'),
                "Departamento": req.get('departamento'),
                "Etapa": req.get('etapa_atual'),
                "Valor": f"R$ {req.get('valor_final', req.get('valor_estimado', 0)) or 0:,.2f}",
                "Data Requisição": req.get('data_requisicao', '')
            })
        
        df_prioridade = pd.DataFrame(dados_prioridade)
        
        # Ordenar por prioridade
        ordem_prioridade = {"🔴 Urgente": 0, "🟡 Alta": 1, "🔵 Normal": 2, "🟢 Baixa": 3}
        df_prioridade['_ordem'] = df_prioridade['Prioridade'].map(ordem_prioridade)
        df_prioridade = df_prioridade.sort_values('_ordem').drop('_ordem', axis=1)
        
        st.dataframe(df_prioridade, use_container_width=True, height=400)
        
        # Botão para exportar
        if st.button("📊 Exportar Dashboard"):
            csv = df_prioridade.to_csv(index=False, encoding='utf-8-sig', sep=';', decimal=',')
            timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"dashboard_suprimentos_{timestamp}.csv",
                mime="text/csv"
            )
    else:
        st.info("📋 Nenhuma requisição ativa encontrada.")
