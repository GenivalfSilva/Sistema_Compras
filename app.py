import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta, date
import json
import os
from typing import Dict, List
import math
import hashlib

# Detecta ambiente cloud
import os
IS_CLOUD = os.path.exists('/mount/src') or 'STREAMLIT_CLOUD' in os.environ

# Sistema simples para cloud
if IS_CLOUD:
    from simple_session import simple_login, ensure_session_persistence, simple_logout
    USE_DATABASE = False
else:
    # Tenta usar banco apenas local
    try:
        from database import get_database
        from session_manager import get_session_manager
        USE_DATABASE = True
    except ImportError:
        from simple_session import simple_login, ensure_session_persistence, simple_logout
        USE_DATABASE = False

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão de Compras - SLA",
    page_icon="📋",
    layout="wide"
)

# Arquivo para armazenar os dados
DATA_FILE = "compras_sla_data.json"

# Configurações baseadas na planilha Excel
ETAPAS_PROCESSO = [
    "Solicitação",
    "Suprimentos", 
    "Em Cotação",
    "Aguardando Aprovação",
    "Aprovado",
    "Reprovado",
    "Pedido Finalizado"
]

DEPARTAMENTOS = [
    "Manutenção",
    "TI", 
    "RH",
    "Financeiro",
    "Marketing",
    "Operações",
    "Outro"
]

PRIORIDADES = [
    "Normal",
    "Urgente",
    "Baixa",
    "Alta"
]

# SLA padrão por prioridade (em dias)
SLA_PADRAO = {
    "Urgente": 1,
    "Alta": 2,
    "Normal": 3,
    "Baixa": 5
}

# Configurações de upload e anexos
ALLOWED_FILE_TYPES = ["pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"]
UPLOAD_ROOT_DEFAULT = "uploads"

def load_data() -> Dict:
    """Carrega os dados do arquivo JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Migração/normalização de dados antigos
                data = migrate_data(data)
                return data
        except:
            return init_empty_data()
    return init_empty_data()

def init_empty_data() -> Dict:
    """Inicializa estrutura de dados vazia baseada na planilha"""
    return {
        "solicitacoes": [],
        "movimentacoes": [],  # Histórico de mudanças de etapa
        "configuracoes": {
            "sla_por_departamento": {},
            "proximo_numero_solicitacao": 1,
            "proximo_numero_pedido": 1,
            "limite_gerencia": 5000.0,
            "limite_diretoria": 15000.0,
            "upload_dir": UPLOAD_ROOT_DEFAULT
        },
        "notificacoes": [],
        "usuarios": []
    }

def save_data(data: Dict):
    """Salva os dados no arquivo JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def ensure_upload_dir(data: Dict):
    """Garante que a pasta de upload exista."""
    upload_dir = data.get("configuracoes", {}).get("upload_dir", UPLOAD_ROOT_DEFAULT)
    if not upload_dir:
        upload_dir = UPLOAD_ROOT_DEFAULT
        data["configuracoes"]["upload_dir"] = upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def save_uploaded_files(files: List, base_dir: str) -> List[Dict]:
    """Salva arquivos enviados e retorna metadados."""
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
        except Exception as e:
            # Ignora falhas individuais e segue com os demais
            pass
    return saved

def migrate_data(data: Dict) -> Dict:
    """Adiciona campos ausentes para compatibilidade com versões anteriores."""
    if not isinstance(data, dict):
        return init_empty_data()
    cfg = data.setdefault("configuracoes", {})
    cfg.setdefault("proximo_numero_solicitacao", 1)
    cfg.setdefault("proximo_numero_pedido", 1)
    cfg.setdefault("sla_por_departamento", {})
    cfg.setdefault("limite_gerencia", 5000.0)
    cfg.setdefault("limite_diretoria", 15000.0)
    cfg.setdefault("upload_dir", UPLOAD_ROOT_DEFAULT)
    data.setdefault("movimentacoes", [])
    data.setdefault("notificacoes", [])
    data.setdefault("usuarios", [])

    for s in data.setdefault("solicitacoes", []):
        s.setdefault("anexos_requisicao", [])
        s.setdefault("cotacoes", [])
        s.setdefault("aprovacoes", [])
        s.setdefault("valor_estimado", None)
        s.setdefault("valor_final", None)
        s.setdefault("fornecedor_recomendado", None)
        s.setdefault("fornecedor_final", None)
        s.setdefault("etapa_atual", s.get("status", "Solicitação"))
        s.setdefault("historico_etapas", [{
            "etapa": s.get("status", "Solicitação"),
            "data_entrada": s.get("carimbo_data_hora", datetime.datetime.now().isoformat()),
            "usuario": "Sistema"
        }])
    return data

def get_best_cotacao(cotacoes: List[Dict]) -> Dict:
    """Retorna a melhor cotação (menor valor)."""
    if not cotacoes:
        return {}
    best = None
    for c in cotacoes:
        if c.get("valor") is None:
            continue
        if best is None or c["valor"] < best["valor"]:
            best = c
    return best or {}

def get_next_pending_approval(aprovacoes: List[Dict]) -> Dict:
    """Retorna o próximo registro de aprovação pendente."""
    if not aprovacoes:
        return {}
    for a in aprovacoes:
        if a.get("nivel") == "Gerência&Diretoria" and a.get("status") == "Pendente":
            return a
    return {}

def add_notification(data: Dict, perfil: str, numero: int, mensagem: str):
    """Adiciona uma notificação interna para o perfil informado."""
    try:
        data.setdefault("notificacoes", [])
        data["notificacoes"].append({
            "perfil": perfil,
            "numero": numero,
            "mensagem": mensagem,
            "data": datetime.datetime.now().isoformat(),
            "lida": False
        })
    except Exception:
        # Falha silenciosa para não interromper o fluxo
        pass

# ===== Autenticação simples (local) =====
SALT = "ziran_local_salt_v1"

def hash_password(password: str) -> str:
    try:
        return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()
    except Exception:
        return ""

def find_user(data: Dict, username: str) -> Dict:
    for u in data.get("usuarios", []):
        if u.get("username", "").lower() == username.lower():
            return u
    return {}

def authenticate_user(data: Dict, username: str, password: str) -> Dict:
    if USE_DATABASE:
        db = get_database()
        return db.authenticate_user(username, password)
    else:
        user = find_user(data, username)
        if not user:
            return {}
        if user.get("senha_hash") == hash_password(password):
            return user
        return {}

def ensure_admin_user(data: Dict) -> bool:
    """Garante um usuário admin inicial. Retorna True se criou."""
    usuarios = data.setdefault("usuarios", [])
    if any(u.get("perfil") == "Admin" for u in usuarios):
        return False
    admin_user = {
        "username": "admin",
        "nome": "Administrador",
        "perfil": "Admin",
        "departamento": "TI",
        "senha_hash": hash_password("admin123")
    }
    usuarios.append(admin_user)
    return True

