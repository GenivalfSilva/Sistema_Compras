import streamlit as st
import pandas as pd
from datetime import datetime, date
from database_local import get_local_database as get_database
from style import get_custom_css, get_section_header_html, get_form_container_start, get_form_container_end

def show_estoque_requisicoes():
    """Interface para o perfil Estoque - Criação de Requisições no Sistema Interno"""
    
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Header da seção
    st.markdown(get_section_header_html("📋 Gestão de Requisições - Sistema Interno"), unsafe_allow_html=True)
    
    # Tabs para organizar as funcionalidades
    tab1, tab2 = st.tabs(["🆕 Nova Requisição", "📊 Requisições Criadas"])
    
    with tab1:
        show_nova_requisicao()
    
    with tab2:
        show_requisicoes_criadas()

def show_nova_requisicao():
    """Interface para criar nova requisição no sistema interno"""
    
    st.markdown("### 🆕 Criar Nova Requisição")
    st.markdown("**Processo:** Solicitação → **Requisição** → Suprimentos → Cotação → Pedido de Compras")
    
    # Buscar solicitações pendentes de requisição
    db = get_database()
    if not db.db_available:
        st.error("❌ Banco de dados não disponível")
        return
    
    # Filtrar solicitações na etapa "Solicitação" (aguardando criação de requisição)
    solicitacoes = db.get_all_solicitacoes()
    solicitacoes_pendentes = [s for s in solicitacoes if s.get('etapa_atual') == 'Solicitação']
    
    if not solicitacoes_pendentes:
        st.info("✅ Não há solicitações pendentes de requisição no momento.")
        return
    
    st.markdown(f"**{len(solicitacoes_pendentes)} solicitação(ões) aguardando criação de requisição:**")
    
    # Seletor de solicitação
    opcoes_solicitacao = []
    for sol in solicitacoes_pendentes:
        prioridade_icon = {"Urgente": "🔴", "Alta": "🟡", "Normal": "🔵", "Baixa": "🟢"}.get(sol.get('prioridade', 'Normal'), "🔵")
        opcoes_solicitacao.append(f"{prioridade_icon} Sol. {sol.get('numero_solicitacao_estoque')} - {sol.get('solicitante')} - {sol.get('descricao', '')[:50]}...")
    
    solicitacao_selecionada = st.selectbox(
        "Selecione a solicitação para criar requisição:",
        options=range(len(opcoes_solicitacao)),
        format_func=lambda x: opcoes_solicitacao[x]
    )
    
    if solicitacao_selecionada is not None:
        sol_dados = solicitacoes_pendentes[solicitacao_selecionada]
        
        # Mostrar detalhes da solicitação
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📋 Dados da Solicitação:**")
            st.write(f"**Número:** {sol_dados.get('numero_solicitacao_estoque')}")
            st.write(f"**Solicitante:** {sol_dados.get('solicitante')}")
            st.write(f"**Departamento:** {sol_dados.get('departamento')}")
            st.write(f"**Prioridade:** {sol_dados.get('prioridade')}")
        
        with col2:
            st.write(f"**Data Solicitação:** {sol_dados.get('carimbo_data_hora', '')[:10]}")
            st.write(f"**Local Aplicação:** {sol_dados.get('local_aplicacao')}")
            st.write(f"**SLA:** {sol_dados.get('sla_dias')} dias")
        
        st.markdown("**Descrição:**")
        st.write(sol_dados.get('descricao', ''))
        
        # Mostrar itens se existirem
        if sol_dados.get('itens'):
            try:
                import json
                itens = json.loads(sol_dados.get('itens', '[]'))
                if itens:
                    st.markdown("**📦 Itens Solicitados:**")
                    df_itens = pd.DataFrame(itens)
                    st.dataframe(df_itens, width='stretch')
            except:
                pass
        
        st.markdown("---")
        
        # Formulário para criar requisição
        st.markdown("### 📝 Dados da Requisição no Sistema Interno")
        
        # Usar form para evitar redirecionamentos
        with st.form(f"form_requisicao_{sol_dados.get('numero_solicitacao_estoque')}", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                # Gerar próximo número de requisição
                proximo_req = db.get_next_numero_requisicao()
                numero_requisicao = st.number_input(
                    "Número da Requisição:",
                    value=proximo_req,
                    min_value=1,
                    help="Número da requisição no sistema interno da empresa",
                    key=f"num_req_{sol_dados.get('numero_solicitacao_estoque')}"
                )
                
                responsavel_estoque = st.text_input(
                    "Responsável Estoque:",
                    value=st.session_state.get('user_data', {}).get('nome', ''),
                    help="Nome do responsável que está criando a requisição",
                    key=f"resp_estoque_{sol_dados.get('numero_solicitacao_estoque')}"
                )
            
            with col2:
                data_requisicao = st.date_input(
                    "Data da Requisição:",
                    value=date.today(),
                    help="Data de criação da requisição no sistema interno",
                    key=f"data_req_{sol_dados.get('numero_solicitacao_estoque')}"
                )
            
            observacoes_requisicao = st.text_area(
                "Observações da Requisição:",
                placeholder="Observações sobre a criação da requisição no sistema interno...",
                help="Informações adicionais sobre o processo de requisição",
                key=f"obs_req_{sol_dados.get('numero_solicitacao_estoque')}"
            )
            
            # Botão para criar requisição dentro do form
            criar_requisicao = st.form_submit_button(
                "🔄 Criar Requisição e Enviar para Suprimentos", 
                type="primary"
            )
        
        # Processar criação da requisição
        if criar_requisicao:
            if numero_requisicao and responsavel_estoque:
                # Atualizar solicitação com dados da requisição
                updates = {
                    'numero_requisicao': numero_requisicao,
                    'data_requisicao': data_requisicao.strftime('%d/%m/%Y'),
                    'responsavel_estoque': responsavel_estoque,
                    'observacoes_requisicao': observacoes_requisicao,
                    'etapa_atual': 'Requisição',
                    'status': 'Requisição Criada'
                }
                
                # Atualizar histórico
                historico_atual = sol_dados.get('historico_etapas', '[]')
                try:
                    import json
                    historico = json.loads(historico_atual) if historico_atual else []
                except:
                    historico = []
                
                historico.append({
                    'etapa': 'Requisição',
                    'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'usuario': responsavel_estoque,
                    'observacao': f'Requisição {numero_requisicao} criada no sistema interno'
                })
                updates['historico_etapas'] = json.dumps(historico)
                
                # Salvar no banco
                if db.update_solicitacao(sol_dados.get('numero_solicitacao_estoque'), updates):
                    # Atualizar próximo número de requisição
                    db.set_config('proximo_numero_requisicao', str(numero_requisicao + 1))
                    
                    st.success(f"✅ Requisição {numero_requisicao} criada com sucesso!")
                    st.success(f"📤 Solicitação enviada para Suprimentos")
                    st.info("🔄 Atualize a página para ver as mudanças ou navegue para outra seção.")
                else:
                    st.error("❌ Erro ao criar requisição")
            else:
                st.error("❌ Preencha todos os campos obrigatórios")

def show_requisicoes_criadas():
    """Mostra histórico de requisições criadas"""
    
    st.markdown("### 📊 Requisições Criadas")
    
    db = get_database()
    if not db.db_available:
        st.error("❌ Banco de dados não disponível")
        return
    
    # Buscar todas as solicitações que já têm requisição
    solicitacoes = db.get_all_solicitacoes()
    requisicoes = [s for s in solicitacoes if s.get('numero_requisicao')]
    
    if not requisicoes:
        st.info("📋 Nenhuma requisição criada ainda.")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_departamento = st.selectbox(
            "Filtrar por Departamento:",
            options=["Todos"] + list(set([r.get('departamento', '') for r in requisicoes])),
            key="filtro_dept_req"
        )
    
    with col2:
        filtro_prioridade = st.selectbox(
            "Filtrar por Prioridade:",
            options=["Todas", "Urgente", "Alta", "Normal", "Baixa"],
            key="filtro_prior_req"
        )
    
    with col3:
        filtro_status = st.selectbox(
            "Filtrar por Status:",
            options=["Todos"] + list(set([r.get('status', '') for r in requisicoes])),
            key="filtro_status_req"
        )
    
    # Aplicar filtros
    requisicoes_filtradas = requisicoes
    if filtro_departamento != "Todos":
        requisicoes_filtradas = [r for r in requisicoes_filtradas if r.get('departamento') == filtro_departamento]
    if filtro_prioridade != "Todas":
        requisicoes_filtradas = [r for r in requisicoes_filtradas if r.get('prioridade') == filtro_prioridade]
    if filtro_status != "Todos":
        requisicoes_filtradas = [r for r in requisicoes_filtradas if r.get('status') == filtro_status]
    
    # Exibir estatísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Requisições", len(requisicoes_filtradas))
    with col2:
        em_suprimentos = len([r for r in requisicoes_filtradas if r.get('etapa_atual') in ['Requisição', 'Suprimentos']])
        st.metric("Em Suprimentos", em_suprimentos)
    with col3:
        em_cotacao = len([r for r in requisicoes_filtradas if r.get('etapa_atual') == 'Em Cotação'])
        st.metric("Em Cotação", em_cotacao)
    with col4:
        finalizadas = len([r for r in requisicoes_filtradas if r.get('etapa_atual') == 'Pedido Finalizado'])
        st.metric("Finalizadas", finalizadas)
    
    # Tabela de requisições
    if requisicoes_filtradas:
        dados_tabela = []
        for req in requisicoes_filtradas:
            prioridade_icon = {"Urgente": "🔴", "Alta": "🟡", "Normal": "🔵", "Baixa": "🟢"}.get(req.get('prioridade', 'Normal'), "🔵")
            
            dados_tabela.append({
                "Solicitação": req.get('numero_solicitacao_estoque'),
                "Requisição": req.get('numero_requisicao'),
                "Solicitante": req.get('solicitante'),
                "Departamento": req.get('departamento'),
                "Prioridade": f"{prioridade_icon} {req.get('prioridade')}",
                "Data Requisição": req.get('data_requisicao', ''),
                "Responsável Estoque": req.get('responsavel_estoque', ''),
                "Etapa Atual": req.get('etapa_atual'),
                "Status": req.get('status'),
                "Descrição": req.get('descricao', '')[:50] + "..." if len(req.get('descricao', '')) > 50 else req.get('descricao', '')
            })
        
        df = pd.DataFrame(dados_tabela)
        
        # Ordenar por número de requisição (mais recentes primeiro)
        df = df.sort_values('Requisição', ascending=False)
        
        st.dataframe(df, width='stretch', height=400)
        
        # Botão para exportar
        if st.button("📊 Exportar Requisições"):
            csv = df.to_csv(index=False, encoding='utf-8-sig', sep=';', decimal=',')
            timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"requisicoes_estoque_{timestamp}.csv",
                mime="text/csv"
            )
    else:
        st.info("📋 Nenhuma requisição encontrada com os filtros aplicados.")
