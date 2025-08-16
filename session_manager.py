import streamlit as st
import uuid
import hashlib
from typing import Dict, Optional
from database import get_database

class SessionManager:
    """Gerenciador de sessões persistentes para Streamlit"""
    
    def __init__(self):
        self.db = get_database()
        self.session_key = "persistent_session_id"
    
    def create_session(self, username: str) -> str:
        """Cria nova sessão persistente"""
        session_id = str(uuid.uuid4())
        
        # Salva no banco de dados
        self.db.create_session(username, session_id)
        
        # Salva no session_state do Streamlit
        st.session_state[self.session_key] = session_id
        
        return session_id
    
    def get_current_user(self) -> Optional[Dict]:
        """Retorna usuário da sessão atual"""
        session_id = st.session_state.get(self.session_key)
        
        if not session_id:
            return None
        
        username = self.db.validate_session(session_id)
        if not username:
            # Sessão expirada ou inválida
            self.logout()
            return None
        
        # Busca dados do usuário
        user = self.db.authenticate_user_by_username(username)
        return user
    
    def login(self, username: str, password: str) -> bool:
        """Faz login e cria sessão persistente"""
        user = self.db.authenticate_user(username, password)
        
        if user:
            session_id = self.create_session(username)
            
            # Salva dados do usuário no session_state
            st.session_state["usuario"] = {
                "username": user.get("username"),
                "nome": user.get("nome", user.get("username")),
                "perfil": user.get("perfil"),
                "departamento": user.get("departamento"),
                "session_id": session_id
            }
            return True
        
        return False
    
    def logout(self):
        """Faz logout e remove sessão"""
        session_id = st.session_state.get(self.session_key)
        
        if session_id:
            self.db.delete_session(session_id)
        
        # Remove do session_state
        st.session_state.pop(self.session_key, None)
        st.session_state.pop("usuario", None)
    
    def is_logged_in(self) -> bool:
        """Verifica se usuário está logado"""
        return self.get_current_user() is not None
    
    def restore_session(self):
        """Restaura sessão ao carregar a página"""
        if "usuario" not in st.session_state:
            user = self.get_current_user()
            if user:
                st.session_state["usuario"] = {
                    "username": user.get("username"),
                    "nome": user.get("nome", user.get("username")),
                    "perfil": user.get("perfil"),
                    "departamento": user.get("departamento")
                }

# Singleton para gerenciar instância única
_session_manager = None

def get_session_manager():
    """Retorna instância única do gerenciador de sessões"""
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
    
    return _session_manager