def add_user(data: Dict, username: str, nome: str, perfil: str, departamento: str, senha: str) -> str:
    if not username or not senha or not perfil:
        return "Preencha usuário, senha e perfil."
    
    if USE_DATABASE:
        db = get_database()
        success = db.add_user(username, nome or username, perfil, departamento or "Outro", senha)
        return "" if success else "Usuário já existe."
    else:
        if find_user(data, username):
            return "Usuário já existe."
        data.setdefault("usuarios", []).append({
            "username": username,
            "nome": nome or username,
            "perfil": perfil,
            "departamento": departamento or "Outro",
            "senha_hash": hash_password(senha)
        })
        return ""

def reset_user_password(data: Dict, username: str, nova_senha: str) -> str:
    user = find_user(data, username)
    if not user:
        return "Usuário não encontrado."
    user["senha_hash"] = hash_password(nova_senha)
    return ""

def calcular_dias_uteis(data_inicio: datetime.datetime, data_fim: datetime.datetime = None) -> int:
    """Calcula dias úteis entre duas datas (excluindo fins de semana)"""
    if data_fim is None:
        data_fim = datetime.datetime.now()
    
    try:
        # Converte para date se necessário
        if isinstance(data_inicio, str):
            data_inicio = datetime.datetime.fromisoformat(data_inicio)
        if isinstance(data_fim, str):
            data_fim = datetime.datetime.fromisoformat(data_fim)
            
        data_atual = data_inicio.date()
        data_final = data_fim.date()
        
        dias_uteis = 0
        while data_atual <= data_final:
            # 0-6 onde 0=segunda, 6=domingo
            if data_atual.weekday() < 5:  # Segunda a sexta
                dias_uteis += 1
            data_atual += timedelta(days=1)
            
        return max(0, dias_uteis - 1)  # Subtrai 1 para não contar o dia inicial
    except:
        return 0

def verificar_sla_cumprido(dias_atendimento: int, sla_dias: int) -> str:
    """Verifica se o SLA foi cumprido"""
    if dias_atendimento <= sla_dias:
        return "Sim"
    else:
        return "Não"

def obter_sla_por_prioridade(prioridade: str, departamento: str = None) -> int:
    """Obtém SLA baseado na prioridade e departamento"""
    # Por enquanto usa SLA padrão, mas pode ser customizado por departamento
    return SLA_PADRAO.get(prioridade, 3)

