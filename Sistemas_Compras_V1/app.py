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

# Configuração para PostgreSQL local na EC2
USE_DATABASE = True
try:
    from database_local import get_local_database
    from session_manager import get_session_manager
    print("✅ Usando PostgreSQL local na EC2")
except Exception as e:
    USE_DATABASE = False
    print(f"❌ Erro ao conectar PostgreSQL local: {e}")
    st.error("❌ Erro na conexão com banco de dados. Verifique a configuração do PostgreSQL.")

# Configuração da página será feita na função main

# Arquivo para armazenar os dados
DATA_FILE = "compras_sla_data.json"

# Configurações baseadas na planilha Excel - Fluxo completo com Requisição
ETAPAS_PROCESSO = [
    "Solicitação",
    "Requisição",
    "Suprimentos", 
    "Em Cotação",
    "Pedido de Compras",
    "Aguardando Aprovação",
    "Aprovado",
    "Reprovado",
    "Compra feita",
    "Aguardando Entrega",
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
            st.dataframe(df, width='stretch')
            return df

# Configurações de upload e anexos
ALLOWED_FILE_TYPES = ["pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"]
UPLOAD_ROOT_DEFAULT = "uploads"

def load_data() -> Dict:
    """Carrega os dados do banco PostgreSQL local"""
    if USE_DATABASE:
        try:
            db = get_local_database()
            if db.db_available:
                # Carrega dados do banco
                solicitacoes = db.get_all_solicitacoes()
                
                # Busca configurações do banco
                catalogo_produtos = db.get_catalogo_produtos()
                if not catalogo_produtos:
                    # Inicializa catálogo padrão se vazio
                    for produto in get_default_product_catalog():
                        db.update_catalogo_produtos([produto])
                    catalogo_produtos = db.get_catalogo_produtos()
                
                # Busca próximos números
                proximo_sol = int(db.get_config('proximo_numero_solicitacao', '1'))
                proximo_ped = int(db.get_config('proximo_numero_pedido', '1'))
                # Garante que os próximos números não conflitem com registros existentes
                try:
                    max_sol = max([s.get('numero_solicitacao_estoque') or 0 for s in solicitacoes] or [0])
                    if proximo_sol <= max_sol:
                        proximo_sol = max_sol + 1
                        db.set_config('proximo_numero_solicitacao', str(proximo_sol))
                except Exception:
                    pass
                try:
                    max_ped = max([s.get('numero_pedido_compras') or 0 for s in solicitacoes] or [0])
                    if proximo_ped <= max_ped:
                        proximo_ped = max_ped + 1
                        db.set_config('proximo_numero_pedido', str(proximo_ped))
                except Exception:
                    pass
                
                # Monta estrutura compatível
                data = {
                    "solicitacoes": solicitacoes,
                    "movimentacoes": [],
                    "configuracoes": {
                        "sla_por_departamento": {},
                        "proximo_numero_solicitacao": proximo_sol,
                        "proximo_numero_pedido": proximo_ped,
                        "limite_gerencia": float(db.get_config('limite_gerencia', '5000.0')),
                        "limite_diretoria": float(db.get_config('limite_diretoria', '15000.0')),
                        "upload_dir": db.get_config('upload_dir', UPLOAD_ROOT_DEFAULT),
                        "suprimentos_min_cotacoes": int(db.get_config('suprimentos_min_cotacoes', '1')),
                        "suprimentos_anexo_obrigatorio": db.get_config('suprimentos_anexo_obrigatorio', 'True') == 'True',
                        "catalogo_produtos": catalogo_produtos
                    },
                    "notificacoes": [],
                    "usuarios": []
                }
                return data
        except Exception as e:
            print(f"Erro ao carregar dados do banco: {e}")
    
    # Fallback para JSON se banco não disponível
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
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
    """Salva os dados no banco PostgreSQL local ou arquivo JSON (fallback)"""
    if USE_DATABASE:
        try:
            db = get_local_database()
            if db.db_available:
                # Salva configurações no banco
                config = data.get("configuracoes", {})
                for key, value in config.items():
                    if key != "catalogo_produtos":  # Catálogo tem tabela própria
                        db.set_config(key, str(value))
                
                # Salva catálogo se modificado
                catalogo = config.get("catalogo_produtos", [])
                if catalogo:
                    db.update_catalogo_produtos(catalogo)
                
                return  # Sucesso - dados salvos no banco
        except Exception as e:
            print(f"Erro ao salvar no banco: {e}")
    
    # Fallback para JSON
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
        # Notificações desabilitadas conforme solicitação do cliente
        pass
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
        db = get_local_database()
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
        db = get_local_database()
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
        db = get_local_database()
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
        db = get_local_database()
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
    # Configuração da página - deve ser a primeira chamada Streamlit
    st.set_page_config(
        page_title="Sistema de Gestão de Compras - SLA",
        page_icon="📋",
        layout="wide"
    )
    
    # Inicializa chaves de sessão
    initialize_persistent_keys()
    
    # Restaura sessão do PostgreSQL local
    if USE_DATABASE:
        try:
            session_manager = get_session_manager()
            session_manager.restore_session()
        except Exception as e:
            print(f"Erro ao restaurar sessão: {e}")
    else:
        # Fallback para sistema simples
        try:
            ensure_session_persistence()
        except Exception:
            pass

def initialize_persistent_keys():
    """Inicializa chaves persistentes que sobrevivem ao refresh"""
    # Cria chaves únicas baseadas no session_id do Streamlit
    if "_app_session_id" not in st.session_state:
        import time
        st.session_state["_app_session_id"] = f"ziran_{int(time.time())}"
    
    # Preserva dados do usuário em chaves especiais
    if "usuario" in st.session_state and "_user_backup" not in st.session_state:
        st.session_state["_user_backup"] = st.session_state["usuario"]
    
    # Restaura usuário se perdido mas backup existe
    if "usuario" not in st.session_state and "_user_backup" in st.session_state:
        st.session_state["usuario"] = st.session_state["_user_backup"]
    
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
        st.markdown('<h1 class="title-text" style="color: #000000 !important; background: rgba(255,255,255,0.9) !important; padding: 0.5rem !important; border-radius: 8px !important; text-shadow: none !important;">📋 Sistema de Gestão de Compras - SLA</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle-text">Controle de Solicitações e Medição de SLA</p>', unsafe_allow_html=True)
        st.markdown('<p class="brand-text">✨ Ziran - Gestão Inteligente</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Carrega os dados
    data = load_data()
    
    # Sidebar com design melhorado
    st.sidebar.markdown(get_sidebar_css(), unsafe_allow_html=True)
    
    # Para ambiente local sem banco, garante usuário admin no JSON
    if not USE_DATABASE:
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
                # Sistema simples de fallback
                user = authenticate_user(data, login_user.strip(), login_pass)
                
                if user:
                    st.session_state["usuario"] = user
                    st.session_state["_user_backup"] = user
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
                # Limpa sessão simples
                if "usuario" in st.session_state:
                    del st.session_state["usuario"]
                if "_user_backup" in st.session_state:
                    del st.session_state["_user_backup"]
            st.rerun()
    
    # Notificações removidas conforme solicitação do cliente
    # (Cliente mencionou que com muitas solicitações ficaria muita informação)

    # Navegação por perfil usando módulos
    st.sidebar.markdown("### 🔧 Navegação")
    st.sidebar.markdown("*Selecione uma opção abaixo:*")
    
    # Importa módulos de perfil
    if perfil_atual == "Admin":
        from profiles.admin import get_profile_options
        opcoes = get_profile_options()
    elif perfil_atual == "Gerência&Diretoria" or perfil_atual.lower() == "aprovador":
        from profiles.diretoria import get_profile_options
        opcoes = get_profile_options()
    elif perfil_atual.lower() == "suprimentos":
        from profiles.suprimentos import get_profile_options
        opcoes = get_profile_options()
    elif perfil_atual.lower() == "estoque":
        from profiles.estoque import get_profile_options
        opcoes = get_profile_options()
    else:  # Solicitante
        from profiles.solicitante import get_profile_options
        opcoes = get_profile_options()
    
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
    
    # Roteamento para módulos de perfil
    if perfil_atual == "Admin":
        from profiles.admin import handle_profile_option
        handle_profile_option(opcao, data, usuario, USE_DATABASE)
    elif perfil_atual == "Gerência&Diretoria" or perfil_atual.lower() == "aprovador":
        from profiles.diretoria import handle_profile_option
        handle_profile_option(opcao, data, usuario, USE_DATABASE)
    elif perfil_atual.lower() == "suprimentos":
        from profiles.suprimentos import handle_profile_option
        handle_profile_option(opcao, data, usuario, USE_DATABASE)
    elif perfil_atual.lower() == "estoque":
        from profiles.estoque import handle_profile_option
        handle_profile_option(opcao, data, usuario, USE_DATABASE)
    else:  # Solicitante
        from profiles.solicitante import handle_profile_option
        handle_profile_option(opcao, data, usuario, USE_DATABASE)

def init_session():
    """Inicializa sessão no início da aplicação"""
    if USE_DATABASE:
        try:
            session_manager = get_session_manager()
            session_manager.restore_session()
        except Exception:
            pass
    
    # Restaura backup de usuário se disponível
    if "usuario" not in st.session_state and "_user_backup" in st.session_state:
        st.session_state["usuario"] = st.session_state["_user_backup"]

if __name__ == "__main__":
    init_session()
    main()
