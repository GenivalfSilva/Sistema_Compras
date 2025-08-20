import streamlit as st
import hashlib
from typing import Dict, Optional
import json
import time
import base64
import datetime
import os
import hmac

# Tenta usar extra-streamlit-components para cookies persistentes
try:
    import extra_streamlit_components as stx
except Exception:
    stx = None

# Nome do cookie de autenticação
COOKIE_NAME = "ziran_auth"

# Singleton do CookieManager para evitar chaves duplicadas
_COOKIE_MANAGER_SINGLETON = None

def _get_cookie_secret() -> str:
    """Obtém segredo para assinar o cookie (use st.secrets se disponível)."""
    try:
        if hasattr(st, "secrets") and "cookie_secret" in st.secrets:
            return str(st.secrets["cookie_secret"])  # configurável no deploy
    except Exception:
        pass
    return os.getenv("COOKIE_SECRET", "ziran_session_secret_v1")

def _get_cookie_manager():
    """Retorna instância única do CookieManager se disponível."""
    global _COOKIE_MANAGER_SINGLETON
    if stx is None:
        return None
    if _COOKIE_MANAGER_SINGLETON is None:
        # Use uma key única e estável para o componente
        _COOKIE_MANAGER_SINGLETON = stx.CookieManager(key="ziran_cookie_manager_v1")
    return _COOKIE_MANAGER_SINGLETON

def _sign_payload(payload_b64: str) -> str:
    secret = _get_cookie_secret().encode("utf-8")
    return hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()

def _encode_token(payload: Dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(raw).decode("ascii")
    signature = _sign_payload(payload_b64)
    return f"{payload_b64}.{signature}"

def _decode_token(token: str) -> Optional[Dict]:
    if not token or "." not in token:
        return None
    payload_b64, signature = token.split(".", 1)
    if _sign_payload(payload_b64) != signature:
        return None
    try:
        raw = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        data = json.loads(raw)
        # Verifica expiração
        if int(data.get("exp", 0)) < int(time.time()):
            return None
        return {
            "username": data.get("u"),
            "nome": data.get("n", data.get("u")),
            "perfil": data.get("p", "Solicitante"),
            "departamento": data.get("d", "Outro"),
        }
    except Exception:
        return None

def _set_login_cookie(user: Dict, hours_valid: int = 24):
    cm = _get_cookie_manager()
    if cm is None:
        return
    exp = int(time.time()) + hours_valid * 3600
    payload = {
        "u": user.get("username"),
        "n": user.get("nome", user.get("username")),
        "p": user.get("perfil", "Solicitante"),
        "d": user.get("departamento", "Outro"),
        "exp": exp,
    }
    token = _encode_token(payload)
    try:
        cm.set(
            COOKIE_NAME,
            token,
            expires_at=datetime.datetime.utcfromtimestamp(exp),
            key="cookie_mgr_set",
        )
    except Exception:
        # Falha silenciosa para não quebrar o app
        pass

def _read_login_cookie() -> Optional[Dict]:
    cm = _get_cookie_manager()
    if cm is None:
        return None
    try:
        token = cm.get(COOKIE_NAME, key="cookie_mgr_get")
        return _decode_token(token)
    except Exception:
        return None

def _clear_login_cookie():
    cm = _get_cookie_manager()
    if cm is None:
        return
    try:
        cm.delete(COOKIE_NAME, key="cookie_mgr_del")
    except Exception:
        pass

def hash_password(password: str) -> str:
    """Hash da senha com salt"""
    SALT = "ziran_local_salt_v1"
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()

def simple_login(data: Dict, username: str, password: str) -> Optional[Dict]:
    """Sistema de login simples para cloud"""
    usuarios = data.get("usuarios", [])
    
    for user in usuarios:
        if (user.get("username") == username and 
            user.get("senha_hash") == hash_password(password)):
            user_obj = {
                "username": user["username"],
                "nome": user.get("nome", username),
                "perfil": user.get("perfil", "Solicitante"),
                "departamento": user.get("departamento", "Outro")
            }
            # Define cookie de sessão para persistir após refresh
            _set_login_cookie(user_obj)
            # Cria backup no session_state também
            st.session_state["_persistent_user_backup"] = user_obj
            return user_obj
    return None

def ensure_session_persistence():
    """Garante que a sessão persista após refresh - CRÍTICO para evitar logout"""
    try:
        # Debug: verifica se o cookie manager está disponível
        cm = _get_cookie_manager()
        if cm is None:
            # Fallback: usa session_state com chave especial para persistência
            if "_persistent_user_backup" in st.session_state and "usuario" not in st.session_state:
                st.session_state["usuario"] = st.session_state["_persistent_user_backup"]
                return st.session_state["usuario"]
            return st.session_state.get("usuario")
        
        # Sempre tenta restaurar de cookie, mesmo se já existe usuário (para casos de refresh)
        user = _read_login_cookie()
        if user:
            # Sempre atualiza/restaura o session_state com dados do cookie
            st.session_state["usuario"] = user
            st.session_state["_persistent_user_backup"] = user  # Backup adicional
            st.session_state["session_persistent"] = True
            return user
        
        # Se não há cookie mas há usuário em memória, mantém
        if "usuario" in st.session_state:
            # Cria backup para próxima sessão
            st.session_state["_persistent_user_backup"] = st.session_state["usuario"]
            return st.session_state["usuario"]
        
        return None
    except Exception as e:
        # Em caso de erro, tenta usar backup do session_state
        if "_persistent_user_backup" in st.session_state:
            st.session_state["usuario"] = st.session_state["_persistent_user_backup"]
            return st.session_state["usuario"]
        return st.session_state.get("usuario")

def simple_logout():
    """Logout simples"""
    keys_to_remove = ["usuario", "session_persistent"]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    # Remove cookie de sessão
    _clear_login_cookie()
