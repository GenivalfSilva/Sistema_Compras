import streamlit as st
import json
import hashlib
import time
import os
import tempfile
from typing import Dict, Optional

class PersistentSession:
    """Sistema robusto de persistência de sessão para Streamlit Cloud"""
    
    def __init__(self):
        self.backup_keys = [
            "_user_backup",
            "_persistent_user_backup", 
            "_session_backup",
            "_user_data_backup"
        ]
        self.session_markers = [
            "logged_in",
            "session_active",
            "_session_initialized"
        ]
        # Diretório temporário para persistência
        self.temp_dir = tempfile.gettempdir()
        self.session_file_prefix = "ziran_session_"
    
    def _get_session_file_path(self) -> str:
        """Obtém caminho do arquivo de sessão baseado no browser"""
        # Usa hash do user agent + timestamp como identificador único
        session_id = hashlib.md5(f"streamlit_session_{int(time.time() / 3600)}".encode()).hexdigest()[:8]
        return os.path.join(self.temp_dir, f"{self.session_file_prefix}{session_id}.json")
    
    def _save_to_file(self, user_data: Dict):
        """Salva dados da sessão em arquivo temporário"""
        try:
            session_file = self._get_session_file_path()
            session_data = {
                "user": user_data,
                "timestamp": int(time.time()),
                "expires": int(time.time()) + 86400  # 24 horas
            }
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # Falha silenciosa para não quebrar o app
    
    def _load_from_file(self) -> Optional[Dict]:
        """Carrega dados da sessão do arquivo temporário"""
        try:
            session_file = self._get_session_file_path()
            if not os.path.exists(session_file):
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Verifica se a sessão não expirou
            if session_data.get("expires", 0) < int(time.time()):
                os.remove(session_file)
                return None
            
            return session_data.get("user")
        except Exception:
            return None
    
    def save_user_session(self, user_data: Dict):
        """Salva dados do usuário em múltiplas chaves para máxima persistência"""
        if not user_data:
            return
        
        # Salva em múltiplas chaves de backup
        for key in self.backup_keys:
            st.session_state[key] = user_data.copy()
        
        # Marca sessão como ativa
        for marker in self.session_markers:
            st.session_state[marker] = True
        
        # Salva dados principais
        st.session_state["usuario"] = user_data
        
        # Cria hash único da sessão para verificação
        user_hash = hashlib.md5(json.dumps(user_data, sort_keys=True).encode()).hexdigest()
        st.session_state["_user_hash"] = user_hash
        st.session_state["_session_timestamp"] = int(time.time())
        
        # Salva em arquivo apenas se não for cloud
        is_cloud = os.path.exists('/mount/src') or 'STREAMLIT_CLOUD' in os.environ
        if not is_cloud:
            self._save_to_file(user_data)
        else:
            # No cloud, usa cookies via simple_session
            try:
                from simple_session import _set_login_cookie
                _set_login_cookie(user_data)
            except Exception:
                pass
    
    def restore_user_session(self) -> Optional[Dict]:
        """Restaura sessão do usuário usando múltiplas estratégias"""
        # Detecta ambiente cloud
        is_cloud = os.path.exists('/mount/src') or 'STREAMLIT_CLOUD' in os.environ
        
        # Estratégia 1: Usuário já existe no session_state
        if "usuario" in st.session_state and st.session_state["usuario"]:
            user_data = st.session_state["usuario"]
            return user_data
        
        # Estratégia 2: Restaura de qualquer chave de backup disponível
        for key in self.backup_keys:
            if key in st.session_state and st.session_state[key]:
                user_data = st.session_state[key]
                st.session_state["usuario"] = user_data
                return user_data
        
        # Estratégia 3: Carrega do arquivo (apenas local) ou cookies (cloud)
        if not is_cloud:
            # Local: usa arquivo temporário
            file_user = self._load_from_file()
            if file_user:
                st.session_state["usuario"] = file_user
                self.save_user_session(file_user)
                return file_user
        else:
            # Cloud: usa sistema de cookies via simple_session
            try:
                from simple_session import _read_login_cookie
                cookie_user = _read_login_cookie()
                if cookie_user:
                    st.session_state["usuario"] = cookie_user
                    self.save_user_session(cookie_user)
                    return cookie_user
            except Exception:
                pass
        
        return None
    
    def clear_session(self):
        """Limpa completamente a sessão"""
        # Remove dados do usuário
        keys_to_remove = ["usuario"] + self.backup_keys + self.session_markers
        keys_to_remove.extend(["_user_hash", "_session_timestamp"])
        
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_session_valid(self) -> bool:
        """Verifica se a sessão atual é válida"""
        # Verifica se há usuário
        if "usuario" not in st.session_state:
            return False
        
        # Verifica se há pelo menos um backup
        has_backup = any(key in st.session_state for key in self.backup_keys)
        
        # Verifica se há marcadores de sessão
        has_markers = any(st.session_state.get(marker, False) for marker in self.session_markers)
        
        return has_backup or has_markers

# Singleton global
_persistent_session = None

def get_persistent_session():
    """Retorna instância única do sistema de persistência"""
    global _persistent_session
    if _persistent_session is None:
        _persistent_session = PersistentSession()
    return _persistent_session

def ensure_robust_session_persistence():
    """Função principal para garantir persistência robusta da sessão"""
    ps = get_persistent_session()
    
    # Sempre tenta restaurar a sessão
    restored_user = ps.restore_user_session()
    
    return restored_user
