"""
Implementação da funcionalidade Nova Solicitação para o perfil Solicitante
Atualizado: 2025-08-20 - Ordem corrigida e SLA dinâmico
"""

import streamlit as st
import pandas as pd
import datetime
import os
from typing import Dict, List

def nova_solicitacao(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Renderiza a página de Nova Solicitação"""
    from style import (get_section_header_html, get_info_box_html, get_form_container_start, 
                      get_form_container_end, get_form_section_start, get_form_section_end, 
                      get_form_section_title)
    
    # Importações condicionais
    if USE_DATABASE:
        try:
            from database_local import get_local_database as get_database
        except ImportError:
            USE_DATABASE = False
    
    # Constantes
    DEPARTAMENTOS = ["Manutenção", "TI", "RH", "Financeiro", "Marketing", "Operações", "Outro"]
    PRIORIDADES = [
        ("Normal", "3 dias úteis"),
        ("Urgente", "1 dia útil"), 
        ("Baixa", "5 dias úteis"),
        ("Alta", "2 dias úteis")
    ]
    ALLOWED_FILE_TYPES = ["pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"]
    
    # Funções auxiliares
    def obter_sla_por_prioridade(prioridade: str, departamento: str = None) -> int:
        SLA_PADRAO = {"Urgente": 1, "Alta": 2, "Normal": 3, "Baixa": 5}
        return SLA_PADRAO.get(prioridade, 3)
    
    def ensure_upload_dir(data: Dict):
        upload_dir = data.get("configuracoes", {}).get("upload_dir", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        return upload_dir
    
    def save_uploaded_files(files: List, base_dir: str) -> List[Dict]:
        saved = []
        if not files:
            return saved
        os.makedirs(base_dir, exist_ok=True)
        for f in files:
            try:
                filename = f.name
                ext = filename.split('.')[-1].lower()
                dest_path = os.path.join(base_dir, filename)
                with open(dest_path, 'wb') as out:
                    out.write(f.getbuffer())
                saved.append({
                    "nome_arquivo": filename,
                    "caminho": dest_path.replace('\\', '/'),
                    "tipo": ext,
                    "data_upload": datetime.datetime.now().isoformat()
                })
            except Exception:
                pass
        return saved
    
    def render_data_editor(df: pd.DataFrame, key: str = None, **kwargs) -> pd.DataFrame:
        try:
            return st.data_editor(df, key=key, **kwargs)
        except Exception:
            try:
                return st.experimental_data_editor(df, key=key, **kwargs)
            except Exception:
                st.dataframe(df, use_container_width=True)
                return df
    
    def save_data(data: Dict):
        if USE_DATABASE:
            try:
                db = get_database()
                if db.db_available:
                    config = data.get("configuracoes", {})
                    for key, value in config.items():
                        if key != "catalogo_produtos":
                            db.set_config(key, str(value))
                    catalogo = config.get("catalogo_produtos", [])
                    if catalogo:
                        db.update_catalogo_produtos(catalogo)
                    return
            except Exception:
                pass
        
        import json
        with open("compras_sla_data.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    # Interface principal
    st.markdown(get_section_header_html('📝 Nova Solicitação de Compra'), unsafe_allow_html=True)
    st.markdown(get_info_box_html('💡 <strong>Baseado na estrutura da planilha Excel - Aba \'Solicitação\'</strong>'), unsafe_allow_html=True)
    
    
    st.markdown(get_form_container_start(), unsafe_allow_html=True)
    
    # Seção 1: Dados do Solicitante (sem formulário para evitar botão)
    st.markdown(get_form_section_start(), unsafe_allow_html=True)
    st.markdown(get_form_section_title('👤 Dados do Solicitante'), unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        solicitante = st.text_input("Solicitante (Nome e Sobrenome)*", 
                                  help="Campo obrigatório conforme planilha",
                                  placeholder="Digite o nome completo do solicitante",
                                  key="solicitante_input")
        departamento = st.selectbox("Departamento*", DEPARTAMENTOS, help="Departamento do solicitante", key="departamento_input")
    
    with col2:
        # Cria opções formatadas para o selectbox
        opcoes_prioridade = [f"{nome} ({sla})" for nome, sla in PRIORIDADES]
        prioridade_selecionada = st.selectbox("Prioridade*", opcoes_prioridade, help="Define o SLA automaticamente", key="prioridade_input")
        
        # Extrai apenas o nome da prioridade
        prioridade = prioridade_selecionada.split(" (")[0]
        sla_dias = obter_sla_por_prioridade(prioridade)
    
    st.markdown(get_form_section_end(), unsafe_allow_html=True)
    
    # Seção 2: Itens da Solicitação (fora do form para permitir interatividade)
    st.markdown(get_form_section_start(), unsafe_allow_html=True)
    st.markdown(get_form_section_title('🧾 Itens da Solicitação'), unsafe_allow_html=True)
    
    # Obtém catálogo de produtos
    catalogo = []
    if USE_DATABASE:
        try:
            db = get_database()
            if db.db_available:
                catalogo = db.get_catalogo_produtos()
        except Exception:
            pass
    
    if not catalogo:
        catalogo = data.get("configuracoes", {}).get("catalogo_produtos", [])
    
    if not catalogo:
        st.warning("⚠️ Catálogo de produtos vazio. Configure em '📦 Catálogo de Produtos' antes de criar solicitações.")
    else:
        # Inicializa lista de itens na sessão se não existir
        if 'itens_solicitacao' not in st.session_state:
            st.session_state.itens_solicitacao = []
        
        # Gerenciamento de produtos
        with st.expander("🔧 **Gerenciar Catálogo de Produtos**", expanded=False):
            tab_add, tab_edit, tab_delete = st.tabs(["➕ Adicionar", "✏️ Editar", "🗑️ Excluir"])
            
            with tab_add:
                st.markdown("**Cadastrar Novo Produto**")
                with st.form("novo_produto_form"):
                    col_np1, col_np2 = st.columns(2)
                    with col_np1:
                        novo_codigo = st.text_input("Código*", placeholder="Ex: PROD001")
                        novo_nome = st.text_input("Nome do Produto*", placeholder="Ex: Cabo HDMI 2m")
                        nova_categoria = st.selectbox("Categoria", ["Eletrônicos", "Escritório", "Limpeza", "Manutenção", "TI", "Construção", "Outro"])
                    with col_np2:
                        nova_unidade = st.selectbox("Unidade", ["UN", "PC", "KG", "M", "L", "CX", "PAR"])
                        novo_preco = st.number_input("Preço Estimado (R$)", min_value=0.0, step=0.01, format="%.2f")
                        novo_ativo = st.checkbox("Produto Ativo", value=True)
                    
                    if st.form_submit_button("💾 Salvar Produto"):
                        if novo_codigo and novo_nome:
                            # Verifica se código já existe
                            codigo_existe = any(p.get('codigo') == novo_codigo for p in catalogo)
                            if codigo_existe:
                                st.error(f"❌ Código '{novo_codigo}' já existe!")
                            else:
                                novo_produto = {
                                    "codigo": novo_codigo,
                                    "nome": novo_nome,
                                    "categoria": nova_categoria,
                                    "unidade": nova_unidade,
                                    "preco_estimado": novo_preco,
                                    "ativo": novo_ativo,
                                    "id": len(catalogo) + 1
                                }
                                
                                # Salva no banco ou JSON
                                if USE_DATABASE:
                                    try:
                                        db = get_database()
                                        if db.db_available:
                                            catalogo.append(novo_produto)
                                            db.update_catalogo_produtos(catalogo)
                                            st.success(f"✅ Produto '{novo_nome}' adicionado com sucesso!")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erro ao salvar no banco: {e}")
                                else:
                                    catalogo.append(novo_produto)
                                    data["configuracoes"]["catalogo_produtos"] = catalogo
                                    save_data(data)
                                    st.success(f"✅ Produto '{novo_nome}' adicionado com sucesso!")
                                    st.rerun()
                        else:
                            st.error("❌ Preencha código e nome do produto!")
            
            with tab_edit:
                st.markdown("**Editar Produto Existente**")
                if catalogo:
                    produto_para_editar = st.selectbox(
                        "Selecione o produto para editar:",
                        options=[f"{p.get('codigo', '')} - {p.get('nome', '')}" for p in catalogo],
                        key="produto_editar"
                    )
                    
                    if produto_para_editar:
                        produto_selecionado_edit = next(p for p in catalogo if f"{p.get('codigo', '')} - {p.get('nome', '')}" == produto_para_editar)
                        
                        with st.form("editar_produto_form"):
                            col_ep1, col_ep2 = st.columns(2)
                            with col_ep1:
                                edit_codigo = st.text_input("Código*", value=produto_selecionado_edit.get('codigo', ''))
                                edit_nome = st.text_input("Nome do Produto*", value=produto_selecionado_edit.get('nome', ''))
                                categorias_disponiveis = ["Eletrônicos", "Escritório", "Limpeza", "Manutenção", "TI", "Construção", "Outro"]
                                categoria_atual = produto_selecionado_edit.get('categoria', 'Outro')
                                if categoria_atual not in categorias_disponiveis:
                                    categoria_atual = 'Outro'
                                edit_categoria = st.selectbox("Categoria", 
                                    categorias_disponiveis,
                                    index=categorias_disponiveis.index(categoria_atual))
                            with col_ep2:
                                edit_unidade = st.selectbox("Unidade", 
                                    ["UN", "PC", "KG", "M", "L", "CX", "PAR"],
                                    index=["UN", "PC", "KG", "M", "L", "CX", "PAR"].index(produto_selecionado_edit.get('unidade', 'UN')))
                                edit_preco = st.number_input("Preço Estimado (R$)", 
                                    value=float(produto_selecionado_edit.get('preco_estimado', 0)), 
                                    min_value=0.0, step=0.01, format="%.2f")
                                edit_ativo = st.checkbox("Produto Ativo", value=produto_selecionado_edit.get('ativo', True))
                            
                            if st.form_submit_button("💾 Salvar Alterações"):
                                if edit_codigo and edit_nome:
                                    # Atualiza o produto
                                    for i, p in enumerate(catalogo):
                                        if p.get('id') == produto_selecionado_edit.get('id'):
                                            catalogo[i] = {
                                                "codigo": edit_codigo,
                                                "nome": edit_nome,
                                                "categoria": edit_categoria,
                                                "unidade": edit_unidade,
                                                "preco_estimado": edit_preco,
                                                "ativo": edit_ativo,
                                                "id": produto_selecionado_edit.get('id')
                                            }
                                            break
                                    
                                    # Salva no banco ou JSON
                                    if USE_DATABASE:
                                        try:
                                            db = get_database()
                                            if db.db_available:
                                                db.update_catalogo_produtos(catalogo)
                                                st.success(f"✅ Produto '{edit_nome}' atualizado com sucesso!")
                                                st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erro ao salvar no banco: {e}")
                                    else:
                                        data["configuracoes"]["catalogo_produtos"] = catalogo
                                        save_data(data)
                                        st.success(f"✅ Produto '{edit_nome}' atualizado com sucesso!")
                                        st.rerun()
                                else:
                                    st.error("❌ Preencha código e nome do produto!")
                else:
                    st.info("📦 Nenhum produto cadastrado para editar.")
            
            with tab_delete:
                st.markdown("**Excluir Produto**")
                if catalogo:
                    produto_para_excluir = st.selectbox(
                        "Selecione o produto para excluir:",
                        options=[f"{p.get('codigo', '')} - {p.get('nome', '')}" for p in catalogo],
                        key="produto_excluir"
                    )
                    
                    if produto_para_excluir:
                        produto_selecionado_del = next(p for p in catalogo if f"{p.get('codigo', '')} - {p.get('nome', '')}" == produto_para_excluir)
                        
                        st.warning(f"⚠️ **Atenção:** Você está prestes a excluir o produto:")
                        st.info(f"**Código:** {produto_selecionado_del.get('codigo', '')}\n**Nome:** {produto_selecionado_del.get('nome', '')}")
                        
                        col_del1, col_del2 = st.columns(2)
                        with col_del1:
                            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                                # Remove o produto
                                catalogo = [p for p in catalogo if p.get('id') != produto_selecionado_del.get('id')]
                                
                                # Salva no banco ou JSON
                                if USE_DATABASE:
                                    try:
                                        db = get_database()
                                        if db.db_available:
                                            db.update_catalogo_produtos(catalogo)
                                            st.success(f"✅ Produto '{produto_selecionado_del.get('nome', '')}' excluído com sucesso!")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erro ao salvar no banco: {e}")
                                else:
                                    data["configuracoes"]["catalogo_produtos"] = catalogo
                                    save_data(data)
                                    st.success(f"✅ Produto '{produto_selecionado_del.get('nome', '')}' excluído com sucesso!")
                                    st.rerun()
                        with col_del2:
                            if st.button("❌ Cancelar"):
                                st.rerun()
                else:
                    st.info("📦 Nenhum produto cadastrado para excluir.")
        
        # Interface para adicionar novo item
        st.markdown("**➕ Adicionar Item à Solicitação**")
        col_add1, col_add2, col_add3, col_add4 = st.columns([3, 2, 1, 1])
        
        with col_add1:
            # Cria opções com código e descrição
            opcoes_produtos = []
            produtos_map = {}
            for produto in catalogo:
                if produto.get('ativo', True):
                    codigo = produto.get('codigo', '')
                    nome = produto.get('nome', '')
                    opcao = f"{codigo} - {nome}"
                    opcoes_produtos.append(opcao)
                    produtos_map[opcao] = produto
            
            produto_selecionado = st.selectbox(
                "Produto", 
                options=[""] + opcoes_produtos,
                key="novo_produto",
                help="Selecione um produto do catálogo"
            )
        
        with col_add2:
            quantidade = st.number_input(
                "Quantidade", 
                min_value=1, 
                value=1, 
                step=1,
                key="nova_quantidade",
                help="Quantidade desejada"
            )
        
        with col_add3:
            if produto_selecionado:
                produto_info = produtos_map.get(produto_selecionado, {})
                unidade = produto_info.get('unidade', 'UN')
                st.text_input("Unidade", value=unidade, disabled=True, key="nova_unidade")
            else:
                st.text_input("Unidade", value="", disabled=True, key="nova_unidade_empty")
        
        with col_add4:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("➕ Adicionar", key="btn_adicionar_item", help="Adicionar item à lista"):
                if produto_selecionado and quantidade > 0:
                    produto_info = produtos_map[produto_selecionado]
                    novo_item = {
                        "codigo": produto_info.get('codigo', ''),
                        "nome": produto_info.get('nome', ''),
                        "quantidade": quantidade,
                        "unidade": produto_info.get('unidade', 'UN'),
                        "categoria": produto_info.get('categoria', '')
                    }
                    st.session_state.itens_solicitacao.append(novo_item)
                    # Limpa os campos usando del para evitar erro de modificação
                    if 'novo_produto' in st.session_state:
                        del st.session_state.novo_produto
                    if 'nova_quantidade' in st.session_state:
                        del st.session_state.nova_quantidade
                    st.rerun()
                else:
                    st.error("Selecione um produto e quantidade válida")
        
        # Exibe lista de itens adicionados
        if st.session_state.itens_solicitacao:
            st.markdown("**📋 Itens Adicionados**")
            
            # Cria DataFrame para exibição
            itens_display = []
            for i, item in enumerate(st.session_state.itens_solicitacao):
                itens_display.append({
                    "#": i + 1,
                    "Código": item['codigo'],
                    "Produto": item['nome'],
                    "Qtd": item['quantidade'],
                    "Unidade": item['unidade'],
                    "Categoria": item.get('categoria', '')
                })
            
            df_itens = pd.DataFrame(itens_display)
            
            # Exibe tabela com opção de edição
            try:
                if hasattr(st, "column_config"):
                    col_config = {
                        "#": st.column_config.NumberColumn("#", width="small"),
                        "Código": st.column_config.TextColumn("Código", width="small"),
                        "Produto": st.column_config.TextColumn("Produto", width="large"),
                        "Qtd": st.column_config.NumberColumn("Qtd", min_value=1, step=1, width="small"),
                        "Unidade": st.column_config.TextColumn("Unidade", width="small"),
                        "Categoria": st.column_config.TextColumn("Categoria", width="medium")
                    }
                    
                    itens_editados_df = st.data_editor(
                        df_itens,
                        column_config=col_config,
                        use_container_width=True,
                        hide_index=True,
                        key="editor_itens_lista"
                    )
                    
                    # Atualiza a lista na sessão com as edições
                    for i, row in itens_editados_df.iterrows():
                        if i < len(st.session_state.itens_solicitacao):
                            st.session_state.itens_solicitacao[i]['quantidade'] = row['Qtd']
                else:
                    st.dataframe(df_itens, use_container_width=True)
            except Exception:
                st.dataframe(df_itens, use_container_width=True)
            
            # Botões de ação
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            with col_btn1:
                if st.button("🗑️ Limpar Lista", key="btn_limpar_itens", help="Remove todos os itens"):
                    st.session_state.itens_solicitacao = []
                    st.rerun()
            
            with col_btn2:
                if st.button("❌ Remover Último", key="btn_remover_ultimo", help="Remove o último item adicionado"):
                    if st.session_state.itens_solicitacao:
                        st.session_state.itens_solicitacao.pop()
                        st.rerun()
            
            with col_btn3:
                st.info(f"📊 **Total de itens:** {len(st.session_state.itens_solicitacao)}")
        else:
            st.info("➕ Use o formulário acima para adicionar itens à solicitação")
    
    st.markdown(get_form_section_end(), unsafe_allow_html=True)
    
    # Formulário principal para o restante das seções
    with st.form("nova_solicitacao_final"):
        # Seção 3: Resumo dos Itens Selecionados
        st.markdown(get_form_section_start(), unsafe_allow_html=True)
        st.markdown(get_form_section_title('🧾 Resumo dos Itens Selecionados'), unsafe_allow_html=True)
        
        itens_struct = st.session_state.get('itens_solicitacao', [])
        if itens_struct:
            resumo_itens = []
            for i, item in enumerate(itens_struct):
                resumo_itens.append({
                    "#": i + 1,
                    "Código": item['codigo'],
                    "Produto": item['nome'],
                    "Qtd": item['quantidade'],
                    "Unidade": item['unidade']
                })
            
            df_resumo = pd.DataFrame(resumo_itens)
            st.dataframe(df_resumo, use_container_width=True, hide_index=True)
            st.success(f"✅ {len(itens_struct)} item(ns) selecionado(s) para a solicitação")
        else:
            st.warning("⚠️ Nenhum item foi adicionado à solicitação. Use a seção acima para adicionar itens.")
        
        st.markdown(get_form_section_end(), unsafe_allow_html=True)
        
        # Seção 3: Dados da Solicitação
        st.markdown(get_form_section_start(), unsafe_allow_html=True)
        st.markdown(get_form_section_title('📋 Dados da Solicitação'), unsafe_allow_html=True)
        
        descricao = st.text_area("Descrição*", height=120,
                                help="Descrição detalhada da solicitação",
                                placeholder="Descreva detalhadamente o que está sendo solicitado...")
        
        local_aplicacao = st.text_input("Local de Aplicação*",
                                       help="Onde o material será aplicado",
                                       placeholder="Ex: Sala de Servidores, Linha de Produção 1...")
        
        st.markdown(get_form_section_end(), unsafe_allow_html=True)
        
        # Seção 4: Anexos
        st.markdown(get_form_section_start(), unsafe_allow_html=True)
        st.markdown(get_form_section_title('📎 Anexos da Solicitação'), unsafe_allow_html=True)
        
        anexos_files = st.file_uploader("Faça upload dos arquivos relacionados à solicitação (opcional)",
                                       type=ALLOWED_FILE_TYPES, accept_multiple_files=True,
                                       help="Tipos permitidos: PDF, PNG, JPG, JPEG, DOC, DOCX, XLS, XLSX")
        
        if anexos_files:
            st.success(f"✅ {len(anexos_files)} arquivo(s) selecionado(s)")
        
        st.markdown(get_form_section_end(), unsafe_allow_html=True)
        
        # Seção 5: Informações Automáticas
        st.markdown(get_form_section_start(), unsafe_allow_html=True)
        st.markdown(get_form_section_title('⚙️ Informações de Controle'), unsafe_allow_html=True)
        st.markdown('<p style="color: #64748b; font-style: italic; margin-bottom: 1rem;">Os campos abaixo são preenchidos automaticamente pelo sistema</p>', unsafe_allow_html=True)
        
        col5, col6 = st.columns(2)
        with col5:
            st.text_input("Nº Solicitação (Estoque)", value="Será gerado automaticamente", disabled=True)
            st.text_input("Status Inicial", value="Solicitação", disabled=True)
        with col6:
            st.text_input("Data/Hora de Criação", 
                         value=datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S'), disabled=True)
            # Campo removido conforme solicitado pelo usuário
            st.text_input("Prioridade Selecionada", value="Será definida automaticamente", disabled=True)
        
        st.markdown(get_form_section_end(), unsafe_allow_html=True)
        
        # Botão de submissão
        st.markdown('<br>', unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Criar Solicitação", use_container_width=True)
    
    st.markdown(get_form_container_end(), unsafe_allow_html=True)
    
    # Processamento do formulário
    if submitted:
        # Previne dupla submissão
        if 'form_submitted' not in st.session_state:
            st.session_state.form_submitted = False
        
        if st.session_state.form_submitted:
            st.warning("⚠️ Solicitação já foi enviada. Aguarde o processamento.")
            return
        
        # Obtém os itens da sessão
        itens_struct = st.session_state.get('itens_solicitacao', [])

        if solicitante and departamento and descricao and local_aplicacao and len(itens_struct) > 0:
            # VALIDAÇÕES DE SEGURANÇA
            # 1. Validar prioridade
            prioridades_validas = ["Urgente", "Alta", "Normal", "Baixa"]
            if prioridade not in prioridades_validas:
                st.error(f"❌ Prioridade inválida: '{prioridade}'. Use: {', '.join(prioridades_validas)}")
                return
            
            # 2. Validar valores negativos nos itens
            for item in itens_struct:
                if item.get('quantidade', 0) <= 0:
                    st.error(f"❌ Quantidade inválida para '{item.get('nome', 'item')}': {item.get('quantidade')}. Deve ser maior que zero.")
                    return
            
            # 3. Validar campos obrigatórios não vazios
            if not solicitante.strip():
                st.error("❌ Nome do solicitante não pode estar vazio.")
                return
            if not descricao.strip():
                st.error("❌ Descrição não pode estar vazia.")
                return
            if not local_aplicacao.strip():
                st.error("❌ Local de aplicação não pode estar vazio.")
                return
            
            # Gera números automáticos (garantindo unicidade no banco)
            if USE_DATABASE:
                try:
                    db_tmp = get_database()
                    if db_tmp.db_available:
                        numero_solicitacao = db_tmp.get_next_numero_solicitacao()
                    else:
                        numero_solicitacao = data["configuracoes"]["proximo_numero_solicitacao"]
                        data["configuracoes"]["proximo_numero_solicitacao"] += 1
                except Exception:
                    numero_solicitacao = data["configuracoes"]["proximo_numero_solicitacao"]
                    data["configuracoes"]["proximo_numero_solicitacao"] += 1
            else:
                numero_solicitacao = data["configuracoes"]["proximo_numero_solicitacao"]
                data["configuracoes"]["proximo_numero_solicitacao"] += 1
            
            # Salva anexos da solicitação
            upload_root = ensure_upload_dir(data)
            sol_dir = os.path.join(upload_root, f"solicitacao_{numero_solicitacao}", "requisicao")
            anexos_meta = save_uploaded_files(anexos_files, sol_dir)
            
            nova_solicitacao = {
                "carimbo_data_hora": datetime.datetime.now().isoformat(),
                "solicitante": solicitante,
                "departamento": departamento,
                "prioridade": prioridade,
                "descricao": descricao,
                "local_aplicacao": local_aplicacao,
                "status": "Solicitação",
                "numero_solicitacao_estoque": numero_solicitacao,
                "numero_pedido_compras": None,
                "data_numero_pedido": None,
                "data_cotacao": None,
                "data_entrega": None,
                "sla_dias": sla_dias,
                "dias_atendimento": None,
                "sla_cumprido": None,
                "observacoes": None,
                "numero_requisicao_interno": None,
                "data_requisicao_interna": None,
                "responsavel_suprimentos": None,
                "itens": itens_struct,
                "anexos_requisicao": anexos_meta,
                "cotacoes": [],
                "aprovacoes": [],
                "valor_estimado": None,
                "valor_final": None,
                "fornecedor_recomendado": None,
                "fornecedor_final": None,
                "id": len(data["solicitacoes"]) + 1,
                "etapa_atual": "Solicitação",
                "historico_etapas": [{
                    "etapa": "Solicitação",
                    "data_entrada": datetime.datetime.now().isoformat(),
                    "usuario": "Sistema"
                }]
            }
            
            # Salva no banco ou JSON
            if USE_DATABASE:
                db = get_database()
                if db.db_available:
                    success = db.add_solicitacao(nova_solicitacao)
                    if success:
                        # Atualiza próximo número (apenas para consistência visual)
                        db.set_config('proximo_numero_solicitacao', str(max(numero_solicitacao + 1, data["configuracoes"].get("proximo_numero_solicitacao", numero_solicitacao + 1))))
                        st.success(f"✅ Solicitação #{numero_solicitacao} salva no banco de dados com sucesso!")
                    else:
                        # Mostra detalhe do erro retornado pelo DB
                        detalhe = getattr(db, 'last_error', '')
                        if detalhe:
                            st.error(f"❌ Erro ao salvar solicitação no banco de dados: {detalhe}")
                        else:
                            st.error("❌ Erro ao salvar solicitação no banco de dados.")
                        return
                else:
                    data["solicitacoes"].append(nova_solicitacao)
                    save_data(data)
            else:
                data["solicitacoes"].append(nova_solicitacao)
                save_data(data)
            
            # Marca como submetido para prevenir duplicatas
            st.session_state.form_submitted = True
            
            # Mensagem de sucesso
            success_content = f'<h3 style="color: #065f46; margin: 0 0 1rem 0;">🎉 Solicitação #{numero_solicitacao} Criada com Sucesso!</h3>'
            st.markdown(get_info_box_html(success_content, "success"), unsafe_allow_html=True)
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.markdown(f"**📅 Data/Hora:** {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
                st.markdown(f"**⏱️ SLA:** {sla_dias} dias úteis")
            with col_info2:
                st.markdown(f"**📊 Status:** Solicitação (Etapa 1 de 7)")
                st.markdown(f"**📎 Anexos:** {len(anexos_meta)} arquivo(s)")
            st.markdown(f"**🧾 Itens:** {len(itens_struct)} item(ns)")
            
            # Próximos passos
            proximos_passos = '<h4 style="color: #1e40af; margin: 0 0 1rem 0;">🔄 Próximos Passos</h4><strong>1.</strong> A solicitação será analisada pela área de <strong>Suprimentos</strong><br><strong>2.</strong> Use a opção <strong>\'🔄 Mover para Próxima Etapa\'</strong> para avançar o processo<br><strong>3.</strong> Acompanhe o progresso no <strong>Dashboard SLA</strong> ou <strong>Histórico por Etapa</strong>'
            st.markdown(get_info_box_html(proximos_passos), unsafe_allow_html=True)
            
            # Botão para criar nova solicitação (limpa o formulário)
            if st.button("🆕 Criar Nova Solicitação", type="primary", use_container_width=True):
                # Limpa o estado do formulário
                for key in list(st.session_state.keys()):
                    if key.startswith('nova_solicitacao') or key in ['form_submitted', 'itens_editor', 'itens_solicitacao', 'novo_produto', 'nova_quantidade']:
                        del st.session_state[key]
                st.rerun()
            
        else:
            warning_content = '<h4 style="color: #92400e; margin: 0 0 0.5rem 0;">⚠️ Campos Obrigatórios</h4>Por favor, preencha todos os campos marcados com **asterisco (*)** e adicione ao menos 1 item válido antes de continuar.'
            st.markdown(get_info_box_html(warning_content, "warning"), unsafe_allow_html=True)
