"""
Módulo para catálogo de produtos do perfil Suprimentos
Contém: Visualizar catálogo, adicionar produtos, editar produtos, gerenciar categorias
"""

import streamlit as st
import pandas as pd
import datetime
from typing import Dict

def catalogo_produtos(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Página de catálogo de produtos para perfil Suprimentos"""
    st.markdown("## 📦 Catálogo de Produtos")
    
    # Importa funções necessárias
    from app import save_data, get_database
    
    # Carrega catálogo de produtos
    if USE_DATABASE:
        try:
            db = get_database()
            if db.db_available:
                catalogo = db.get_catalogo_produtos()
            else:
                catalogo = data.get("configuracoes", {}).get("catalogo_produtos", [])
        except:
            catalogo = data.get("configuracoes", {}).get("catalogo_produtos", [])
    else:
        catalogo = data.get("configuracoes", {}).get("catalogo_produtos", [])
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["📋 Visualizar Catálogo", "➕ Adicionar Produto", "⚙️ Gerenciar Catálogo"])
    
    with tab1:
        st.markdown("### 📋 Catálogo de Produtos")
        
        if not catalogo:
            st.info("📝 Nenhum produto cadastrado no catálogo. Adicione produtos na aba 'Adicionar Produto'.")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        # Extrai categorias únicas
        categorias = list(set([p.get('categoria', 'Sem categoria') for p in catalogo]))
        categorias.sort()
        
        with col1:
            filtro_categoria = st.selectbox(
                "Filtrar por Categoria",
                ["Todas"] + categorias,
                key="filtro_categoria"
            )
        
        with col2:
            filtro_status = st.selectbox(
                "Status",
                ["Todos", "Ativo", "Inativo"],
                key="filtro_status"
            )
        
        with col3:
            busca_produto = st.text_input(
                "🔍 Buscar produto",
                placeholder="Nome ou código...",
                key="busca_produto"
            )
        
        # Aplica filtros
        catalogo_filtrado = catalogo.copy()
        
        if filtro_categoria != "Todas":
            catalogo_filtrado = [p for p in catalogo_filtrado if p.get('categoria') == filtro_categoria]
        
        if filtro_status != "Todos":
            ativo = filtro_status == "Ativo"
            catalogo_filtrado = [p for p in catalogo_filtrado if p.get('ativo', True) == ativo]
        
        if busca_produto:
            catalogo_filtrado = [
                p for p in catalogo_filtrado 
                if busca_produto.lower() in p.get('nome', '').lower() or 
                   busca_produto.lower() in p.get('codigo', '').lower()
            ]
        
        # Exibe produtos
        if catalogo_filtrado:
            # Cria DataFrame para exibição
            produtos_df = pd.DataFrame([
                {
                    "Código": p.get('codigo', ''),
                    "Nome": p.get('nome', ''),
                    "Categoria": p.get('categoria', ''),
                    "Unidade": p.get('unidade', ''),
                    "Status": "✅ Ativo" if p.get('ativo', True) else "❌ Inativo"
                }
                for p in catalogo_filtrado
            ])
            
            st.dataframe(produtos_df, use_container_width=True)
            
            # Estatísticas
            st.markdown("#### 📊 Estatísticas do Catálogo")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Produtos", len(catalogo))
            
            with col2:
                ativos = len([p for p in catalogo if p.get('ativo', True)])
                st.metric("Produtos Ativos", ativos)
            
            with col3:
                st.metric("Categorias", len(categorias))
            
            with col4:
                st.metric("Filtrados", len(catalogo_filtrado))
        else:
            st.warning("🔍 Nenhum produto encontrado com os filtros aplicados.")
    
    with tab2:
        st.markdown("### ➕ Adicionar Novo Produto")
        
        with st.form("adicionar_produto_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                novo_codigo = st.text_input(
                    "Código do Produto*",
                    placeholder="Ex: PRD-001",
                    help="Código único do produto"
                )
                
                novo_nome = st.text_input(
                    "Nome do Produto*",
                    placeholder="Ex: Cabo de Rede Cat6",
                    help="Nome descritivo do produto"
                )
            
            with col2:
                nova_categoria = st.selectbox(
                    "Categoria*",
                    ["TI", "Manutenção", "Escritório", "Limpeza", "Segurança", "Outro"],
                    help="Categoria do produto"
                )
                
                nova_unidade = st.selectbox(
                    "Unidade*",
                    ["UN", "PC", "CX", "KG", "L", "M", "M2", "M3"],
                    help="Unidade de medida"
                )
            
            nova_descricao = st.text_area(
                "Descrição Detalhada",
                height=100,
                placeholder="Descrição completa do produto, especificações técnicas...",
                help="Descrição opcional para mais detalhes"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                produto_ativo = st.checkbox("Produto Ativo", value=True)
            
            adicionar_produto = st.form_submit_button("➕ Adicionar Produto", type="primary")
        
        if adicionar_produto:
            if novo_codigo.strip() and novo_nome.strip() and nova_categoria and nova_unidade:
                # Verifica se código já existe
                codigo_existe = any(p.get('codigo', '').lower() == novo_codigo.strip().lower() for p in catalogo)
                
                if codigo_existe:
                    st.error(f"❌ Código '{novo_codigo}' já existe no catálogo.")
                else:
                    # Adiciona novo produto
                    novo_produto = {
                        "codigo": novo_codigo.strip(),
                        "nome": novo_nome.strip(),
                        "categoria": nova_categoria,
                        "unidade": nova_unidade,
                        "ativo": produto_ativo,
                        "descricao": nova_descricao.strip() if nova_descricao else "",
                        "data_cadastro": pd.Timestamp.now().isoformat(),
                        "usuario_cadastro": usuario.get('nome', usuario.get('username'))
                    }
                    
                    # Atualiza catálogo
                    if USE_DATABASE:
                        try:
                            db = get_database()
                            if db.db_available:
                                success = db.add_catalogo_produto(
                                    novo_produto['codigo'],
                                    novo_produto['nome'],
                                    novo_produto['categoria'],
                                    novo_produto['unidade'],
                                    novo_produto['ativo']
                                )
                                if success:
                                    st.success(f"✅ Produto '{novo_nome}' adicionado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao adicionar produto no banco de dados.")
                        except Exception as e:
                            st.error(f"Erro ao salvar no banco: {e}")
                    else:
                        # Adiciona ao JSON
                        data.setdefault("configuracoes", {}).setdefault("catalogo_produtos", []).append(novo_produto)
                        save_data(data)
                        st.success(f"✅ Produto '{novo_nome}' adicionado com sucesso!")
                        st.rerun()
            else:
                st.error("❌ Preencha todos os campos obrigatórios (*).")
    
    with tab3:
        st.markdown("### ⚙️ Gerenciar Catálogo")
        
        if not catalogo:
            st.info("📝 Nenhum produto para gerenciar.")
            return
        
        # Editor de produtos existentes
        st.markdown("#### ✏️ Editar Produtos")
        
        # Seleção de produto para editar
        produtos_opcoes = [f"{p.get('codigo', '')} - {p.get('nome', '')}" for p in catalogo]
        
        if produtos_opcoes:
            produto_selecionado = st.selectbox(
                "Selecionar Produto para Editar",
                produtos_opcoes,
                key="produto_editar"
            )
            
            if produto_selecionado:
                # Encontra o produto selecionado
                codigo_selecionado = produto_selecionado.split(" - ")[0]
                produto_atual = next((p for p in catalogo if p.get('codigo') == codigo_selecionado), None)
                
                if produto_atual:
                    with st.form("editar_produto_form"):
                        st.markdown(f"**Editando:** {produto_atual.get('nome', '')}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_nome = st.text_input(
                                "Nome do Produto",
                                value=produto_atual.get('nome', ''),
                                key="edit_nome"
                            )
                            
                            edit_categoria = st.selectbox(
                                "Categoria",
                                ["TI", "Manutenção", "Escritório", "Limpeza", "Segurança", "Outro"],
                                index=["TI", "Manutenção", "Escritório", "Limpeza", "Segurança", "Outro"].index(produto_atual.get('categoria', 'Outro')),
                                key="edit_categoria"
                            )
                        
                        with col2:
                            edit_unidade = st.selectbox(
                                "Unidade",
                                ["UN", "PC", "CX", "KG", "L", "M", "M2", "M3"],
                                index=["UN", "PC", "CX", "KG", "L", "M", "M2", "M3"].index(produto_atual.get('unidade', 'UN')),
                                key="edit_unidade"
                            )
                            
                            edit_ativo = st.checkbox(
                                "Produto Ativo",
                                value=produto_atual.get('ativo', True),
                                key="edit_ativo"
                            )
                        
                        edit_descricao = st.text_area(
                            "Descrição",
                            value=produto_atual.get('descricao', ''),
                            height=100,
                            key="edit_descricao"
                        )
                        
                        col_save, col_delete = st.columns(2)
                        
                        with col_save:
                            salvar_edicao = st.form_submit_button("💾 Salvar Alterações", type="primary")
                        
                        with col_delete:
                            excluir_produto = st.form_submit_button("🗑️ Excluir Produto", type="secondary")
                    
                    if salvar_edicao:
                        if edit_nome.strip():
                            # Atualiza produto
                            if USE_DATABASE:
                                try:
                                    db = get_database()
                                    if db.db_available:
                                        # Atualiza no banco
                                        catalogo_atualizado = []
                                        for p in catalogo:
                                            if p.get('codigo') == codigo_selecionado:
                                                p_updated = p.copy()
                                                p_updated.update({
                                                    'nome': edit_nome.strip(),
                                                    'categoria': edit_categoria,
                                                    'unidade': edit_unidade,
                                                    'ativo': edit_ativo,
                                                    'descricao': edit_descricao.strip()
                                                })
                                                catalogo_atualizado.append(p_updated)
                                            else:
                                                catalogo_atualizado.append(p)
                                        
                                        db.update_catalogo_produtos(catalogo_atualizado)
                                        st.success(f"✅ Produto '{edit_nome}' atualizado com sucesso!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao atualizar no banco: {e}")
                            else:
                                # Atualiza no JSON
                                for i, p in enumerate(data["configuracoes"]["catalogo_produtos"]):
                                    if p.get('codigo') == codigo_selecionado:
                                        data["configuracoes"]["catalogo_produtos"][i].update({
                                            'nome': edit_nome.strip(),
                                            'categoria': edit_categoria,
                                            'unidade': edit_unidade,
                                            'ativo': edit_ativo,
                                            'descricao': edit_descricao.strip()
                                        })
                                        break
                                
                                save_data(data)
                                st.success(f"✅ Produto '{edit_nome}' atualizado com sucesso!")
                                st.rerun()
                        else:
                            st.error("❌ Nome do produto não pode estar vazio.")
                    
                    if excluir_produto:
                        st.warning("⚠️ Tem certeza que deseja excluir este produto?")
                        if st.button("🗑️ Confirmar Exclusão", key="confirmar_exclusao"):
                            # Remove produto
                            if USE_DATABASE:
                                try:
                                    db = get_database()
                                    if db.db_available:
                                        catalogo_filtrado = [p for p in catalogo if p.get('codigo') != codigo_selecionado]
                                        db.update_catalogo_produtos(catalogo_filtrado)
                                        st.success(f"✅ Produto excluído com sucesso!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir do banco: {e}")
                            else:
                                # Remove do JSON
                                data["configuracoes"]["catalogo_produtos"] = [
                                    p for p in data["configuracoes"]["catalogo_produtos"] 
                                    if p.get('codigo') != codigo_selecionado
                                ]
                                save_data(data)
                                st.success(f"✅ Produto excluído com sucesso!")
                                st.rerun()
        
        # Ferramentas de importação/exportação
        st.markdown("---")
        st.markdown("#### 🔧 Ferramentas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Exportar Catálogo"):
                if catalogo:
                    df_export = pd.DataFrame(catalogo)
                    
                    # Formatar datas se existirem
                    date_columns = ['data_criacao', 'data_atualizacao', 'created_at', 'updated_at']
                    for col in date_columns:
                        if col in df_export.columns:
                            df_export[col] = pd.to_datetime(df_export[col], errors='coerce').dt.strftime('%d/%m/%Y %H:%M:%S')
                    
                    # Formatar valores monetários para PT-BR
                    money_columns = ['preco', 'valor', 'preco_unitario', 'custo']
                    for col in money_columns:
                        if col in df_export.columns:
                            df_export[col] = df_export[col].apply(lambda x: f"R$ {x:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.') if pd.notnull(x) and x != '' else 'N/A')
                    
                    csv_data = df_export.to_csv(index=False, encoding='utf-8-sig', sep=';', decimal=',')
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name=f"catalogo_produtos_{datetime.datetime.now().strftime('%d%m%Y_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("Nenhum produto para exportar.")
        
        with col2:
            st.info("💡 **Dica:** Use códigos padronizados para facilitar a busca e organização.")
