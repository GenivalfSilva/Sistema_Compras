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

def _get_cookie_secret() -> str:
    """Obtém segredo para assinar o cookie (use st.secrets se disponível)."""
    try:
        if hasattr(st, "secrets") and "cookie_secret" in st.secrets:
            return str(st.secrets["cookie_secret"])  # configurável no deploy
    except Exception:
        pass
    return os.getenv("COOKIE_SECRET", "ziran_session_secret_v1")

def _get_cookie_manager():
    """Retorna instância do CookieManager se disponível."""
    if stx is None:
        return None
    # O componente precisa ser instanciado durante o script
    return stx.CookieManager()

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
            return user_obj
    return None

def ensure_session_persistence():
    """Garante que a sessão persista após refresh"""
    # 1) Se já há usuário em memória, nada a fazer
    if "usuario" in st.session_state:
        return st.session_state["usuario"]
    # 2) Tenta restaurar de cookie
    user = _read_login_cookie()
    if user:
        st.session_state["usuario"] = user
        return user
    return None

def simple_logout():
    """Logout simples"""
    keys_to_remove = ["usuario", "session_persistent"]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    # Remove cookie de sessão
    _clear_login_cookie()
