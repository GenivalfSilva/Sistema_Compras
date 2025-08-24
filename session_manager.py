import streamlit as st
import uuid
import hashlib
from typing import Dict, Optional
from database_local import get_local_database

class SessionManager:
    """Gerenciador de sessões persistentes para Streamlit"""
    
    def __init__(self):
        self.db = get_local_database()
        self.session_key = "persistent_session_id"
    
    def create_session(self, username: str) -> str:
        """Cria nova sessão persistente"""
        session_id = str(uuid.uuid4())
        
        # Tenta salvar no banco de dados
        success = self.db.create_session(username, session_id)
        
        # Salva no session_state do Streamlit sempre
        st.session_state[self.session_key] = session_id
        st.session_state["session_username"] = username
        
        return session_id
    
    def get_current_user(self) -> Optional[Dict]:
        """Retorna usuário da sessão atual"""
        session_id = st.session_state.get(self.session_key)
        username = st.session_state.get("session_username")
        
        if not session_id or not username:
            return None
        
        # Tenta validar no banco, mas usa fallback se não disponível
        try:
            db_username = self.db.validate_session(session_id)
            if db_username:
                # Busca usuário por username no PostgreSQL local
                users = self.db.get_all_users()
                for user in users:
                    if user.get('username') == db_username:
                        return user
        except:
            pass
        
        # Fallback: usar dados do session_state
        if username:
            return {
                "username": username,
                "nome": username,
                "perfil": "Solicitante",  # Perfil padrão
                "departamento": "Outro"
            }
        
        return None
    
    def login(self, username: str, password: str) -> bool:
        """Faz login e cria sessão persistente"""
        # Tenta autenticar via banco se disponível
        user = None
        if hasattr(self.db, 'db_available') and self.db.db_available:
            user = self.db.authenticate_user(username, password)
        
        if user:
            session_id = self.create_session(username)
            
            # Salva dados do usuário no session_state
            st.session_state["usuario"] = {
                "username": user["username"],
                "nome": user["nome"],
                "perfil": user["perfil"],
                "departamento": user["departamento"]
            }
            
            return True
        
        return False
    
    def logout(self):
        """Faz logout e remove sessão"""
        session_id = st.session_state.get(self.session_key)
        
        if session_id:
            # PostgreSQL local não tem delete_session, mas não é crítico
            try:
                # Poderia implementar delete se necessário, mas sessões expiram automaticamente
                pass
            except:
                pass
        
        # Remove TODAS as chaves de sessão relacionadas ao usuário
        keys_to_remove = [
            self.session_key,
            "usuario", 
            "session_username",
            "_user_backup",
            "authenticated",
            "login_status"
        ]
        
        for key in keys_to_remove:
            st.session_state.pop(key, None)
        
        # Limpa qualquer cache de sessão
        st.session_state.clear()
    
    def is_logged_in(self) -> bool:
        """Verifica se usuário está logado"""
        return self.get_current_user() is not None
    
    def restore_session(self):
        """Restaura sessão ao carregar a página - CRÍTICO para evitar logout no refresh"""
        # Sempre tenta restaurar, mesmo se já existe usuário (para casos de refresh)
        user = self.get_current_user()
        if user:
            # Atualiza/restaura dados do usuário no session_state
            st.session_state["usuario"] = {
                "username": user.get("username"),
                "nome": user.get("nome", user.get("username")),
                "perfil": user.get("perfil"),
                "departamento": user.get("departamento")
            }
            # Garante que a sessão persistente também está definida
            if self.session_key not in st.session_state:
                st.session_state[self.session_key] = str(uuid.uuid4())
            return True
        return False

# Singleton para gerenciar instância única
_session_manager = None

def get_session_manager():
    """Retorna instância única do gerenciador de sessões"""
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
    
    return _session_manager