def main():
    # CSS personalizado com cores da marca Ziran
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
    
    :root {
        --ziran-red: #E53E3E;
        --ziran-red-light: #FC8181;
        --ziran-red-dark: #C53030;
        --ziran-gray: #2D3748;
        --ziran-gray-light: #4A5568;
        --ziran-white: #FFFFFF;
        --ziran-bg-light: #F7FAFC;
        --ziran-bg-gray: #EDF2F7;
    }
    
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: linear-gradient(rgba(247, 250, 252, 0.95), rgba(247, 250, 252, 0.95)), 
                    url('./assets/img/ziran fundo.jpg') center/cover no-repeat fixed;
        min-height: 100vh;
    }
    
    .background-overlay {
        background: linear-gradient(135deg, rgba(229, 62, 62, 0.05) 0%, rgba(197, 48, 48, 0.05) 100%);
        backdrop-filter: blur(1px);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .main-header {
        background: linear-gradient(135deg, var(--ziran-red) 0%, var(--ziran-red-dark) 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(229, 62, 62, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .title-text {
        color: var(--ziran-white);
        margin: 0;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 2.2rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .subtitle-text {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        font-weight: 400;
        opacity: 0.9;
    }
    .brand-text {
        color: var(--ziran-gray);
        font-weight: 600;
        font-size: 1rem;
        text-shadow: none;
        background: rgba(255, 255, 255, 0.9);
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        display: inline-block;
        border: 1px solid rgba(45, 55, 72, 0.1);
    }
    .section-header {
        background: linear-gradient(135deg, var(--ziran-red) 0%, var(--ziran-red-dark) 100%);
        color: var(--ziran-white);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin: 2rem 0 1.5rem 0;
        text-align: center;
        font-weight: 600;
        font-size: 1.3rem;
        font-family: 'Poppins', sans-serif;
        box-shadow: 0 4px 16px rgba(229, 62, 62, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .info-box {
        background: linear-gradient(135deg, var(--ziran-bg-light) 0%, var(--ziran-bg-gray) 100%);
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 4px solid var(--ziran-red);
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        color: var(--ziran-gray);
    }
    .success-box {
        background: linear-gradient(135deg, #F0FFF4 0%, #C6F6D5 100%);
        border: 1px solid #9AE6B4;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 4px solid #38A169;
        color: #22543D;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(56, 161, 105, 0.1);
    }
    .warning-box {
        background: linear-gradient(135deg, #FFFAF0 0%, #FED7AA 100%);
        border: 1px solid #F6AD55;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 4px solid #ED8936;
        color: #C05621;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(237, 137, 54, 0.1);
    }
    .form-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin: 1rem 0;
    }
    .form-section {
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--ziran-bg-gray);
    }
    .form-section:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }
    .form-section h3 {
        color: var(--ziran-gray);
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--ziran-red);
        display: inline-block;
    }
    .stats-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(8px);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid var(--ziran-red);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        margin: 0.5rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    .stats-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(229, 62, 62, 0.12);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--ziran-red);
        margin: 0;
        font-family: 'Poppins', sans-serif;
    }
    .metric-label {
        color: var(--ziran-gray-light);
        font-size: 0.9rem;
        margin: 0;
        font-weight: 500;
    }
    .stButton > button {
        background: linear-gradient(135deg, var(--ziran-red) 0%, var(--ziran-red-dark) 100%) !important;
        color: var(--ziran-white) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 16px rgba(229, 62, 62, 0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(229, 62, 62, 0.4) !important;
        background: linear-gradient(135deg, var(--ziran-red-light) 0%, var(--ziran-red) 100%) !important;
    }
    .stSelectbox label, .stTextInput label, .stTextArea label, .stNumberInput label {
        font-weight: 500 !important;
        color: var(--ziran-gray) !important;
        font-size: 0.95rem !important;
        margin-bottom: 0.5rem !important;
    }
    .stFileUploader {
        border: 2px dashed var(--ziran-red-light) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        background: var(--ziran-bg-light) !important;
        transition: all 0.3s ease !important;
    }
    .stFileUploader:hover {
        border-color: var(--ziran-red) !important;
        background: var(--ziran-white) !important;
    }
    .sidebar .stSelectbox {
        margin-bottom: 1rem;
    }
    /* Sidebar customization */
    .css-1d391kg {
        background-color: var(--ziran-white) !important;
    }
    .css-1d391kg .stSelectbox > div > div {
        background-color: var(--ziran-bg-light) !important;
        border: 1px solid var(--ziran-red-light) !important;
    }
    /* Metrics styling */
    .css-1xarl3l {
        color: var(--ziran-red) !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header elegante com logo
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        # Logo com melhor apresentação
        logo_path = "assets/img/logo_ziran.jpg"
        if os.path.exists(logo_path):
            st.image(logo_path, width=140)
        else:
            st.markdown('<div style="font-size: 4rem; text-align: center; color: white;">🏢</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<h1 class="title-text">📋 Sistema de Gestão de Compras - SLA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle-text">Controle de Solicitações e Medição de SLA</p>', unsafe_allow_html=True)
        st.markdown('<p class="brand-text">✨ Ziran - Gestão Inteligente</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Carrega os dados
    data = load_data()
    
    # Inicializa gerenciador de sessões se disponível
    if USE_DATABASE:
        session_manager = get_session_manager()
        session_manager.restore_session()
    else:
        # Cloud/simple mode: tenta restaurar sessão via cookie
        try:
            ensure_session_persistence()
        except Exception:
            pass
    
    # Sidebar com design melhorado
    st.sidebar.markdown("""
    <div style="background: linear-gradient(135deg, var(--ziran-red) 0%, var(--ziran-red-dark) 100%); 
                padding: 1rem; border-radius: 12px; margin-bottom: 1rem; text-align: center;">
        <h3 style="color: white; margin: 0; font-family: 'Poppins', sans-serif;">🏢 ZIRAN</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">Sistema de Compras</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Garante que existe um usuário admin
    if USE_DATABASE:
        db = get_database()
        # Cria admin se não existir
        admin_exists = db.authenticate_user("admin", "admin123")
        if not admin_exists:
            db.add_user("admin", "Administrador", "Admin", "TI", "admin123")
    else:
        changed = ensure_admin_user(data)
        if changed:
            save_data(data)
    
    if "usuario" not in st.session_state:
        st.sidebar.markdown("### 🔐 Login")
        with st.sidebar.form("login_form"):
            login_user = st.text_input("Usuário")
            login_pass = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar")
        if entrar:
            if USE_DATABASE:
                session_manager = get_session_manager()
                if session_manager.login(login_user.strip(), login_pass):
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
            else:
                # Sistema simples para cloud
                if IS_CLOUD:
                    user = simple_login(data, login_user.strip(), login_pass)
                else:
                    user = authenticate_user(data, login_user.strip(), login_pass)
                
                if user:
                    st.session_state["usuario"] = user
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        
        st.info("Faça login para acessar o sistema.")
        return
    
    # Continua com o usuário logado
    usuario = st.session_state.get("usuario", {})
    perfil_atual = usuario.get("perfil", "Solicitante")
    nome_atual = usuario.get("nome", usuario.get("username", "Usuário"))
    
    with st.sidebar.expander("👤 Usuário", expanded=True):
        st.markdown(f"**Nome:** {nome_atual}")
        st.markdown(f"**Perfil:** {perfil_atual}")
        
        if st.button("🚪 Logout", key="logout_btn"):
            if USE_DATABASE:
                session_manager = get_session_manager()
                session_manager.logout()
            else:
                simple_logout()
            st.rerun()
    
    # Notificações por perfil logado
    notif_alvos = [perfil_atual] if perfil_atual != "Admin" else ["Gerência&Diretoria", "Suprimentos"]
    pend_notif = [n for n in data.get("notificacoes", []) if n.get("perfil") in notif_alvos and not n.get("lida")]
    
    if pend_notif:
        st.sidebar.markdown("### 🔔 Notificações")
        for n in pend_notif[:5]:
            st.sidebar.info(f"#{n.get('numero')} - {n.get('mensagem')}")

    # Navegação por perfil
    st.sidebar.markdown("### 🔧 Navegação")
    st.sidebar.markdown("*Selecione uma opção abaixo:*")
    
    def opcoes_por_perfil(p: str) -> List[str]:
        if p == "Admin":
            return [
                "📝 Nova Solicitação",
                "🔄 Mover para Próxima Etapa",
                "📱 Aprovações",
                "📊 Dashboard SLA",
                "📚 Histórico por Etapa",
                "⚙️ Configurações SLA",
                "👥 Gerenciar Usuários"
            ]
        if p == "Gerência&Diretoria":
            return [
                "📱 Aprovações",
                "📊 Dashboard SLA",
                "📚 Histórico por Etapa"
            ]
        if p == "Suprimentos":
            return [
                "🔄 Mover para Próxima Etapa",
                "📊 Dashboard SLA",
                "📚 Histórico por Etapa"
            ]
        # Solicitante
        return [
            "📝 Nova Solicitação",
            "📊 Dashboard SLA",
            "📚 Histórico por Etapa"
        ]
    opcoes = opcoes_por_perfil(perfil_atual)
    opcao = st.sidebar.selectbox("Escolha uma opção:", opcoes)
    
    # Estatísticas rápidas com design melhorado
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Estatísticas Rápidas")
    
    total_solicitacoes = len(data["solicitacoes"])
    solicitacoes_pendentes = len([s for s in data["solicitacoes"] if s["status"] != "Pedido Finalizado"])
    
    # Cards de métricas na sidebar
    st.sidebar.markdown(f"""
    <div class="stats-card">
        <p class="metric-value">{total_solicitacoes}</p>
        <p class="metric-label">Total de Solicitações</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
    <div class="stats-card">
        <p class="metric-value">{solicitacoes_pendentes}</p>
        <p class="metric-label">Pendentes</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Adicionar mais uma métrica útil
    finalizadas = len([s for s in data["solicitacoes"] if s["status"] == "Pedido Finalizado"])
    st.sidebar.markdown(f"""
    <div class="stats-card">
        <p class="metric-value">{finalizadas}</p>
        <p class="metric-label">Finalizadas</p>
    </div>
    """, unsafe_allow_html=True)
    
    if total_solicitacoes > 0:
        # Calcula SLA médio
        slas_cumpridos = 0
        total_com_sla = 0
        for sol in data["solicitacoes"]:
            if sol.get("dias_atendimento") is not None and sol.get("sla_cumprido"):
                total_com_sla += 1
                if sol["sla_cumprido"] == "Sim":
                    slas_cumpridos += 1
        
        if total_com_sla > 0:
            taxa_sla = (slas_cumpridos / total_com_sla) * 100
            st.sidebar.metric("Taxa SLA Cumprido", f"{taxa_sla:.1f}%")
    
    if opcao == "📝 Nova Solicitação":
        st.markdown('<div class="section-header">📝 Nova Solicitação de Compra</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">💡 <strong>Baseado na estrutura da planilha Excel - Aba \'Solicitação\'</strong></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        
        with st.form("nova_solicitacao"):
            # Seção 1: Dados do Solicitante
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.markdown('<h3>👤 Dados do Solicitante</h3>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                solicitante = st.text_input(
                    "Solicitante (Nome e Sobrenome)*", 
                    help="Campo obrigatório conforme planilha",
                    placeholder="Digite o nome completo do solicitante"
                )
                departamento = st.selectbox(
                    "Departamento*",
                    DEPARTAMENTOS,
                    help="Departamento do solicitante"
                )
            
            with col2:
                prioridade = st.selectbox(
                    "Prioridade*",
                    PRIORIDADES,
                    help="Define o SLA automaticamente"
                )
                # Mostra SLA que será aplicado
                sla_dias = obter_sla_por_prioridade(prioridade if 'prioridade' in locals() else "Normal")
                st.info(f"📅 **SLA:** {sla_dias} dias úteis para prioridade '{prioridade if 'prioridade' in locals() else 'Normal'}'")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Seção 2: Dados da Solicitação
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.markdown('<h3>📋 Dados da Solicitação</h3>', unsafe_allow_html=True)
            
            col3, col4 = st.columns([2, 1])
            with col3:
                descricao = st.text_area(
                    "Descrição*", 
                    height=120,
                    help="Descrição detalhada da solicitação",
                    placeholder="Descreva detalhadamente o que está sendo solicitado..."
                )
            
            with col4:
                aplicacao = st.number_input(
                    "Aplicação (Código)*", 
                    min_value=1, 
                    step=1,
                    help="Código numérico da aplicação",
                    value=1
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Seção 3: Anexos
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.markdown('<h3>📎 Anexos da Solicitação</h3>', unsafe_allow_html=True)
            
            anexos_files = st.file_uploader(
                "Faça upload dos arquivos relacionados à solicitação (opcional)",
                type=ALLOWED_FILE_TYPES,
                accept_multiple_files=True,
                help="Tipos permitidos: PDF, PNG, JPG, JPEG, DOC, DOCX, XLS, XLSX"
            )
            
            if anexos_files:
                st.success(f"✅ {len(anexos_files)} arquivo(s) selecionado(s)")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Seção 4: Informações Automáticas
            st.markdown('<div class="form-section">', unsafe_allow_html=True)
            st.markdown('<h3>⚙️ Informações de Controle</h3>', unsafe_allow_html=True)
            st.markdown('<p style="color: #64748b; font-style: italic; margin-bottom: 1rem;">Os campos abaixo são preenchidos automaticamente pelo sistema</p>', unsafe_allow_html=True)
            
            col5, col6 = st.columns(2)
            with col5:
                st.text_input(
                    "Nº Solicitação (Estoque)", 
                    value="Será gerado automaticamente", 
                    disabled=True
                )
                st.text_input(
                    "Status Inicial", 
                    value="Solicitação", 
                    disabled=True
                )
            
            with col6:
                st.text_input(
                    "Data/Hora de Criação", 
                    value=datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S'), 
                    disabled=True
                )
                st.text_input(
                    "SLA Aplicado", 
                    value=f"{sla_dias} dias úteis", 
                    disabled=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Botão de submissão
            st.markdown('<br>', unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "🚀 Criar Solicitação", 
                use_container_width=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if submitted:
            if solicitante and departamento and descricao and aplicacao:
                # Gera números automáticos
                numero_solicitacao = data["configuracoes"]["proximo_numero_solicitacao"]
                data["configuracoes"]["proximo_numero_solicitacao"] += 1
                
                # Calcula SLA baseado na prioridade
                sla_dias = obter_sla_por_prioridade(prioridade, departamento)
                
                # Salva anexos da solicitação
                upload_root = ensure_upload_dir(data)
                sol_dir = os.path.join(upload_root, f"solicitacao_{numero_solicitacao}", "requisicao")
                anexos_meta = save_uploaded_files(anexos_files, sol_dir)
                
                nova_solicitacao = {
                    # Campos da planilha Excel
                    "carimbo_data_hora": datetime.datetime.now().isoformat(),
                    "solicitante": solicitante,
                    "departamento": departamento,
                    "prioridade": prioridade,
                    "descricao": descricao,
                    "aplicacao": aplicacao,
                    "status": "Solicitação",  # Primeira etapa
                    "numero_solicitacao_estoque": numero_solicitacao,
                    "numero_pedido_compras": None,
                    "data_numero_pedido": None,
                    "data_cotacao": None,
                    "data_entrega": None,
                    "sla_dias": sla_dias,
                    "dias_atendimento": None,
                    "sla_cumprido": None,
                    "observacoes": None,
                    "anexos_requisicao": anexos_meta,
                    "cotacoes": [],
                    "aprovacoes": [],
                    "valor_estimado": None,
                    "valor_final": None,
                    "fornecedor_recomendado": None,
                    "fornecedor_final": None,
                    
                    # Campos de controle interno
                    "id": len(data["solicitacoes"]) + 1,
                    "etapa_atual": "Solicitação",
                    "historico_etapas": [{
                        "etapa": "Solicitação",
                        "data_entrada": datetime.datetime.now().isoformat(),
                        "usuario": "Sistema"
                    }]
                }
                
                data["solicitacoes"].append(nova_solicitacao)
                save_data(data)
                
                # Mensagem de sucesso melhorada
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown(f'<h3 style="color: #065f46; margin: 0 0 1rem 0; font-family: Poppins;">🎉 Solicitação #{numero_solicitacao} Criada com Sucesso!</h3>', unsafe_allow_html=True)
                
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.markdown(f"**📅 Data/Hora:** {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
                    st.markdown(f"**⏱️ SLA:** {sla_dias} dias úteis")
                with col_info2:
                    st.markdown(f"**📊 Status:** Solicitação (Etapa 1 de 7)")
                    st.markdown(f"**📎 Anexos:** {len(anexos_meta)} arquivo(s)")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Próximos passos com design melhorado
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #1e40af; margin: 0 0 1rem 0; font-family: Poppins;">🔄 Próximos Passos</h4>', unsafe_allow_html=True)
                st.markdown("**1.** A solicitação será analisada pela área de **Suprimentos**")
                st.markdown("**2.** Use a opção **'🔄 Mover para Próxima Etapa'** para avançar o processo")
                st.markdown("**3.** Acompanhe o progresso no **Dashboard SLA** ou **Histórico por Etapa**")
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                st.markdown('<h4 style="color: #92400e; margin: 0 0 0.5rem 0;">⚠️ Campos Obrigatórios</h4>', unsafe_allow_html=True)
                st.markdown("Por favor, preencha todos os campos marcados com **asterisco (*)** antes de continuar.")
                st.markdown('</div>', unsafe_allow_html=True)
    
    elif opcao == "🔄 Mover para Próxima Etapa":
        st.markdown('<div class="section-header">🔄 Mover Solicitação para Próxima Etapa</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">⚡ <strong>Controle do fluxo do processo de compras</strong></div>', unsafe_allow_html=True)
        
        # Filtra solicitações que não estão finalizadas
        solicitacoes_ativas = [s for s in data["solicitacoes"] if s["status"] != "Pedido Finalizado"]
        
        if not solicitacoes_ativas:
            st.warning("📋 Não há solicitações ativas para mover.")
            st.info("💡 Crie uma nova solicitação primeiro!")
            return
        
        # Seleção da solicitação
        st.subheader("1️⃣ Selecione a Solicitação")
        
        opcoes_solicitacoes = []
        for s in solicitacoes_ativas:
            data_criacao = datetime.datetime.fromisoformat(s["carimbo_data_hora"]).strftime('%d/%m/%Y %H:%M')
            opcoes_solicitacoes.append(
                f"#{s['numero_solicitacao_estoque']} - {s['solicitante']} - {s['status']} ({data_criacao})"
            )
        
        solicitacao_selecionada = st.selectbox("Escolha a solicitação:", opcoes_solicitacoes)
        
        if solicitacao_selecionada:
            # Extrai o número da solicitação
            numero_solicitacao = int(solicitacao_selecionada.split('#')[1].split(' -')[0])
            solicitacao = next(s for s in solicitacoes_ativas if s['numero_solicitacao_estoque'] == numero_solicitacao)
            
            # Mostra detalhes da solicitação
            st.subheader("2️⃣ Detalhes da Solicitação Atual")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Número", f"#{solicitacao['numero_solicitacao_estoque']}")
                st.metric("Solicitante", solicitacao['solicitante'])
                st.metric("Departamento", solicitacao['departamento'])
            
            with col2:
                st.metric("Status Atual", solicitacao['status'])
                st.metric("Prioridade", solicitacao['prioridade'])
                st.metric("SLA (dias)", solicitacao['sla_dias'])
            
            with col3:
                data_criacao = datetime.datetime.fromisoformat(solicitacao["carimbo_data_hora"])
                dias_decorridos = calcular_dias_uteis(data_criacao)
                st.metric("Dias Decorridos", dias_decorridos)
                
                # Calcula status do SLA
                if dias_decorridos <= solicitacao['sla_dias']:
                    st.success("✅ Dentro do SLA")
                else:
                    st.error("❌ SLA Estourado")
            
            st.markdown(f"**Descrição:** {solicitacao['descricao']}")
            
            # Determina próxima etapa
            etapa_atual = solicitacao['status']
            proxima_etapa = None
            
            if etapa_atual == "Solicitação":
                proxima_etapa = "Suprimentos"
            elif etapa_atual == "Suprimentos":
                proxima_etapa = "Em Cotação"
            elif etapa_atual == "Em Cotação":
                proxima_etapa = "Aguardando Aprovação"
            elif etapa_atual == "Aguardando Aprovação":
                proxima_etapa = None  # Aprovações ocorrem na página 📱 Aprovações
            elif etapa_atual == "Aprovado":
                proxima_etapa = "Pedido Finalizado"
            
            if proxima_etapa:
                st.subheader(f"3️⃣ Mover para: {proxima_etapa}")
                
                with st.form("mover_etapa"):
                    # Campos específicos por etapa
                    if proxima_etapa == "Suprimentos":
                        st.markdown("**📦 Dados para Suprimentos**")
                        col1, col2 = st.columns(2)
                        with col1:
                            responsavel = st.text_input("Responsável Suprimentos*")
                        with col2:
                            observacoes = st.text_area("Observações", height=100)
                    
                    elif proxima_etapa == "Em Cotação":
                        st.markdown("**💰 Dados para Cotação**")
                        col1, col2 = st.columns(2)
                        with col1:
                            numero_pedido = st.number_input("Nº Pedido (Compras)*", min_value=1, step=1)
                            data_pedido = st.date_input("Data Nº Pedido*", value=date.today())
                        with col2:
                            data_cotacao = st.date_input("Data Cotação", value=date.today())
                            observacoes = st.text_area("Observações", height=100)
                    
                    elif proxima_etapa == "Aguardando Aprovação":
                        st.markdown("**🧾 Registrar Cotações (mín. 1, ideal 3)**")
                        st.info("Cadastre as cotações recebidas para seguir para aprovação. Anexe os documentos se possível.")
                        cotacoes_input = []
                        for idx in range(1, 4):
                            with st.expander(f"Cotação {idx}", expanded=(idx == 1)):
                                fornecedor = st.text_input(f"Fornecedor {idx}", key=f"cot_fornecedor_{numero_solicitacao}_{idx}")
                                valor = st.number_input(f"Valor {idx} (R$)", min_value=0.0, step=0.01, key=f"cot_valor_{numero_solicitacao}_{idx}")
                                prazo = st.number_input(f"Prazo {idx} (dias)", min_value=0, step=1, key=f"cot_prazo_{numero_solicitacao}_{idx}")
                                validade = st.date_input(f"Validade {idx}", value=date.today(), key=f"cot_validade_{numero_solicitacao}_{idx}")
                                anexos = st.file_uploader(
                                    f"Anexos Cotação {idx}",
                                    type=ALLOWED_FILE_TYPES,
                                    accept_multiple_files=True,
                                    key=f"cot_anexos_{numero_solicitacao}_{idx}"
                                )
                                obs_c = st.text_area(f"Observações {idx}", key=f"cot_obs_{numero_solicitacao}_{idx}")
                                cotacoes_input.append((fornecedor, valor, prazo, validade, anexos, obs_c))
                    
                    elif proxima_etapa == "Pedido Finalizado":
                        st.markdown("**✅ Finalização do Pedido**")
                        col1, col2 = st.columns(2)
                        with col1:
                            data_entrega = st.date_input("Data Entrega*", value=date.today())
                            valor_final = st.number_input("Valor Final (R$)", min_value=0.0, step=0.01)
                        with col2:
                            fornecedor_final = st.text_input("Fornecedor Final")
                            observacoes = st.text_area("Observações Finais", height=100)
                    
                    submitted = st.form_submit_button(f"🚀 Mover para {proxima_etapa}", use_container_width=True)
                    
                    if submitted:
                        # Atualiza a solicitação
                        for i, s in enumerate(data["solicitacoes"]):
                            if s["numero_solicitacao_estoque"] == numero_solicitacao:
                                # Atualiza status
                                data["solicitacoes"][i]["status"] = proxima_etapa
                                data["solicitacoes"][i]["etapa_atual"] = proxima_etapa
                                
                                # Adiciona ao histórico
                                data["solicitacoes"][i]["historico_etapas"].append({
                                    "etapa": proxima_etapa,
                                    "data_entrada": datetime.datetime.now().isoformat(),
                                    "usuario": responsavel if 'responsavel' in locals() else "Sistema"
                                })
                                
                                # Atualiza campos específicos
                                if proxima_etapa == "Em Cotação" and 'numero_pedido' in locals():
                                    data["solicitacoes"][i]["numero_pedido_compras"] = numero_pedido
                                    data["solicitacoes"][i]["data_numero_pedido"] = data_pedido.isoformat()
                                    if 'data_cotacao' in locals():
                                        data["solicitacoes"][i]["data_cotacao"] = data_cotacao.isoformat()
                                elif proxima_etapa == "Aguardando Aprovação":
                                    cotacoes_salvas = []
                                    upload_root = ensure_upload_dir(data)
                                    for idx, (fornecedor, valor, prazo, validade, anexos, obs_c) in enumerate(cotacoes_input, start=1):
                                        try:
                                            if fornecedor and valor and float(valor) > 0:
                                                cot_dir = os.path.join(upload_root, f"solicitacao_{numero_solicitacao}", "cotacoes", f"cotacao_{idx}")
                                                anexos_meta = save_uploaded_files(anexos, cot_dir)
                                                cotacoes_salvas.append({
                                                    "fornecedor": fornecedor,
                                                    "valor": float(valor),
                                                    "prazo": int(prazo) if prazo is not None else None,
                                                    "validade": validade.isoformat() if hasattr(validade, 'isoformat') else str(validade),
                                                    "observacoes": obs_c,
                                                    "anexos": anexos_meta
                                                })
                                        except Exception:
                                            pass
                                    # Persiste cotações e recomenda melhor
                                    data["solicitacoes"][i]["cotacoes"] = cotacoes_salvas
                                    melhor = get_best_cotacao(cotacoes_salvas)
                                    if melhor:
                                        data["solicitacoes"][i]["fornecedor_recomendado"] = melhor.get("fornecedor")
                                        data["solicitacoes"][i]["valor_estimado"] = melhor.get("valor")
                                        # Notifica Gerência&Diretoria quando há cotações para aprovação
                                        try:
                                            add_notification(data, "Gerência&Diretoria", numero_solicitacao, "Solicitação com cotações aguardando aprovação.")
                                        except Exception:
                                            pass
                                
                                elif proxima_etapa == "Pedido Finalizado":
                                    data["solicitacoes"][i]["data_entrega"] = data_entrega.isoformat()
                                    # Persistir dados finais
                                    if 'valor_final' in locals():
                                        data["solicitacoes"][i]["valor_final"] = valor_final
                                    if 'fornecedor_final' in locals():
                                        data["solicitacoes"][i]["fornecedor_final"] = fornecedor_final
                                    
                                    # Calcula dias de atendimento e SLA
                                    data_inicio = datetime.datetime.fromisoformat(s["carimbo_data_hora"])
                                    data_fim = datetime.datetime.combine(data_entrega, datetime.time())
                                    dias_atendimento = calcular_dias_uteis(data_inicio, data_fim)
                                    
                                    data["solicitacoes"][i]["dias_atendimento"] = dias_atendimento
                                    data["solicitacoes"][i]["sla_cumprido"] = verificar_sla_cumprido(
                                        dias_atendimento, s["sla_dias"]
                                    )
                                
                                # Notificação quando entra em aprovação
                                if proxima_etapa == "Aguardando Aprovação":
                                    try:
                                        add_notification(data, "Gerência&Diretoria", numero_solicitacao, "Solicitação aguardando aprovação.")
                                    except Exception:
                                        pass
                                
                                # Atualiza observações
                                if 'observacoes' in locals() and observacoes:
                                    data["solicitacoes"][i]["observacoes"] = observacoes
                                
                                break
                        
                        save_data(data)
                        
                        st.success(f"✅ Solicitação #{numero_solicitacao} movida para '{proxima_etapa}' com sucesso!")
                        
                        if proxima_etapa == "Pedido Finalizado":
                            # Mostra resultado final do SLA
                            solicitacao_atualizada = next(s for s in data["solicitacoes"] if s['numero_solicitacao_estoque'] == numero_solicitacao)
                            st.info(f"⏱️ Dias de atendimento: {solicitacao_atualizada['dias_atendimento']}")
                            
                            if solicitacao_atualizada['sla_cumprido'] == "Sim":
                                st.success(f"🎯 SLA CUMPRIDO! (Limite: {solicitacao_atualizada['sla_dias']} dias)")
                            else:
                                st.error(f"⚠️ SLA NÃO CUMPRIDO! (Limite: {solicitacao_atualizada['sla_dias']} dias)")
                        
                        st.rerun()
            else:
                st.info("✅ Esta solicitação já está finalizada!")
    
    elif opcao == "📱 Aprovações":
        st.markdown('<div class="section-header">📱 Aprovações</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">🛡️ <strong>Somente Gerência&Diretoria ou Admin podem aprovar</strong></div>', unsafe_allow_html=True)

        if perfil_atual not in ["Gerência&Diretoria", "Admin"]:
            st.info("Esta página é restrita a Gerência&Diretoria ou Admin.")
        else:
            pendentes = [s for s in data.get("solicitacoes", []) if s.get("status") == "Aguardando Aprovação"]
            if not pendentes:
                st.success("✅ Não há solicitações pendentes de aprovação.")
            else:
                opcoes = []
                for s in pendentes:
                    data_criacao = datetime.datetime.fromisoformat(s["carimbo_data_hora"]).strftime('%d/%m/%Y %H:%M')
                    opcoes.append(f"#{s['numero_solicitacao_estoque']} - {s['solicitante']} - {s['departamento']} - {s['prioridade']} ({data_criacao})")

                escolha = st.selectbox("Selecione a solicitação para aprovar:", opcoes)
                if escolha:
                    numero_solicitacao = int(escolha.split('#')[1].split(' -')[0])
                    sol = next(s for s in pendentes if s['numero_solicitacao_estoque'] == numero_solicitacao)

                    st.subheader(f"Detalhes da Solicitação #{numero_solicitacao}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Prioridade", sol.get('prioridade', 'N/A'))
                        st.metric("SLA (dias)", sol.get('sla_dias', 'N/A'))
                    with col2:
                        data_criacao_dt = datetime.datetime.fromisoformat(sol["carimbo_data_hora"]) 
                        st.metric("Dias decorridos", calcular_dias_uteis(data_criacao_dt))
                    with col3:
                        anexos_qtd = len(sol.get('anexos_requisicao', []))
                        st.metric("Anexos", anexos_qtd)

                    st.markdown("**Descrição**")
                    st.write(sol.get('descricao', ''))

                    comentarios = st.text_area("Comentários (opcional)", key=f"aprov_coment_{numero_solicitacao}")
                    a1, a2 = st.columns(2)
                    with a1:
                        aprovar = st.button("✅ Aprovar", key=f"aprovar_{numero_solicitacao}")
                    with a2:
                        reprovar = st.button("❌ Reprovar", key=f"reprovar_{numero_solicitacao}")

                    if aprovar or reprovar:
                        for i, s in enumerate(data["solicitacoes"]):
                            if s["numero_solicitacao_estoque"] == numero_solicitacao:
                                novo_status = "Aprovado" if aprovar else "Reprovado"
                                data["solicitacoes"][i]["status"] = novo_status
                                data["solicitacoes"][i]["etapa_atual"] = novo_status
                                data["solicitacoes"][i].setdefault("aprovacoes", []).append({
                                    "nivel": "Gerência&Diretoria",
                                    "aprovador": nome_atual,
                                    "status": novo_status,
                                    "comentarios": comentarios,
                                    "data": datetime.datetime.now().isoformat()
                                })
                                data["solicitacoes"][i]["historico_etapas"].append({
                                    "etapa": novo_status,
                                    "data_entrada": datetime.datetime.now().isoformat(),
                                    "usuario": f"Aprovação - {perfil_atual}"
                                })
                                # Notificação
                                try:
                                    if novo_status == "Aprovado":
                                        add_notification(data, "Suprimentos", numero_solicitacao, "Solicitação aprovada. Prosseguir com pedido.")
                                    else:
                                        add_notification(data, "Solicitante", numero_solicitacao, "Solicitação reprovada.")
                                except Exception:
                                    pass
                                break
                        save_data(data)
                        if aprovar:
                            st.success("✅ Solicitação aprovada com sucesso! Avance para 'Pedido Finalizado'.")
                        else:
                            st.warning("❌ Solicitação reprovada.")
                        st.rerun()

    elif opcao == "📊 Dashboard SLA":
        st.markdown('<div class="section-header">📊 Dashboard SLA</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">📈 <strong>Visualização baseada nas abas da planilha Excel</strong></div>', unsafe_allow_html=True)
        
        if not data["solicitacoes"]:
            st.markdown('<div class="warning-box">📋 <strong>Não há dados para exibir no dashboard.</strong><br>💡 Crie algumas solicitações primeiro!</div>', unsafe_allow_html=True)
        else:
            # Métricas principais com cards customizados
            col1, col2, col3, col4 = st.columns(4)
            
            total_solicitacoes = len(data["solicitacoes"])
            pendentes = len([s for s in data["solicitacoes"] if s["status"] not in ["Aprovado", "Reprovado", "Finalizado"]])
            aprovadas = len([s for s in data["solicitacoes"] if s["status"] == "Aprovado"])
            em_atraso = len([s for s in data["solicitacoes"] if calcular_dias_uteis_decorridos(s["data_criacao"]) > obter_sla_por_prioridade(s["prioridade"]) and s["status"] not in ["Aprovado", "Reprovado", "Finalizado"]])
            
            with col1:
                st.markdown(f"""
                <div class="stats-card">
                    <p class="metric-value">{total_solicitacoes}</p>
                    <p class="metric-label">📋 Total de Solicitações</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stats-card">
                    <p class="metric-value">{pendentes}</p>
                    <p class="metric-label">⏳ Pendentes</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="stats-card">
                    <p class="metric-value">{aprovadas}</p>
                    <p class="metric-label">✅ Aprovadas</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="stats-card">
                    <p class="metric-value">{em_atraso}</p>
                    <p class="metric-label">🚨 Em Atraso</p>
                </div>
                """, unsafe_allow_html=True)
        
            # Métricas secundárias
            st.markdown('<h3 style="color: var(--ziran-gray); margin-top: 2rem; margin-bottom: 1rem;">📈 Métricas Detalhadas</h3>', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            finalizadas = len([s for s in data["solicitacoes"] if s["status"] == "Pedido Finalizado"])
            em_andamento = total_solicitacoes - finalizadas
            
            # Calcula SLA
            slas_cumpridos = len([s for s in data["solicitacoes"] if s.get("sla_cumprido") == "Sim"])
            slas_nao_cumpridos = len([s for s in data["solicitacoes"] if s.get("sla_cumprido") == "Não"])
            
            with col1:
                st.markdown(f"""
                <div class="stats-card">
                    <p class="metric-value">{finalizadas}</p>
                    <p class="metric-label">🏁 Finalizadas</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="stats-card">
                    <p class="metric-value">{em_andamento}</p>
                    <p class="metric-label">⚡ Em Andamento</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="stats-card">
                    <p class="metric-value">{slas_cumpridos}</p>
                    <p class="metric-label">✅ SLA Cumprido</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                if finalizadas > 0:
                    taxa_sla = (slas_cumpridos / finalizadas) * 100
                    taxa_display = f"{taxa_sla:.1f}%"
                else:
                    taxa_display = "N/A"
                st.markdown(f"""
                <div class="stats-card">
                    <p class="metric-value">{taxa_display}</p>
                    <p class="metric-label">📊 Taxa SLA</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Distribuição por etapa
        st.subheader("🔄 Distribuição por Etapa")
        etapas_count = {}
        for etapa in ETAPAS_PROCESSO:
            etapas_count[etapa] = len([s for s in data["solicitacoes"] if s["status"] == etapa])
        
        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]
        
        for i, (etapa, count) in enumerate(etapas_count.items()):
            with cols[i]:
                st.metric(etapa, count)
        
        # Análise por departamento
        st.subheader("🏢 Performance por Departamento")
        
        dept_stats = {}
        for sol in data["solicitacoes"]:
            dept = sol["departamento"]
            if dept not in dept_stats:
                dept_stats[dept] = {
                    "total": 0,
                    "finalizadas": 0,
                    "sla_cumprido": 0,
                    "sla_nao_cumprido": 0,
                    "dias_medio": []
                }
            
            dept_stats[dept]["total"] += 1
            
            if sol["status"] == "Pedido Finalizado":
                dept_stats[dept]["finalizadas"] += 1
                
                if sol.get("sla_cumprido") == "Sim":
                    dept_stats[dept]["sla_cumprido"] += 1
                elif sol.get("sla_cumprido") == "Não":
                    dept_stats[dept]["sla_nao_cumprido"] += 1
                
                if sol.get("dias_atendimento") is not None:
                    dept_stats[dept]["dias_medio"].append(sol["dias_atendimento"])
        
        if dept_stats:
            dept_df = []
            for dept, stats in dept_stats.items():
                taxa_finalizacao = (stats["finalizadas"] / stats["total"]) * 100 if stats["total"] > 0 else 0
                taxa_sla = (stats["sla_cumprido"] / stats["finalizadas"]) * 100 if stats["finalizadas"] > 0 else 0
                dias_medio = sum(stats["dias_medio"]) / len(stats["dias_medio"]) if stats["dias_medio"] else 0
                
                dept_df.append({
                    "Departamento": dept,
                    "Total": stats["total"],
                    "Finalizadas": stats["finalizadas"],
                    "Taxa Finalização": f"{taxa_finalizacao:.1f}%",
                    "SLA Cumprido": stats["sla_cumprido"],
                    "Taxa SLA": f"{taxa_sla:.1f}%",
                    "Dias Médio": f"{dias_medio:.1f}"
                })
            
            df_dept = pd.DataFrame(dept_df)
            st.dataframe(df_dept, use_container_width=True)
        
        # Análise por prioridade
        st.subheader("⚡ Performance por Prioridade")
        
        prio_stats = {}
        for sol in data["solicitacoes"]:
            prio = sol["prioridade"]
            if prio not in prio_stats:
                prio_stats[prio] = {
                    "total": 0,
                    "finalizadas": 0,
                    "sla_cumprido": 0,
                    "dias_medio": []
                }
            
            prio_stats[prio]["total"] += 1
            
            if sol["status"] == "Pedido Finalizado":
                prio_stats[prio]["finalizadas"] += 1
                
                if sol.get("sla_cumprido") == "Sim":
                    prio_stats[prio]["sla_cumprido"] += 1
                
                if sol.get("dias_atendimento") is not None:
                    prio_stats[prio]["dias_medio"].append(sol["dias_atendimento"])
        
        if prio_stats:
            prio_df = []
            for prio, stats in prio_stats.items():
                taxa_sla = (stats["sla_cumprido"] / stats["finalizadas"]) * 100 if stats["finalizadas"] > 0 else 0
                dias_medio = sum(stats["dias_medio"]) / len(stats["dias_medio"]) if stats["dias_medio"] else 0
                sla_definido = SLA_PADRAO.get(prio, 3)
                
                prio_df.append({
                    "Prioridade": prio,
                    "SLA Definido": f"{sla_definido} dias",
                    "Total": stats["total"],
                    "Finalizadas": stats["finalizadas"],
                    "SLA Cumprido": stats["sla_cumprido"],
                    "Taxa SLA": f"{taxa_sla:.1f}%",
                    "Dias Médio": f"{dias_medio:.1f}"
                })
            
            df_prio = pd.DataFrame(prio_df)
            st.dataframe(df_prio, use_container_width=True)
        
        # Solicitações com SLA em risco
        st.subheader("⚠️ Solicitações com SLA em Risco")
        
        solicitacoes_risco = []
        for sol in data["solicitacoes"]:
            if sol["status"] != "Pedido Finalizado":
                data_criacao = datetime.datetime.fromisoformat(sol["carimbo_data_hora"])
                dias_decorridos = calcular_dias_uteis(data_criacao)
                
                if dias_decorridos >= sol["sla_dias"]:
                    solicitacoes_risco.append({
                        "Número": f"#{sol['numero_solicitacao_estoque']}",
                        "Solicitante": sol["solicitante"],
                        "Departamento": sol["departamento"],
                        "Prioridade": sol["prioridade"],
                        "Status": sol["status"],
                        "SLA (dias)": sol["sla_dias"],
                        "Dias Decorridos": dias_decorridos,
                        "Atraso": dias_decorridos - sol["sla_dias"]
                    })
        
        if solicitacoes_risco:
            df_risco = pd.DataFrame(solicitacoes_risco)
            st.dataframe(df_risco, use_container_width=True)
        else:
            st.success("✅ Nenhuma solicitação com SLA em risco!")
    
    elif opcao == "📚 Histórico por Etapa":
        st.markdown('<div class="section-header">📚 Histórico por Etapa</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">📋 <strong>Visualização baseada nas abas da planilha Excel</strong></div>', unsafe_allow_html=True)
        
        if not data["solicitacoes"]:
            st.warning("📋 Não há dados para exibir.")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            etapa_filtro = st.selectbox(
                "Filtrar por Etapa:",
                ["Todas"] + ETAPAS_PROCESSO
            )
        
        with col2:
            departamento_filtro = st.selectbox(
                "Filtrar por Departamento:",
                ["Todos"] + DEPARTAMENTOS
            )
        
        with col3:
            prioridade_filtro = st.selectbox(
                "Filtrar por Prioridade:",
                ["Todas"] + PRIORIDADES
            )
        
        # Aplica filtros
        solicitacoes_filtradas = data["solicitacoes"]
        
        if etapa_filtro != "Todas":
            solicitacoes_filtradas = [s for s in solicitacoes_filtradas if s["status"] == etapa_filtro]
        
        if departamento_filtro != "Todos":
            solicitacoes_filtradas = [s for s in solicitacoes_filtradas if s["departamento"] == departamento_filtro]
        
        if prioridade_filtro != "Todas":
            solicitacoes_filtradas = [s for s in solicitacoes_filtradas if s["prioridade"] == prioridade_filtro]
        
        # Cria DataFrame para exibição
        if solicitacoes_filtradas:
            historico_df = []
            for sol in solicitacoes_filtradas:
                data_criacao = datetime.datetime.fromisoformat(sol["carimbo_data_hora"]).strftime('%d/%m/%Y %H:%M')
                
                historico_df.append({
                    "Nº Solicitação": f"#{sol['numero_solicitacao_estoque']}",
                    "Data/Hora": data_criacao,
                    "Solicitante": sol["solicitante"],
                    "Departamento": sol["departamento"],
                    "Prioridade": sol["prioridade"],
                    "Descrição": sol["descricao"][:50] + "..." if len(sol["descricao"]) > 50 else sol["descricao"],
                    "Status": sol["status"],
                    "SLA (dias)": sol["sla_dias"],
                    "Dias Atendimento": sol.get("dias_atendimento", "N/A"),
                    "SLA Cumprido": sol.get("sla_cumprido", "N/A"),
                    "Nº Pedido": sol.get("numero_pedido_compras", "N/A"),
                    "Data Entrega": datetime.datetime.fromisoformat(sol["data_entrega"]).strftime('%d/%m/%Y') if sol.get("data_entrega") else "N/A"
                })
            
            df_historico = pd.DataFrame(historico_df)
            st.dataframe(df_historico, use_container_width=True)
            
            # Botão para download
            csv = df_historico.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"historico_compras_sla_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("📋 Nenhuma solicitação encontrada com os filtros aplicados.")
    
    elif opcao == "⚙️ Configurações SLA":
        st.markdown('<div class="section-header">⚙️ Configurações SLA</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">🔧 <strong>Personalize os SLAs por prioridade e departamento</strong></div>', unsafe_allow_html=True)
        
        st.subheader("📋 SLA Atual por Prioridade")
        
        # Mostra SLA atual
        sla_df = []
        for prio, dias in SLA_PADRAO.items():
            sla_df.append({
                "Prioridade": prio,
                "SLA (dias úteis)": dias
            })
        
        df_sla = pd.DataFrame(sla_df)
        st.dataframe(df_sla, use_container_width=True)
        
        st.info("💡 Os SLAs são aplicados automaticamente baseados na prioridade da solicitação.")
        st.info("📊 Use o Dashboard SLA para monitorar a performance e ajustar os SLAs conforme necessário.")
    
    elif opcao == "👥 Gerenciar Usuários":
        if perfil_atual != "Admin":
            st.error("Acesso restrito ao Admin.")
            return
        st.markdown('<div class="section-header">👥 Gerenciar Usuários</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-box">Crie usuários, defina perfis e redefina senhas.</div>', unsafe_allow_html=True)
        with st.form("novo_usuario_form"):
            col1, col2 = st.columns(2)
            with col1:
                novo_username = st.text_input("Usuário*")
                novo_nome = st.text_input("Nome")
                novo_perfil = st.selectbox("Perfil*", ["Solicitante", "Suprimentos", "Gerência&Diretoria", "Admin"])
            with col2:
                novo_depart = st.selectbox("Departamento", DEPARTAMENTOS + ["Outro"])
                nova_senha = st.text_input("Senha*", type="password")
                nova_senha2 = st.text_input("Confirmar Senha*", type="password")
            criar = st.form_submit_button("➕ Criar Usuário")
        if criar:
            if not nova_senha or nova_senha != nova_senha2:
                st.error("Senhas não conferem.")
            else:
                erro = add_user(data, novo_username.strip(), novo_nome.strip(), novo_perfil, novo_depart, nova_senha)
                if erro:
                    st.error(erro)
                else:
                    save_data(data)
                    st.success(f"Usuário '{novo_username}' criado com sucesso.")
        
        st.markdown("---")
        st.subheader("Usuários Atuais")
        usuarios_df = pd.DataFrame([
            {"Usuário": u.get("username"), "Nome": u.get("nome"), "Perfil": u.get("perfil"), "Departamento": u.get("departamento")}
            for u in data.get("usuarios", [])
        ])
        if not usuarios_df.empty:
            st.dataframe(usuarios_df, use_container_width=True)
        else:
            st.info("Nenhum usuário cadastrado além do admin.")
        
        st.markdown("---")
        st.subheader("Redefinir Senha")
        with st.form("reset_senha_form"):
            r_user = st.selectbox("Usuário", [u.get("username") for u in data.get("usuarios", [])])
            r_senha = st.text_input("Nova senha", type="password")
            r_senha2 = st.text_input("Confirmar nova senha", type="password")
            bt_reset = st.form_submit_button("🔒 Redefinir")
        if bt_reset:
            if not r_senha or r_senha != r_senha2:
                st.error("Senhas não conferem.")
            else:
                erro = reset_user_password(data, r_user, r_senha)
                if erro:
                    st.error(erro)
                else:
                    save_data(data)
                    st.success(f"Senha de '{r_user}' redefinida com sucesso.")
    
    else:
        st.error("❌ Opção não implementada ainda.")

if __name__ == "__main__":
    main()
