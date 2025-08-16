import sqlite3
import json
import os
from typing import Dict, List
import datetime
import streamlit as st

class DatabaseManager:
    """Gerenciador de banco de dados para Streamlit Cloud e local"""
    
    def __init__(self, use_cloud_db=False):
        self.use_cloud_db = use_cloud_db
        if use_cloud_db:
            # Para Streamlit Cloud - usar st.secrets para configuração
            self.setup_cloud_database()
        else:
            # Para desenvolvimento local
            self.db_path = "compras_sla.db"
            self.setup_local_database()
    
    def setup_local_database(self):
        """Configura banco SQLite local"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
    
    def setup_cloud_database(self):
        """Configura banco para Streamlit Cloud"""
        try:
            # Exemplo para PostgreSQL no Streamlit Cloud
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Usar st.secrets para credenciais
            self.conn = psycopg2.connect(
                host=st.secrets["database"]["host"],
                database=st.secrets["database"]["name"],
                user=st.secrets["database"]["user"],
                password=st.secrets["database"]["password"],
                port=st.secrets["database"]["port"],
                cursor_factory=RealDictCursor
            )
            self.create_tables_postgres()
        except ImportError:
            st.error("psycopg2 não instalado. Usando SQLite local.")
            self.use_cloud_db = False
            self.setup_local_database()
        except Exception as e:
            st.error(f"Erro ao conectar banco cloud: {e}")
            self.use_cloud_db = False
            self.setup_local_database()
    
    def create_tables(self):
        """Cria tabelas SQLite"""
        cursor = self.conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            perfil TEXT NOT NULL,
            departamento TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabela de solicitações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_solicitacao_estoque INTEGER UNIQUE NOT NULL,
            solicitante TEXT NOT NULL,
            departamento TEXT NOT NULL,
            descricao TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            aplicacao INTEGER NOT NULL,
            status TEXT NOT NULL,
            etapa_atual TEXT NOT NULL,
            data_criacao TIMESTAMP NOT NULL,
            valor_estimado REAL,
            valor_final REAL,
            fornecedor_recomendado TEXT,
            fornecedor_final TEXT,
            sla_cumprido TEXT,
            anexos TEXT,  -- JSON string
            cotacoes TEXT,  -- JSON string
            aprovacoes TEXT,  -- JSON string
            historico_etapas TEXT,  -- JSON string
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabela de configurações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabela de notificações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perfil TEXT NOT NULL,
            numero INTEGER NOT NULL,
            mensagem TEXT NOT NULL,
            data TIMESTAMP NOT NULL,
            lida BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabela de sessões (para persistência de login)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()
    
    def create_tables_postgres(self):
        """Cria tabelas PostgreSQL para Streamlit Cloud"""
        cursor = self.conn.cursor()
        
        # Similar ao SQLite mas com sintaxe PostgreSQL
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            nome VARCHAR(100) NOT NULL,
            perfil VARCHAR(50) NOT NULL,
            departamento VARCHAR(50) NOT NULL,
            senha_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Outras tabelas...
        self.conn.commit()
    
    def migrate_from_json(self, json_file_path: str):
        """Migra dados do JSON para o banco de dados"""
        if not os.path.exists(json_file_path):
            return
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Migrar usuários
            for user in data.get('usuarios', []):
                self.add_user(
                    user['username'],
                    user['nome'],
                    user['perfil'],
                    user['departamento'],
                    user['senha_hash'],
                    is_hashed=True
                )
            
            # Migrar solicitações
            for sol in data.get('solicitacoes', []):
                self.add_solicitacao(sol)
            
            # Migrar configurações
            config = data.get('configuracoes', {})
            for key, value in config.items():
                self.set_config(key, json.dumps(value) if isinstance(value, (dict, list)) else str(value))
            
            print(f"Migração concluída de {json_file_path}")
            
        except Exception as e:
            print(f"Erro na migração: {e}")
    
    def add_user(self, username: str, nome: str, perfil: str, departamento: str, senha_hash: str, is_hashed=False):
        """Adiciona usuário ao banco"""
        cursor = self.conn.cursor()
        
        if not is_hashed:
            # Hash da senha se necessário
            import hashlib
            SALT = "ziran_local_salt_v1"
            senha_hash = hashlib.sha256((SALT + senha_hash).encode("utf-8")).hexdigest()
        
        try:
            cursor.execute('''
            INSERT INTO usuarios (username, nome, perfil, departamento, senha_hash)
            VALUES (?, ?, ?, ?, ?)
            ''', (username, nome, perfil, departamento, senha_hash))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Usuário já existe
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Autentica usuário"""
        import hashlib
        SALT = "ziran_local_salt_v1"
        senha_hash = hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()
        
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT username, nome, perfil, departamento
        FROM usuarios 
        WHERE username = ? AND senha_hash = ?
        ''', (username, senha_hash))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {}
    
    def get_all_users(self) -> List[Dict]:
        """Retorna todos os usuários"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT username, nome, perfil, departamento FROM usuarios')
        return [dict(row) for row in cursor.fetchall()]
    
    def create_session(self, username: str, session_id: str, expires_hours=24):
        """Cria sessão persistente"""
        cursor = self.conn.cursor()
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=expires_hours)
        
        cursor.execute('''
        INSERT OR REPLACE INTO sessoes (id, username, expires_at)
        VALUES (?, ?, ?)
        ''', (session_id, username, expires_at))
        self.conn.commit()
    
    def validate_session(self, session_id: str) -> str:
        """Valida sessão e retorna username"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT username FROM sessoes 
        WHERE id = ? AND expires_at > CURRENT_TIMESTAMP
        ''', (session_id,))
        
        row = cursor.fetchone()
        return row['username'] if row else None
    
    def delete_session(self, session_id: str):
        """Remove sessão"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM sessoes WHERE id = ?', (session_id,))
        self.conn.commit()
    
    def set_config(self, key: str, value: str):
        """Define configuração"""
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO configuracoes (chave, valor, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        self.conn.commit()
    
    def get_config(self, key: str, default=None):
        """Obtém configuração"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT valor FROM configuracoes WHERE chave = ?', (key,))
        row = cursor.fetchone()
        return row['valor'] if row else default
    
    def close(self):
        """Fecha conexão"""
        if hasattr(self, 'conn'):
            self.conn.close()

# Singleton para gerenciar instância única
_db_instance = None

def get_database(use_cloud_db=None):
    """Retorna instância única do banco"""
    global _db_instance
    
    if _db_instance is None:
        # Detectar se está no Streamlit Cloud
        if use_cloud_db is None:
            use_cloud_db = os.getenv('STREAMLIT_SHARING_MODE') == 'true' or 'streamlit.app' in os.getenv('HOSTNAME', '')
        
        _db_instance = DatabaseManager(use_cloud_db)
    
    return _db_instance
