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
# Detecta ambiente cloud
IS_CLOUD = os.path.exists('/mount/src') or 'STREAMLIT_CLOUD' in os.environ

# Decide uso de banco: utilizar DB no cloud se houver credenciais
def _has_cloud_db_credentials() -> bool:
    try:
        has_secrets = hasattr(st, 'secrets') and (
            ("postgres" in st.secrets) or
            ("database" in st.secrets) or
            ("postgres_url" in st.secrets) or
            ("database_url" in st.secrets)
        )
        return has_secrets or bool(os.getenv("DATABASE_URL"))
    except Exception:
        return False

USE_DATABASE = False
try:
    if (IS_CLOUD and _has_cloud_db_credentials()) or (not IS_CLOUD):
        from database import get_database
        from session_manager import get_session_manager
        USE_DATABASE = True
except Exception:
    USE_DATABASE = False

if not USE_DATABASE:
    # Fallback para autenticação simples em memória
    from simple_session import simple_login, ensure_session_persistence, simple_logout

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

# Unidades e catálogo de produtos padrão
UNIDADES_PADRAO = [
    "UN", "PC", "CX", "KG", "L", "M", "M2"
]

def get_default_product_catalog() -> List[Dict]:
    """Retorna um catálogo inicial editável de produtos."""
    return [
        {"codigo": "PRD-001", "nome": "Cabo de Rede Cat6", "categoria": "TI", "unidade": "UN", "ativo": True},
        {"codigo": "PRD-002", "nome": "Notebook 14\"", "categoria": "TI", "unidade": "UN", "ativo": True},
        {"codigo": "PRD-003", "nome": "Tinta Látex Branca", "categoria": "Manutenção", "unidade": "L", "ativo": True},
        {"codigo": "PRD-004", "nome": "Parafuso 5mm", "categoria": "Manutenção", "unidade": "CX", "ativo": True},
        {"codigo": "PRD-005", "nome": "Papel A4 75g", "categoria": "Escritório", "unidade": "CX", "ativo": True},
    ]

def render_data_editor(df: pd.DataFrame, key: str = None, **kwargs) -> pd.DataFrame:
    """Tenta usar st.data_editor; faz fallback para experimental_data_editor; por fim, mostra dataframe somente leitura."""
    try:
        return st.data_editor(df, key=key, **kwargs)
    except Exception:
        try:
            return st.experimental_data_editor(df, key=key, **kwargs)  # type: ignore[attr-defined]
        except Exception:
            st.dataframe(df, use_container_width=True)
            return df

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
            "upload_dir": UPLOAD_ROOT_DEFAULT,
            "suprimentos_min_cotacoes": 1,
            "suprimentos_anexo_obrigatorio": True,
            "catalogo_produtos": get_default_product_catalog()
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
    cfg.setdefault("suprimentos_min_cotacoes", 1)
    cfg.setdefault("suprimentos_anexo_obrigatorio", True)
    cfg.setdefault("catalogo_produtos", get_default_product_catalog())
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
        s.setdefault("itens", [])
        s.setdefault("local_aplicacao", None)
        s.setdefault("numero_requisicao_interno", None)
        s.setdefault("data_requisicao_interna", None)
        s.setdefault("responsavel_suprimentos", None)
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
    if USE_DATABASE:
        db = get_database()
        ok = db.update_user_password(username, nova_senha)
        return "" if ok else "Usuário não encontrado."
    user = find_user(data, username)
    if not user:
        return "Usuário não encontrado."
    user["senha_hash"] = hash_password(nova_senha)
    return ""

def migrate_users_to_db_from_json(data: Dict):
    """Migra usuários existentes no JSON para o banco (uma vez)."""
    try:
        db = get_database()
        if not getattr(db, "db_available", False):
            return
        existentes = {u.get("username") for u in db.get_all_users()}
        for u in data.get("usuarios", []):
            username = u.get("username")
            if username and username not in existentes:
                db.add_user(
                    username,
                    u.get("nome", username),
                    u.get("perfil", "Solicitante"),
                    u.get("departamento", "Outro"),
                    u.get("senha_hash", ""),
                    is_hashed=True
                )
    except Exception:
        # Falha silenciosa para não bloquear o app
        pass

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

def format_brl(valor) -> str:
    """Formata número para moeda BRL (pt-BR) ex.: R$ 1.234,56"""
    if valor is None:
        return "N/A"
    try:
        s = f"{float(valor):,.2f}"
        s = s.replace(",", "_").replace(".", ",").replace("_", ".")
        return f"R$ {s}"
    except Exception:
        return "N/A"

