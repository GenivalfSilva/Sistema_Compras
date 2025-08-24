import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta, date
import json
import os
from typing import Dict, List
import math
import hashlib

import io
from style import get_custom_css, get_sidebar_css, get_stats_card_html, get_section_header_html, get_info_box_html, get_form_container_start, get_form_container_end, get_form_section_start, get_form_section_end, get_form_section_title

# Usar PostgreSQL local exclusivamente
from database_local import get_local_database

# Sistema de sessão simplificado para PostgreSQL local
import uuid
import time

def init_session():
    """Inicializa sistema de sessão"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}

def authenticate_user(username: str, password: str) -> bool:
    """Autentica usuário no PostgreSQL local"""
    db = get_local_database()
    user_data = db.authenticate_user(username, password)
    
    if user_data:
        st.session_state.authenticated = True
        st.session_state.user_data = user_data
        st.session_state.username = username
        
        # Criar sessão no banco
        db.create_session(username, st.session_state.session_id)
        return True
    return False

def logout():
    """Faz logout do usuário"""
    st.session_state.authenticated = False
    st.session_state.user_data = {}
    if 'username' in st.session_state:
        del st.session_state.username
    st.rerun()

def check_authentication():
    """Verifica se usuário está autenticado"""
    if not st.session_state.authenticated:
        return False
    
    # Validar sessão no banco
    db = get_local_database()
    username = db.validate_session(st.session_state.session_id)
    
    if username and username == st.session_state.get('username'):
        return True
    else:
        # Sessão inválida, fazer logout
        st.session_state.authenticated = False
        st.session_state.user_data = {}
        return False

# Sistema robusto de persistência para PostgreSQL local
def get_persistent_session():
    """Retorna dados da sessão persistente"""
    return st.session_state.user_data

def ensure_robust_session_persistence():
    """Garante persistência robusta da sessão"""
    if st.session_state.authenticated and 'username' in st.session_state:
        db = get_local_database()
        # Renovar sessão se necessário
        db.create_session(st.session_state.username, st.session_state.session_id)

# Importar perfis
from profiles.solicitante_nova import render_solicitante_nova
from profiles.suprimentos_estoque import render_suprimentos_estoque
from profiles.aprovador_compras import render_aprovador_compras
from profiles.admin_dashboard import render_admin_dashboard
from profiles.admin_usuarios import render_admin_usuarios
from profiles.admin_configuracoes import render_admin_configuracoes
from profiles.suprimentos_catalogo import render_suprimentos_catalogo
from profiles.common_historico import render_common_historico
from profiles.solicitante_minhas import render_solicitante_minhas

# Configuração da página
st.set_page_config(
    page_title="Sistema de Compras - PostgreSQL Local",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_data():
    """Carrega dados do PostgreSQL local"""
    db = get_local_database()
    
    data = {
        'solicitacoes': db.get_all_solicitacoes(),
        'usuarios': db.get_all_users(),
        'configuracoes': {},
        'catalogo_produtos': db.get_catalogo_produtos()
    }
    
    # Carregar configurações
    config_keys = ['sla_urgente', 'sla_alta', 'sla_normal', 'sla_baixa', 
                   'empresa_nome', 'sistema_versao', 'max_upload_size']
    
    for key in config_keys:
        value = db.get_config(key)
        if value:
            try:
                # Tentar converter para número se possível
                data['configuracoes'][key] = int(value) if value.isdigit() else value
            except:
                data['configuracoes'][key] = value
    
    return data

def save_data(data):
    """Salva dados no PostgreSQL local"""
    db = get_local_database()
    
    # Salvar configurações
    if 'configuracoes' in data:
        for key, value in data['configuracoes'].items():
            db.set_config(key, str(value))
    
    # Salvar catálogo de produtos
    if 'catalogo_produtos' in data:
        db.update_catalogo_produtos(data['catalogo_produtos'])
    
    return True

def get_next_numero_solicitacao():
    """Gera próximo número de solicitação"""
    db = get_local_database()
    solicitacoes = db.get_all_solicitacoes()
    
    if not solicitacoes:
        return 1
    
    max_numero = max([sol.get('numero_solicitacao_estoque', 0) for sol in solicitacoes])
    return max_numero + 1

def main():
    """Função principal da aplicação"""
    # Inicializar sessão
    init_session()
    
    # Verificar autenticação
    if not check_authentication():
        render_login()
        return
    
    # Garantir persistência da sessão
    ensure_robust_session_persistence()
    
    # CSS customizado
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    st.markdown(get_sidebar_css(), unsafe_allow_html=True)
    
    # Carregar dados
    data = load_data()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 👤 Usuário Logado")
        user_data = st.session_state.user_data
        st.write(f"**{user_data.get('nome', 'Usuário')}**")
        st.write(f"Perfil: {user_data.get('perfil', 'N/A')}")
        st.write(f"Depto: {user_data.get('departamento', 'N/A')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
        
        st.markdown("---")
        
        # Menu baseado no perfil
        perfil = user_data.get('perfil', '')
        
        if perfil == 'admin':
            opcoes = [
                "📊 Dashboard Admin",
                "👥 Gerenciar Usuários", 
                "⚙️ Configurações",
                "📦 Catálogo de Produtos",
                "📋 Histórico Completo"
            ]
        elif perfil == 'solicitante':
            opcoes = [
                "🆕 Nova Solicitação",
                "📋 Minhas Solicitações",
                "📋 Histórico Completo"
            ]
        elif perfil == 'suprimentos':
            opcoes = [
                "📦 Estoque",
                "🛒 Catálogo de Produtos",
                "📋 Histórico Completo"
            ]
        elif perfil == 'aprovador':
            opcoes = [
                "✅ Aprovações",
                "📋 Histórico Completo"
            ]
        else:
            opcoes = ["📋 Histórico Completo"]
        
        opcao_selecionada = st.selectbox("Selecione uma opção:", opcoes)
    
    # Conteúdo principal
    if opcao_selecionada == "📊 Dashboard Admin":
        render_admin_dashboard(data, save_data)
    elif opcao_selecionada == "👥 Gerenciar Usuários":
        render_admin_usuarios(data, save_data)
    elif opcao_selecionada == "⚙️ Configurações":
        render_admin_configuracoes(data, save_data)
    elif opcao_selecionada == "🆕 Nova Solicitação":
        render_solicitante_nova(data, save_data, get_next_numero_solicitacao)
    elif opcao_selecionada == "📋 Minhas Solicitações":
        render_solicitante_minhas(data, save_data)
    elif opcao_selecionada == "📦 Estoque":
        render_suprimentos_estoque(data, save_data)
    elif opcao_selecionada == "✅ Aprovações":
        render_aprovador_compras(data, save_data)
    elif opcao_selecionada == "🛒 Catálogo de Produtos":
        render_suprimentos_catalogo(data, save_data)
    elif opcao_selecionada == "📋 Histórico Completo":
        render_common_historico(data, save_data)

def render_login():
    """Renderiza tela de login"""
    st.markdown("""
    <div style='text-align: center; padding: 2rem;'>
        <h1>🛒 Sistema de Compras</h1>
        <h3>PostgreSQL Local - EC2</h3>
        <p>Faça login para acessar o sistema</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("### 🔐 Login")
            username = st.text_input("👤 Usuário")
            password = st.text_input("🔒 Senha", type="password")
            login_button = st.form_submit_button("Entrar", use_container_width=True)
            
            if login_button:
                if username and password:
                    if authenticate_user(username, password):
                        st.success("✅ Login realizado com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos")
                else:
                    st.warning("⚠️ Preencha todos os campos")
        
        # Informações de acesso
        with st.expander("ℹ️ Credenciais de Teste"):
            st.markdown("""
            **Administrador:**
            - Usuário: `admin`
            - Senha: `admin123`
            
            **Solicitantes:**
            - Usuário: `Leonardo.Fragoso` | Senha: `Teste123`
            - Usuário: `Genival.Silva` | Senha: `Teste123`
            
            **Aprovador:**
            - Usuário: `Diretoria` | Senha: `Teste123`
            
            **Suprimentos:**
            - Usuário: `Fabio.Ramos` | Senha: `Teste123`
            """)

if __name__ == "__main__":
    main()
