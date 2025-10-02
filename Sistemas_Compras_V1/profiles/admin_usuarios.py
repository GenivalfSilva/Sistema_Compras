"""
Módulo para gerenciamento de usuários do perfil Admin
Contém: Criar usuários, listar usuários, resetar senhas, gerenciar perfis
"""

import streamlit as st
import pandas as pd
import datetime
from typing import Dict

def gerenciar_usuarios(data: Dict, usuario: Dict, USE_DATABASE: bool = False):
    """Página de gerenciamento de usuários para administradores"""
    st.markdown("## 👥 Gerenciar Usuários")
    
    # Importa funções necessárias
    from app import save_data, add_user, reset_user_password
    from database_local import get_local_database as get_database
    
    # Tabs para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["👤 Criar Usuário", "📋 Lista de Usuários", "🔑 Resetar Senhas"])
    
    with tab1:
        st.markdown("### ➕ Criar Novo Usuário")
        
        with st.form("criar_usuario_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                novo_username = st.text_input("Nome de Usuário*", help="Login único do usuário")
                novo_nome = st.text_input("Nome Completo", help="Nome para exibição")
                nova_senha = st.text_input("Senha*", type="password", help="Senha inicial do usuário")
            
            with col2:
                novo_perfil = st.selectbox(
                    "Perfil*",
                    ["Solicitante", "Suprimentos", "Gerência&Diretoria", "Admin"],
                    help="Nível de acesso do usuário"
                )
                novo_departamento = st.selectbox(
                    "Departamento",
                    ["Manutenção", "TI", "RH", "Financeiro", "Marketing", "Operações", "Outro"],
                    help="Departamento do usuário"
                )
                st.write("")  # Espaçamento
            
            criar_usuario = st.form_submit_button("➕ Criar Usuário", type="primary")
        
        if criar_usuario:
            if novo_username and nova_senha and novo_perfil:
                erro = add_user(data, novo_username.strip(), novo_nome.strip(), 
                              novo_perfil, novo_departamento, nova_senha)
                if erro:
                    st.error(f"❌ {erro}")
                else:
                    save_data(data)
                    st.success(f"✅ Usuário '{novo_username}' criado com sucesso!")
                    st.rerun()
            else:
                st.error("❌ Preencha os campos obrigatórios (*).")
    
    with tab2:
        st.markdown("### 📋 Lista de Usuários")
        
        # Carrega usuários do banco ou JSON
        usuarios = []
        if USE_DATABASE:
            try:
                db = get_database()
                if db.db_available:
                    usuarios = db.get_all_users()
            except Exception as e:
                st.error(f"Erro ao carregar usuários do banco: {e}")
                usuarios = data.get("usuarios", [])
        else:
            usuarios = data.get("usuarios", [])
        
        if usuarios:
            # Cria DataFrame para exibição
            usuarios_df = pd.DataFrame([
                {
                    "Usuário": u.get("username", ""),
                    "Nome": u.get("nome", ""),
                    "Perfil": u.get("perfil", ""),
                    "Departamento": u.get("departamento", ""),
                    "Status": "Ativo"  # Pode ser expandido futuramente
                }
                for u in usuarios
            ])
            
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_perfil = st.selectbox(
                    "Filtrar por Perfil",
                    ["Todos"] + list(usuarios_df["Perfil"].unique()),
                    key="filtro_perfil"
                )
            with col2:
                filtro_dept = st.selectbox(
                    "Filtrar por Departamento",
                    ["Todos"] + list(usuarios_df["Departamento"].unique()),
                    key="filtro_dept"
                )
            with col3:
                busca = st.text_input("🔍 Buscar usuário", key="busca_usuario")
            
            # Aplica filtros
            df_filtrado = usuarios_df.copy()
            if filtro_perfil != "Todos":
                df_filtrado = df_filtrado[df_filtrado["Perfil"] == filtro_perfil]
            if filtro_dept != "Todos":
                df_filtrado = df_filtrado[df_filtrado["Departamento"] == filtro_dept]
            if busca:
                mask = (df_filtrado["Usuário"].str.contains(busca, case=False, na=False) |
                       df_filtrado["Nome"].str.contains(busca, case=False, na=False))
                df_filtrado = df_filtrado[mask]
            
            # Exibe tabela
            st.dataframe(df_filtrado, width='stretch')
            
            # Estatísticas
            st.markdown("#### 📊 Estatísticas")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total de Usuários", len(usuarios_df))
            with col2:
                admins = len(usuarios_df[usuarios_df["Perfil"] == "Admin"])
                st.metric("Administradores", admins)
            with col3:
                suprimentos = len(usuarios_df[usuarios_df["Perfil"] == "Suprimentos"])
                st.metric("Suprimentos", suprimentos)
            with col4:
                solicitantes = len(usuarios_df[usuarios_df["Perfil"] == "Solicitante"])
                st.metric("Solicitantes", solicitantes)
        else:
            st.info("📝 Nenhum usuário encontrado. Crie o primeiro usuário na aba 'Criar Usuário'.")
    
    with tab3:
        st.markdown("### 🔑 Resetar Senhas")
        st.warning("⚠️ Use esta funcionalidade com cuidado. O usuário será notificado da nova senha.")
        
        # Carrega lista de usuários para seleção
        usuarios_opcoes = []
        if USE_DATABASE:
            try:
                db = get_database()
                if db.db_available:
                    usuarios_lista = db.get_all_users()
                    usuarios_opcoes = [u.get("username", "") for u in usuarios_lista if u.get("username")]
            except:
                usuarios_lista = data.get("usuarios", [])
                usuarios_opcoes = [u.get("username", "") for u in usuarios_lista if u.get("username")]
        else:
            usuarios_lista = data.get("usuarios", [])
            usuarios_opcoes = [u.get("username", "") for u in usuarios_lista if u.get("username")]
        
        if usuarios_opcoes:
            with st.form("reset_senha_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    usuario_reset = st.selectbox(
                        "Selecionar Usuário",
                        usuarios_opcoes,
                        help="Escolha o usuário para resetar a senha"
                    )
                
                with col2:
                    nova_senha_reset = st.text_input(
                        "Nova Senha*",
                        type="password",
                        help="Nova senha para o usuário"
                    )
                
                confirmar_reset = st.form_submit_button("🔑 Resetar Senha", type="secondary")
            
            if confirmar_reset:
                if usuario_reset and nova_senha_reset:
                    if len(nova_senha_reset) < 4:
                        st.error("❌ A senha deve ter pelo menos 4 caracteres.")
                    else:
                        erro = reset_user_password(data, usuario_reset, nova_senha_reset)
                        if erro:
                            st.error(f"❌ {erro}")
                        else:
                            save_data(data)
                            st.success(f"✅ Senha do usuário '{usuario_reset}' resetada com sucesso!")
                            
                            # Adiciona notificação para o usuário (se sistema de notificações estiver ativo)
                            try:
                                from app import add_notification
                                add_notification(data, "Sistema", 0, 
                                               f"Sua senha foi resetada pelo administrador {usuario.get('nome', 'Admin')}")
                            except:
                                pass
                else:
                    st.error("❌ Selecione um usuário e digite a nova senha.")
        else:
            st.info("📝 Nenhum usuário disponível para reset de senha.")
    
    # Seção de backup e importação (funcionalidade futura)
    st.markdown("---")
    st.markdown("### 🔧 Ferramentas Avançadas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Exportar Lista de Usuários"):
            if usuarios:
                # Criar DataFrame e formatar datas para PT-BR
                df_usuarios = pd.DataFrame(usuarios)
                
                # Formatar coluna created_at se existir
                if 'created_at' in df_usuarios.columns:
                    df_usuarios['created_at'] = pd.to_datetime(df_usuarios['created_at'], errors='coerce').dt.strftime('%d/%m/%Y %H:%M:%S')
                
                # Normalizar caracteres especiais para evitar problemas de codificação
                import unicodedata
                for col in df_usuarios.select_dtypes(include=['object']).columns:
                    df_usuarios[col] = df_usuarios[col].astype(str).apply(
                        lambda x: unicodedata.normalize('NFC', x) if x != 'nan' else x
                    )
                
                # Exportar como Excel (.xlsx) para melhor compatibilidade com caracteres especiais
                try:
                    from io import BytesIO
                    buffer = BytesIO()
                    df_usuarios.to_excel(buffer, index=False, engine='openpyxl')
                    excel_data = buffer.getvalue()
                    
                    st.download_button(
                        label="⬇️ Download Excel",
                        data=excel_data,
                        file_name=f"usuarios_sistema_{datetime.datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx",
                        help="Arquivo Excel com caracteres especiais preservados",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except ImportError:
                    st.error("📦 Instale a dependência 'openpyxl' para exportar Excel: pip install openpyxl")
                except Exception as e:
                    st.error(f"❌ Erro ao gerar Excel: {str(e)}")
            else:
                st.warning("Nenhum usuário para exportar.")
    
    with col2:
        st.info("💡 **Dica:** Mantenha sempre pelo menos um usuário Admin ativo no sistema.")