def main():
    # CSS personalizado com cores da marca Ziran
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
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
    st.sidebar.markdown(get_sidebar_css(), unsafe_allow_html=True)
    
    # Garante que existe um usuário admin
    if USE_DATABASE:
        db = get_database()
        # Cria admin se não existir
        admin_exists = db.authenticate_user("admin", "admin123")
        if not admin_exists:
            db.add_user("admin", "Administrador", "Admin", "TI", "admin123")
        # Migra usuários do JSON para o banco (se houver)
        migrate_users_to_db_from_json(data)
    else:
        changed = ensure_admin_user(data)
        if changed:
            save_data(data)
    
    if "usuario" not in st.session_state:
        st.sidebar.markdown("### 🔐 Login")
        with st.sidebar.form("login_form"):
            login_user = st.text_input("Usuário", key="login_username")
            login_pass = st.text_input("Senha", type="password", key="login_password")
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
                "📑 Requisição (Estoque)",
                "🔄 Mover para Próxima Etapa",
                "📱 Aprovações",
                "📊 Dashboard SLA",
                "📚 Histórico por Etapa",
                "📦 Catálogo de Produtos",
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
                "📑 Requisição (Estoque)",
                "🔄 Mover para Próxima Etapa",
                "📊 Dashboard SLA",
                "📚 Histórico por Etapa",
                "📦 Catálogo de Produtos"
            ]
        # Solicitante
        return [
            "📝 Nova Solicitação",
            "📊 Dashboard SLA",
            "📚 Histórico por Etapa"
        ]
    opcoes = opcoes_por_perfil(perfil_atual)
    opcao = st.sidebar.selectbox("Escolha uma opção:", opcoes, key="menu_option")
    
    # Estatísticas rápidas com design melhorado
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Estatísticas Rápidas")
    
    total_solicitacoes = len(data["solicitacoes"])
    solicitacoes_pendentes = len([s for s in data["solicitacoes"] if s["status"] != "Pedido Finalizado"])
    
    # Cards de métricas na sidebar
    st.sidebar.markdown(get_stats_card_html(str(total_solicitacoes), "Total de Solicitações"), unsafe_allow_html=True)
    st.sidebar.markdown(get_stats_card_html(str(solicitacoes_pendentes), "Pendentes"), unsafe_allow_html=True)
    
    # Adicionar mais uma métrica útil
    finalizadas = len([s for s in data["solicitacoes"] if s["status"] == "Pedido Finalizado"])
    st.sidebar.markdown(get_stats_card_html(str(finalizadas), "Finalizadas"), unsafe_allow_html=True)
    
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
        st.markdown(get_section_header_html('📝 Nova Solicitação de Compra'), unsafe_allow_html=True)
        st.markdown(get_info_box_html('💡 <strong>Baseado na estrutura da planilha Excel - Aba \'Solicitação\'</strong>'), unsafe_allow_html=True)
        
        st.markdown(get_form_container_start(), unsafe_allow_html=True)
        
        with st.form("nova_solicitacao"):
            # Seção 1: Dados do Solicitante
            st.markdown(get_form_section_start(), unsafe_allow_html=True)
            st.markdown(get_form_section_title('👤 Dados do Solicitante'), unsafe_allow_html=True)
            
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
            
            st.markdown(get_form_section_end(), unsafe_allow_html=True)
            
            # Seção 2: Dados da Solicitação
            st.markdown(get_form_section_start(), unsafe_allow_html=True)
            st.markdown(get_form_section_title('📋 Dados da Solicitação'), unsafe_allow_html=True)
            
            col3 = st.columns(1)[0]
            with col3:
                descricao = st.text_area(
                    "Descrição*", 
                    height=120,
                    help="Descrição detalhada da solicitação",
                    placeholder="Descreva detalhadamente o que está sendo solicitado..."
                )
            # Campo Local de Aplicação
            local_aplicacao = st.text_input(
                "Local de Aplicação*",
                help="Onde o material será aplicado (ex: Linha 3, Sala 201, Equipamento X)"
            )

            # Itens da Solicitação (lista padronizada)
            st.markdown(get_form_section_start(), unsafe_allow_html=True)
            st.markdown(get_form_section_title('🧾 Itens da Solicitação'), unsafe_allow_html=True)
            catalogo = data.get("configuracoes", {}).get("catalogo_produtos", [])
            if not catalogo:
                st.warning("Catálogo de produtos vazio. Configure em '📦 Catálogo de Produtos'.")
                itens_editados = pd.DataFrame([{"codigo": "", "quantidade": 1}])
            else:
                # DataFrame inicial
                itens_df_init = pd.DataFrame([{"codigo": "", "quantidade": 1}])
                try:
                    # Tenta configurar colunas com selectbox/number quando disponível
                    if hasattr(st, "column_config"):
                        col_cfg = {
                            "codigo": st.column_config.SelectboxColumn(
                                "Código do Produto",
                                options=[c.get("codigo") for c in catalogo if c.get("ativo", True)],
                                help="Selecione um código válido do catálogo"
                            ),
                            "quantidade": st.column_config.NumberColumn(
                                "Quantidade",
                                min_value=1,
                                step=1,
                                help="Informe a quantidade desejada"
                            )
                        }
                        itens_editados = render_data_editor(
                            itens_df_init,
                            key="itens_editor",
                            use_container_width=True,
                            num_rows="dynamic",
                            column_config=col_cfg,
                            hide_index=True
                        )
                    else:
                        itens_editados = render_data_editor(
                            itens_df_init,
                            key="itens_editor",
                            use_container_width=True,
                            num_rows="dynamic"
                        )
                except Exception:
                    itens_editados = render_data_editor(
                        itens_df_init,
                        key="itens_editor",
                        use_container_width=True,
                        num_rows="dynamic"
                    )
                st.info("Adicione linhas e selecione o código do produto e a quantidade. Linhas vazias serão ignoradas.")
            st.markdown(get_form_section_end(), unsafe_allow_html=True)

            st.markdown(get_form_section_end(), unsafe_allow_html=True)
            
            # Seção 3: Anexos
            st.markdown(get_form_section_start(), unsafe_allow_html=True)
            st.markdown(get_form_section_title('📎 Anexos da Solicitação'), unsafe_allow_html=True)
            
            anexos_files = st.file_uploader(
                "Faça upload dos arquivos relacionados à solicitação (opcional)",
                type=ALLOWED_FILE_TYPES,
                accept_multiple_files=True,
                help="Tipos permitidos: PDF, PNG, JPG, JPEG, DOC, DOCX, XLS, XLSX"
            )
            
            if anexos_files:
                st.success(f"✅ {len(anexos_files)} arquivo(s) selecionado(s)")
            
            st.markdown(get_form_section_end(), unsafe_allow_html=True)
            
            # Seção 4: Informações Automáticas
            st.markdown(get_form_section_start(), unsafe_allow_html=True)
            st.markdown(get_form_section_title('⚙️ Informações de Controle'), unsafe_allow_html=True)
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
            
            st.markdown(get_form_section_end(), unsafe_allow_html=True)
            
            # Botão de submissão
            st.markdown('<br>', unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "🚀 Criar Solicitação", 
                use_container_width=True
            )
        
        st.markdown(get_form_container_end(), unsafe_allow_html=True)
        
        if submitted:
            # Prepara itens estruturados
            itens_struct = []
            try:
                catalog_map = {c.get("codigo"): c for c in data.get("configuracoes", {}).get("catalogo_produtos", [])}
                if 'itens_editados' in locals() and isinstance(itens_editados, pd.DataFrame):
                    for r in itens_editados.to_dict(orient="records"):
                        cod = (r.get("codigo") or "").strip()
                        if not cod:
                            continue
                        prod = catalog_map.get(cod)
                        qtd = r.get("quantidade")
                        try:
                            qtd_val = int(qtd) if float(qtd) == int(qtd) else float(qtd)
                        except Exception:
                            qtd_val = None
                        if prod and qtd_val and qtd_val > 0:
                            itens_struct.append({
                                "codigo": cod,
                                "nome": prod.get("nome"),
                                "unidade": prod.get("unidade"),
                                "quantidade": qtd_val
                            })
            except Exception:
                itens_struct = []

            if solicitante and departamento and descricao and local_aplicacao and len(itens_struct) > 0:
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
                    "local_aplicacao": local_aplicacao,
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
                success_content = f'<h3 style="color: #065f46; margin: 0 0 1rem 0; font-family: Poppins;">🎉 Solicitação #{numero_solicitacao} Criada com Sucesso!</h3>'
                st.markdown(get_info_box_html(success_content, "success"), unsafe_allow_html=True)
                
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.markdown(f"**📅 Data/Hora:** {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
                    st.markdown(f"**⏱️ SLA:** {sla_dias} dias úteis")
                with col_info2:
                    st.markdown(f"**📊 Status:** Solicitação (Etapa 1 de 7)")
                    st.markdown(f"**📎 Anexos:** {len(anexos_meta)} arquivo(s)")
                st.markdown(f"**🧾 Itens:** {len(itens_struct)} item(ns)")
                
                
                # Próximos passos com design melhorado
                proximos_passos = '<h4 style="color: #1e40af; margin: 0 0 1rem 0; font-family: Poppins;">🔄 Próximos Passos</h4>**1.** A solicitação será analisada pela área de **Suprimentos**<br>**2.** Use a opção **\'🔄 Mover para Próxima Etapa\'** para avançar o processo<br>**3.** Acompanhe o progresso no **Dashboard SLA** ou **Histórico por Etapa**'
                st.markdown(get_info_box_html(proximos_passos), unsafe_allow_html=True)
                
            else:
                warning_content = '<h4 style="color: #92400e; margin: 0 0 0.5rem 0;">⚠️ Campos Obrigatórios</h4>Por favor, preencha todos os campos marcados com **asterisco (*)** e adicione ao menos 1 item válido antes de continuar.'
                st.markdown(get_info_box_html(warning_content, "warning"), unsafe_allow_html=True)
    
    elif opcao == "🔄 Mover para Próxima Etapa":
        st.markdown(get_section_header_html('🔄 Mover Solicitação para Próxima Etapa'), unsafe_allow_html=True)
        st.markdown(get_info_box_html('⚡ <strong>Controle do fluxo do processo de compras</strong>'), unsafe_allow_html=True)
        
        # Filtra solicitações que não estão finalizadas
        solicitacoes_ativas = [s for s in data["solicitacoes"] if s["status"] != "Pedido Finalizado"]
        
        if not solicitacoes_ativas:
            st.warning("📋 Não há solicitações ativas para mover.")
            st.info("💡 Crie uma nova solicitação primeiro!")
            return
        
        # 0) Pendências de Suprimentos (tabela com filtros e ordenação por urgência/SLA)
        usar_pendencias = False
        pendentes_opcoes = []
        if perfil_atual in ["Suprimentos", "Admin"]:
            st.subheader("0️⃣ Pendências de Suprimentos")
            pend_supr = [s for s in data.get("solicitacoes", []) if s.get("status") == "Suprimentos"]
            
            # Resumo de prioridades para o setor de suprimentos
            if pend_supr:
                urgentes = len([s for s in pend_supr if s.get("prioridade") == "Urgente"])
                altas = len([s for s in pend_supr if s.get("prioridade") == "Alta"])
                normais = len([s for s in pend_supr if s.get("prioridade") == "Normal"])
                baixas = len([s for s in pend_supr if s.get("prioridade") == "Baixa"])
                
                # Conta atrasados
                atrasados = 0
                vence_hoje = 0
                for s in pend_supr:
                    try:
                        data_cr = datetime.datetime.fromisoformat(s.get("carimbo_data_hora"))
                        dias_dec = calcular_dias_uteis(data_cr)
                        sla = s.get("sla_dias", 0) or 0
                        dias_rest = sla - dias_dec
                        if dias_rest < 0:
                            atrasados += 1
                        elif dias_rest == 0:
                            vence_hoje += 1
                    except:
                        continue
                
                st.markdown("### 📊 Resumo de Prioridades")
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                with col1:
                    if urgentes > 0:
                        st.metric("🔴 Urgentes", urgentes, delta=None, delta_color="inverse")
                    else:
                        st.metric("🔴 Urgentes", urgentes)
                
                with col2:
                    if altas > 0:
                        st.metric("🟠 Altas", altas, delta=None, delta_color="normal")
                    else:
                        st.metric("🟠 Altas", altas)
                
                with col3:
                    st.metric("🟡 Normais", normais)
                
                with col4:
                    st.metric("🟢 Baixas", baixas)
                
                with col5:
                    if atrasados > 0:
                        st.metric("❌ Atrasados", atrasados, delta=None, delta_color="inverse")
                    else:
                        st.metric("❌ Atrasados", atrasados)
                
                with col6:
                    if vence_hoje > 0:
                        st.metric("⚠️ Vence Hoje", vence_hoje, delta=None, delta_color="normal")
                    else:
                        st.metric("⚠️ Vence Hoje", vence_hoje)
                
                if urgentes > 0 or atrasados > 0:
                    st.error("🚨 **ATENÇÃO:** Há solicitações URGENTES ou ATRASADAS que precisam de ação imediata!")
                elif vence_hoje > 0:
                    st.warning("⚠️ **AVISO:** Há solicitações que vencem HOJE!")
                
                st.markdown("---")
            if pend_supr:
                c1, c2, c3, c4 = st.columns([1,1,1,1])
                with c1:
                    dep_f = st.selectbox("Departamento", ["Todos"] + sorted(list({s.get("departamento") for s in pend_supr})))
                with c2:
                    prio_f = st.selectbox("Prioridade", ["Todas"] + PRIORIDADES)
                with c3:
                    so_atraso = st.checkbox("Somente em atraso", value=False)
                with c4:
                    usar_pendencias = st.checkbox("Usar lista na seleção abaixo", value=True)

                rows = []
                prio_rank_map = {"Urgente": 3, "Alta": 2, "Normal": 1, "Baixa": 0}
                for s in pend_supr:
                    try:
                        data_cr = datetime.datetime.fromisoformat(s.get("carimbo_data_hora"))
                    except Exception:
                        continue
                    dias_dec = calcular_dias_uteis(data_cr)
                    sla = s.get("sla_dias", 0) or 0
                    dias_rest = sla - dias_dec
                    if dep_f != "Todos" and s.get("departamento") != dep_f:
                        continue
                    if prio_f != "Todas" and s.get("prioridade") != prio_f:
                        continue
                    if so_atraso and dias_rest >= 0:
                        continue
                    # Adiciona emoji e cor baseado na prioridade
                    prio = s.get("prioridade", "Normal")
                    if prio == "Urgente":
                        prio_display = "🔴 URGENTE"
                    elif prio == "Alta":
                        prio_display = "🟠 ALTA"
                    elif prio == "Normal":
                        prio_display = "🟡 NORMAL"
                    else:  # Baixa
                        prio_display = "🟢 BAIXA"
                    
                    # Status visual para dias restantes
                    if dias_rest < 0:
                        status_sla = f"❌ ATRASADO ({abs(dias_rest)}d)"
                    elif dias_rest == 0:
                        status_sla = "⚠️ VENCE HOJE"
                    elif dias_rest == 1:
                        status_sla = "🟡 VENCE AMANHÃ"
                    else:
                        status_sla = f"✅ {dias_rest}d restantes"
                    
                    rows.append({
                        "Número": s.get("numero_solicitacao_estoque"),
                        "Solicitante": s.get("solicitante"),
                        "Departamento": s.get("departamento"),
                        "🚨 Prioridade": prio_display,
                        "SLA (dias)": sla,
                        "Dias Decorridos": dias_dec,
                        "⏰ Status SLA": status_sla,
                        "Responsável": s.get("responsavel_suprimentos") or "-",
                        "Data/Hora": data_cr.strftime('%d/%m/%Y %H:%M'),
                        "_rank": (dias_rest, -prio_rank_map.get(s.get("prioridade"), 1))
                    })

                if rows:
                    # ordena: menor dias restantes primeiro (atrasados primeiro), depois prioridade mais alta
                    rows_sorted = sorted(rows, key=lambda r: r["_rank"])
                    df_pend = pd.DataFrame([{k: v for k, v in r.items() if k != "_rank"} for r in rows_sorted])
                    
                    # Destaca linhas críticas com cores
                    def highlight_priority(row):
                        if "🔴 URGENTE" in str(row["🚨 Prioridade"]):
                            return ['background-color: #fee2e2; font-weight: bold'] * len(row)
                        elif "🟠 ALTA" in str(row["🚨 Prioridade"]):
                            return ['background-color: #fed7aa; font-weight: bold'] * len(row)
                        elif "❌ ATRASADO" in str(row["⏰ Status SLA"]):
                            return ['background-color: #fecaca'] * len(row)
                        elif "⚠️ VENCE HOJE" in str(row["⏰ Status SLA"]):
                            return ['background-color: #fef3c7'] * len(row)
                        return [''] * len(row)
                    
                    try:
                        styled_df = df_pend.style.apply(highlight_priority, axis=1)
                        st.dataframe(styled_df, use_container_width=True)
                    except:
                        # Fallback se styling não funcionar
                        st.dataframe(df_pend, use_container_width=True)

                    pendentes_opcoes = [
                        f"#{r['Número']} - {r['🚨 Prioridade']} - {r['Solicitante']} - {r['⏰ Status SLA']} ({r['Data/Hora']})" for r in rows_sorted
                    ]
                else:
                    st.info("Nenhuma pendência encontrada com os filtros aplicados.")
            else:
                st.success("✅ Não há solicitações na etapa de Suprimentos.")

        # Seleção da solicitação
        st.subheader("1️⃣ Selecione a Solicitação")
        
        opcoes_solicitacoes = []
        if usar_pendencias and pendentes_opcoes:
            opcoes_solicitacoes = pendentes_opcoes
        else:
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
                            responsavel = st.text_input("Responsável Suprimentos*", value=solicitacao.get("responsavel_suprimentos") or nome_atual)
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
                            resp_supr = st.text_input("Responsável Suprimentos*", value=solicitacao.get("responsavel_suprimentos") or nome_atual)
                            observacoes = st.text_area("Observações", height=100)
                    
                    elif proxima_etapa == "Aguardando Aprovação":
                        cfg_rules = data.get("configuracoes", {})
                        min_cot_cfg = int(cfg_rules.get("suprimentos_min_cotacoes", 1))
                        anexo_obrig_cfg = bool(cfg_rules.get("suprimentos_anexo_obrigatorio", True))
                        st.markdown(f"**🧾 Registrar Cotações (mín. {min_cot_cfg}, ideal 3)**")
                        if anexo_obrig_cfg:
                            st.info("Cadastre as cotações recebidas para seguir para aprovação. Anexos são obrigatórios em pelo menos 1 cotação.")
                        else:
                            st.info("Cadastre as cotações recebidas para seguir para aprovação. Anexos são opcionais.")
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
                        # Valida campos obrigatórios por etapa
                        if proxima_etapa == "Suprimentos" and not ("responsavel" in locals() and responsavel):
                            st.warning("Preencha o campo 'Responsável Suprimentos*'.")
                            st.stop()
                        if proxima_etapa == "Em Cotação" and not ("resp_supr" in locals() and resp_supr):
                            st.warning("Informe o 'Responsável Suprimentos*' para a etapa de cotação.")
                            st.stop()
                        
                        # Validação: usar regras configuráveis (mínimo de cotações e anexos)
                        if proxima_etapa == "Aguardando Aprovação":
                            cfg_rules = data.get("configuracoes", {})
                            min_cot_cfg = int(cfg_rules.get("suprimentos_min_cotacoes", 1))
                            anexo_obrig_cfg = bool(cfg_rules.get("suprimentos_anexo_obrigatorio", True))
                            valid_quotes = 0
                            valid_quotes_with_attachment = 0
                            try:
                                for idx, (fornecedor, valor, prazo, validade, anexos, obs_c) in enumerate(cotacoes_input, start=1):
                                    if fornecedor and valor and float(valor) > 0:
                                        valid_quotes += 1
                                        if anexos and len(anexos) > 0:
                                            valid_quotes_with_attachment += 1
                            except Exception:
                                valid_quotes = 0
                                valid_quotes_with_attachment = 0
                            if valid_quotes < min_cot_cfg:
                                st.warning(f"Informe no mínimo {min_cot_cfg} cotação(ões) válidas (Fornecedor e Valor) para seguir para aprovação.")
                                st.stop()
                            if anexo_obrig_cfg and valid_quotes_with_attachment < 1:
                                st.warning("É obrigatório anexar pelo menos 1 documento em uma das cotações.")
                                st.stop()
                        
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
                                    "usuario": (responsavel if 'responsavel' in locals() and responsavel else (resp_supr if 'resp_supr' in locals() and resp_supr else nome_atual))
                                })
                                
                                # Atualiza campos específicos
                                if proxima_etapa == "Suprimentos" and 'responsavel' in locals() and responsavel:
                                    data["solicitacoes"][i]["responsavel_suprimentos"] = responsavel
                                if proxima_etapa == "Em Cotação" and 'numero_pedido' in locals():
                                    data["solicitacoes"][i]["numero_pedido_compras"] = numero_pedido
                                    data["solicitacoes"][i]["data_numero_pedido"] = data_pedido.isoformat()
                                    if 'data_cotacao' in locals():
                                        data["solicitacoes"][i]["data_cotacao"] = data_cotacao.isoformat()
                                    if 'resp_supr' in locals() and resp_supr:
                                        data["solicitacoes"][i]["responsavel_suprimentos"] = resp_supr
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
    
    elif opcao == "📑 Requisição (Estoque)":
        st.markdown(get_section_header_html('📑 Requisição (Estoque)'), unsafe_allow_html=True)
        st.markdown(get_info_box_html('🧭 <strong>Lançar número de requisição interna e encaminhar para Suprimentos</strong>'), unsafe_allow_html=True)

        if perfil_atual not in ["Suprimentos", "Admin"]:
            st.info("Esta página é restrita a Suprimentos ou Admin.")
        else:
            pend = [s for s in data.get("solicitacoes", []) if s.get("status") == "Solicitação"]
            if not pend:
                st.success("✅ Não há solicitações aguardando requisição interna.")
            else:
                opcoes = []
                for s in pend:
                    data_criacao = datetime.datetime.fromisoformat(s["carimbo_data_hora"]).strftime('%d/%m/%Y %H:%M')
                    opcoes.append(f"#{s['numero_solicitacao_estoque']} - {s['solicitante']} - {s['departamento']} ({data_criacao})")

                escolha = st.selectbox("Selecione a solicitação:", opcoes)
                if escolha:
                    numero_solicitacao = int(escolha.split('#')[1].split(' -')[0])
                    sol = next(s for s in pend if s['numero_solicitacao_estoque'] == numero_solicitacao)

                    with st.form("lançar_requisicao_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            num_req = st.text_input("Nº Requisição Interna*", value=sol.get("numero_requisicao_interno") or "")
                            data_req = st.date_input("Data Requisição*", value=date.today())
                        with col2:
                            resp = st.text_input("Responsável (Suprimentos)", value=sol.get("responsavel_suprimentos") or nome_atual)
                            obs_req = st.text_area("Observações", height=100)
                        confirmar = st.form_submit_button("Salvar e Enviar para Suprimentos", use_container_width=True)

                    if confirmar:
                        if num_req.strip():
                            for i, s in enumerate(data["solicitacoes"]):
                                if s["numero_solicitacao_estoque"] == numero_solicitacao:
                                    data["solicitacoes"][i]["numero_requisicao_interno"] = num_req.strip()
                                    data["solicitacoes"][i]["data_requisicao_interna"] = data_req.isoformat()
                                    if resp:
                                        data["solicitacoes"][i]["responsavel_suprimentos"] = resp
                                    data["solicitacoes"][i]["observacoes"] = obs_req or s.get("observacoes")
                                    # Muda etapa para Suprimentos
                                    data["solicitacoes"][i]["status"] = "Suprimentos"
                                    data["solicitacoes"][i]["etapa_atual"] = "Suprimentos"
                                    data["solicitacoes"][i]["historico_etapas"].append({
                                        "etapa": "Suprimentos",
                                        "data_entrada": datetime.datetime.now().isoformat(),
                                        "usuario": nome_atual
                                    })
                                    try:
                                        add_notification(data, "Suprimentos", numero_solicitacao, "Requisição interna lançada e disponível para tratamento.")
                                    except Exception:
                                        pass
                                    break
                            save_data(data)
                            st.success(f"✅ Solicitação #{numero_solicitacao} atualizada e movida para 'Suprimentos'.")
                            st.rerun()
                        else:
                            st.warning("Informe o número da requisição interna.")
    
    elif opcao == "📦 Catálogo de Produtos":
        st.markdown(get_section_header_html('📦 Catálogo de Produtos'), unsafe_allow_html=True)
        st.markdown(get_info_box_html('🗂️ <strong>Gerencie os produtos disponíveis para seleção nas solicitações</strong>'), unsafe_allow_html=True)

        if perfil_atual not in ["Suprimentos", "Admin"]:
            st.info("Esta página é restrita a Suprimentos ou Admin.")
        else:
            st.subheader("Lista de Produtos")
            catalogo = data.get("configuracoes", {}).get("catalogo_produtos", [])
            df_init = pd.DataFrame(catalogo) if catalogo else pd.DataFrame(columns=["codigo", "nome", "categoria", "unidade", "ativo"])
            # Garante colunas e ordem
            for col in ["codigo", "nome", "categoria", "unidade", "ativo"]:
                if col not in df_init.columns:
                    df_init[col] = True if col == "ativo" else ""
            df_init = df_init[["codigo", "nome", "categoria", "unidade", "ativo"]]

            try:
                if hasattr(st, "column_config"):
                    col_cfg = {
                        "codigo": st.column_config.TextColumn("Código*", help="Código único do produto (ex.: PRD-001)"),
                        "nome": st.column_config.TextColumn("Nome*", help="Nome do produto"),
                        "categoria": st.column_config.TextColumn("Categoria", help="Categoria/área"),
                        "unidade": st.column_config.SelectboxColumn("Unidade*", options=UNIDADES_PADRAO, help="Unidade padrão"),
                        "ativo": st.column_config.CheckboxColumn("Ativo", default=True, help="Se desmarcado, não aparece para seleção")
                    }
                    df_edit = render_data_editor(
                        df_init,
                        key="catalogo_editor",
                        use_container_width=True,
                        num_rows="dynamic",
                        column_config=col_cfg,
                        hide_index=True
                    )
                else:
                    df_edit = render_data_editor(
                        df_init,
                        key="catalogo_editor",
                        use_container_width=True,
                        num_rows="dynamic"
                    )
            except Exception:
                df_edit = render_data_editor(
                    df_init,
                    key="catalogo_editor",
                    use_container_width=True,
                    num_rows="dynamic"
                )

            st.caption("Dica: adicione linhas para novos produtos. Linhas com código ou nome vazio serão ignoradas no salvamento.")

            c1, c2 = st.columns([1, 1])
            with c1:
                salvar = st.button("💾 Salvar Catálogo", use_container_width=True)
            with c2:
                resetar = st.button("↩️ Restaurar Catálogo Padrão", use_container_width=True)

            if salvar:
                registros = []
                codigos = set()
                erros = []
                try:
                    for r in df_edit.to_dict(orient="records"):
                        cod = (r.get("codigo") or "").strip()
                        nome = (r.get("nome") or "").strip()
                        if not cod and not nome:
                            continue
                        if not cod or not nome:
                            erros.append(f"Linha com código ou nome vazio: {r}")
                            continue
                        if cod in codigos:
                            erros.append(f"Código duplicado: {cod}")
                            continue
                        codigos.add(cod)
                        cat = (r.get("categoria") or "").strip()
                        und = (r.get("unidade") or "").strip() or "UN"
                        ativo = bool(r.get("ativo", True))
                        registros.append({"codigo": cod, "nome": nome, "categoria": cat, "unidade": und, "ativo": ativo})
                except Exception:
                    erros.append("Falha ao processar os dados do catálogo.")

                if erros:
                    st.error("Não foi possível salvar devido a erros:")
                    for e in erros:
                        st.write(f"• {e}")
                else:
                    data["configuracoes"]["catalogo_produtos"] = registros
                    save_data(data)
                    st.success(f"✅ Catálogo salvo. {len(registros)} produto(s) ativo(s).")

            if resetar:
                data["configuracoes"]["catalogo_produtos"] = get_default_product_catalog()
                save_data(data)
                st.success("Catálogo restaurado para o padrão inicial.")
                st.rerun()

    elif opcao == "📱 Aprovações":
        st.markdown(get_section_header_html('📱 Aprovações'), unsafe_allow_html=True)
        st.markdown(get_info_box_html('🛡️ <strong>Somente Gerência&Diretoria ou Admin podem aprovar</strong>'), unsafe_allow_html=True)

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

                    # Campos adicionais solicitados: responsável, qtde de cotações, fornecedor/valor e local de aplicação
                    resp_sup = sol.get('responsavel_suprimentos') or 'N/A'
                    qt_cot = len(sol.get('cotacoes', []) or [])
                    fornecedor_exib = sol.get('fornecedor_final') or sol.get('fornecedor_recomendado') or 'N/A'
                    valor_exib = sol.get('valor_final') if sol.get('valor_final') is not None else sol.get('valor_estimado')
                    valor_exib_str = format_brl(valor_exib)

                    cx1, cx2, cx3, cx4 = st.columns(4)
                    with cx1:
                        st.metric("Resp. Suprimentos", resp_sup)
                    with cx2:
                        st.metric("Qtde de Cotações", qt_cot)
                    with cx3:
                        st.metric("Fornecedor", fornecedor_exib)
                    with cx4:
                        st.metric("Valor (R$)", valor_exib_str)

                    st.markdown(f"**Local de Aplicação:** {sol.get('local_aplicacao') or 'N/A'}")

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
        st.markdown(get_section_header_html('📊 Dashboard SLA'), unsafe_allow_html=True)
        st.markdown(get_info_box_html('📈 <strong>Visualização baseada nas abas da planilha Excel</strong>'), unsafe_allow_html=True)
        
        if not data["solicitacoes"]:
            warning_content = '📋 <strong>Não há dados para exibir no dashboard.</strong><br>💡 Crie algumas solicitações primeiro!'
            st.markdown(get_info_box_html(warning_content, "warning"), unsafe_allow_html=True)
        else:
            # Métricas principais com cards customizados
            col1, col2, col3, col4 = st.columns(4)
            
            total_solicitacoes = len(data["solicitacoes"])
            pendentes = len([s for s in data["solicitacoes"] if s["status"] not in ["Aprovado", "Reprovado", "Pedido Finalizado"]])
            aprovadas = len([s for s in data["solicitacoes"] if s["status"] == "Aprovado"])
            em_atraso = len([
                s for s in data["solicitacoes"]
                if s["status"] not in ["Aprovado", "Reprovado", "Pedido Finalizado"]
                and calcular_dias_uteis(s.get("carimbo_data_hora")) > (s.get("sla_dias") or obter_sla_por_prioridade(s.get("prioridade", "Normal")))
            ])
            
            with col1:
                st.markdown(get_stats_card_html(str(total_solicitacoes), "📋 Total de Solicitações"), unsafe_allow_html=True)
            
            with col2:
                st.markdown(get_stats_card_html(str(pendentes), "⏳ Pendentes"), unsafe_allow_html=True)
            
            with col3:
                st.markdown(get_stats_card_html(str(aprovadas), "✅ Aprovadas"), unsafe_allow_html=True)
            
            with col4:
                st.markdown(get_stats_card_html(str(em_atraso), "🚨 Em Atraso"), unsafe_allow_html=True)
        
            # Métricas secundárias
            st.markdown('<h3 style="color: var(--ziran-gray); margin-top: 2rem; margin-bottom: 1rem;">📈 Métricas Detalhadas</h3>', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            finalizadas = len([s for s in data["solicitacoes"] if s["status"] == "Pedido Finalizado"])
            em_andamento = total_solicitacoes - finalizadas
            
            # Calcula SLA
            slas_cumpridos = len([s for s in data["solicitacoes"] if s.get("sla_cumprido") == "Sim"])
            slas_nao_cumpridos = len([s for s in data["solicitacoes"] if s.get("sla_cumprido") == "Não"])
            
            with col1:
                st.markdown(get_stats_card_html(str(finalizadas), "🏁 Finalizadas"), unsafe_allow_html=True)
            
            with col2:
                st.markdown(get_stats_card_html(str(em_andamento), "⚡ Em Andamento"), unsafe_allow_html=True)
            
            with col3:
                st.markdown(get_stats_card_html(str(slas_cumpridos), "✅ SLA Cumprido"), unsafe_allow_html=True)
            
            with col4:
                if finalizadas > 0:
                    taxa_sla = (slas_cumpridos / finalizadas) * 100
                    taxa_display = f"{taxa_sla:.1f}%"
                else:
                    taxa_display = "N/A"
                st.markdown(get_stats_card_html(taxa_display, "📊 Taxa SLA"), unsafe_allow_html=True)
        
        # Distribuição por etapa
        st.subheader("🔄 Distribuição por Etapa")
        etapas_count = {}
        for etapa in ETAPAS_PROCESSO:
            etapas_count[etapa] = len([s for s in data["solicitacoes"] if s["status"] == etapa])
        
        # Renderiza em linhas de até 4 colunas para evitar IndexError quando houver mais de 4 etapas
        items = list(etapas_count.items())
        for start in range(0, len(items), 4):
            chunk = items[start:start+4]
            cols = st.columns(len(chunk))
            for col, (etapa, count) in zip(cols, chunk):
                with col:
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
        st.markdown(get_section_header_html('📚 Histórico por Etapa'), unsafe_allow_html=True)
        st.markdown(get_info_box_html('📋 <strong>Visualização baseada nas abas da planilha Excel</strong>'), unsafe_allow_html=True)
        
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
            
            # Botões para download
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_historico.to_excel(writer, index=False, sheet_name='Historico')
                xlsx_data = output.getvalue()
                st.download_button(
                    label="📥 Download Excel (.xlsx)",
                    data=xlsx_data,
                    file_name=f"historico_compras_sla_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception:
                st.caption("Não foi possível gerar Excel (.xlsx). Verifique a dependência 'openpyxl'.")

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
        st.markdown(get_section_header_html('⚙️ Configurações SLA'), unsafe_allow_html=True)
        st.markdown(get_info_box_html('🔧 <strong>Personalize os SLAs por prioridade e departamento</strong>'), unsafe_allow_html=True)
        
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

        st.markdown("---")
        st.subheader("🧾 Regras de Suprimentos (Cotações e Anexos)")
        st.caption("Defina a quantidade mínima de cotações para avançar à aprovação e se é obrigatório anexar documentos em ao menos 1 cotação.")

        cfg_rules = data.get("configuracoes", {})
        min_cot_atual = int(cfg_rules.get("suprimentos_min_cotacoes", 1))
        anexo_obrig_atual = bool(cfg_rules.get("suprimentos_anexo_obrigatorio", True))

        with st.form("regras_suprimentos_form"):
            c1, c2 = st.columns([1, 1])
            with c1:
                min_cot_novo = st.number_input(
                    "Mínimo de Cotações*",
                    min_value=1,
                    max_value=3,
                    step=1,
                    value=min_cot_atual,
                    help="Quantidade mínima de cotações válidas (Fornecedor e Valor) exigidas para seguir para aprovação."
                )
            with c2:
                anexo_obrig_novo = st.checkbox(
                    "Anexo obrigatório em ao menos 1 cotação",
                    value=anexo_obrig_atual,
                    help="Quando marcado, exige pelo menos 1 anexo em uma das cotações para avançar."
                )
            salvar_regras = st.form_submit_button("💾 Salvar Regras", use_container_width=True)

        if salvar_regras:
            try:
                # Garante limites coerentes com o formulário
                min_cot_val = int(min_cot_novo)
                min_cot_val = max(1, min(3, min_cot_val))
                data["configuracoes"]["suprimentos_min_cotacoes"] = min_cot_val
                data["configuracoes"]["suprimentos_anexo_obrigatorio"] = bool(anexo_obrig_novo)
                save_data(data)
                st.success("✅ Regras de Suprimentos salvas com sucesso.")
                st.rerun()
            except Exception:
                st.error("Não foi possível salvar as regras. Tente novamente.")
    
    elif opcao == "👥 Gerenciar Usuários":
        if perfil_atual != "Admin":
            st.error("Acesso restrito ao Admin.")
            return
        st.subheader("👥 Gerenciar Usuários")
        st.info("Crie usuários, defina perfis e redefina senhas.")
        with st.form("novo_usuario_form"):
            col1, col2 = st.columns(2)
            with col1:
                novo_username = st.text_input("Usuário*", key="new_user_username")
                novo_nome = st.text_input("Nome", key="new_user_name")
                novo_perfil = st.selectbox("Perfil*", ["Solicitante", "Suprimentos", "Gerência&Diretoria", "Admin"], key="new_user_profile")
            with col2:
                novo_depart = st.selectbox("Departamento", DEPARTAMENTOS, key="new_user_department")
                nova_senha = st.text_input("Senha*", type="password", key="new_user_password")
                nova_senha2 = st.text_input("Confirmar Senha*", type="password", key="new_user_password2")
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
        if USE_DATABASE:
            try:
                db = get_database()
                usuarios_list = db.get_all_users()
            except Exception:
                usuarios_list = []
        else:
            usuarios_list = data.get("usuarios", [])
        usuarios_df = pd.DataFrame([
            {"Usuário": u.get("username"), "Nome": u.get("nome"), "Perfil": u.get("perfil"), "Departamento": u.get("departamento")}
            for u in usuarios_list
        ])
        if usuarios_df.empty:
            usuarios_df = pd.DataFrame(columns=["Usuário", "Nome", "Perfil", "Departamento"])
        st.dataframe(usuarios_df, use_container_width=True, key="usuarios_df_table")
        if len(usuarios_list) == 0:
            st.caption("Nenhum usuário cadastrado além do admin.")
        
        st.markdown("---")
        st.subheader("Redefinir Senha")
        with st.form("reset_senha_form"):
            lista_usernames = [u.get("username") for u in usuarios_list]
            options_reset = lista_usernames if lista_usernames else ["(sem usuários)"]
            r_user = st.selectbox("Usuário", options_reset, key="reset_user_username")
            r_senha = st.text_input("Nova senha", type="password", key="reset_user_newpass")
            r_senha2 = st.text_input("Confirmar nova senha", type="password", key="reset_user_newpass2")
            bt_reset = st.form_submit_button("🔒 Redefinir")
        if bt_reset:
            if r_user not in lista_usernames:
                st.warning("Cadastre um usuário antes de redefinir a senha.")
            elif not r_senha or r_senha != r_senha2:
                st.error("Senhas não conferem.")
            else:
                erro = reset_user_password(data, r_user, r_senha)
                if erro:
                    st.error(erro)
                else:
                    if not USE_DATABASE:
                        save_data(data)
                    st.success(f"Senha de '{r_user}' redefinida com sucesso.")
    
    else:
        st.error("❌ Opção não implementada ainda.")

if __name__ == "__main__":
    main()
