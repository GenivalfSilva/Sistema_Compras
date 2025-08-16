import streamlit as st
import hashlib
from typing import Dict, Optional

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
            return {
                "username": user["username"],
                "nome": user.get("nome", username),
                "perfil": user.get("perfil", "Solicitante"),
                "departamento": user.get("departamento", "Outro")
            }
    return None

def ensure_session_persistence():
    """Garante que a sessão persista após refresh"""
    # Usa apenas session_state do Streamlit para persistência simples
    if "session_persistent" not in st.session_state:
        st.session_state["session_persistent"] = True
    
    # Mantém dados do usuário na sessão
    if "usuario" in st.session_state:
        return st.session_state["usuario"]
    
    return None

def simple_logout():
    """Logout simples"""
    keys_to_remove = ["usuario", "session_persistent"]
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
