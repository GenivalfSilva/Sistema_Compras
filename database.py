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
        # Tipo do banco atual: 'sqlite' ou 'postgres'
        self.db_type = 'sqlite'
        self.db_available = False
        self.conn = None
        
        if use_cloud_db:
            # Para Streamlit Cloud - usar st.secrets para configuração
            self.setup_cloud_database()
        else:
            # Para desenvolvimento local
            self.db_path = "compras_sla.db"
            self.setup_local_database()
    
    def setup_local_database(self):
        """Configura banco SQLite local"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.db_type = 'sqlite'
            self.create_tables()
            self.db_available = True
        except Exception as e:
            print(f"SQLite setup failed: {e}")
            self.db_available = False
            self.conn = None
    
    def setup_cloud_database(self):
        """Configura banco para Streamlit Cloud"""
        try:
            # Tenta PostgreSQL primeiro se configurado
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = None
            if hasattr(st, 'secrets') and ('postgres' in st.secrets or 'database' in st.secrets):
                pg = st.secrets.get("postgres") or st.secrets.get("database")
                # sslmode opcional; default para 'require' quando usando provedores gerenciados (Neon)
                sslmode = pg.get("sslmode", "require")
                conn = psycopg2.connect(
                    host=pg["host"],
                    database=pg.get("database") or pg.get("name"),
                    user=pg["user"],
                    password=pg["password"],
                    port=int(pg.get("port", 5432)),
                    sslmode=sslmode,
                    cursor_factory=RealDictCursor,
                )
            elif hasattr(st, 'secrets') and 'postgres_url' in st.secrets:
                conn = psycopg2.connect(st.secrets['postgres_url'], cursor_factory=RealDictCursor)
            elif hasattr(st, 'secrets') and 'database_url' in st.secrets:
                conn = psycopg2.connect(st.secrets['database_url'], cursor_factory=RealDictCursor)
            elif os.getenv('DATABASE_URL'):
                conn = psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)

            if conn is not None:
                self.conn = conn
                self.db_type = 'postgres'
                self.create_tables_postgres()
                self.db_available = True
                return
        except Exception as e:
            print(f"PostgreSQL não disponível: {e}")
        
        # Fallback: desabilita banco completamente no cloud
        print("Cloud environment detected - database disabled")
        self.db_available = False
        self.conn = None

    def _sql(self, sql: str) -> str:
        """Ajusta placeholders para o driver atual."""
        if self.db_type == 'postgres':
            # Converte placeholders estilo SQLite (?) para psycopg2 (%s)
            return sql.replace('?', '%s')
        return sql
    
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
            numero_pedido_compras INTEGER,
            solicitante TEXT NOT NULL,
            departamento TEXT NOT NULL,
            descricao TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            local_aplicacao TEXT NOT NULL,
            status TEXT NOT NULL,
            etapa_atual TEXT NOT NULL,
            carimbo_data_hora TEXT NOT NULL,
            data_numero_pedido TEXT,
            data_cotacao TEXT,
            data_entrega TEXT,
            sla_dias INTEGER NOT NULL,
            dias_atendimento INTEGER,
            sla_cumprido TEXT,
            observacoes TEXT,
            numero_requisicao_interno TEXT,
            data_requisicao_interna TEXT,
            responsavel_suprimentos TEXT,
            valor_estimado REAL,
            valor_final REAL,
            fornecedor_recomendado TEXT,
            fornecedor_final TEXT,
            anexos_requisicao TEXT,  -- JSON string
            cotacoes TEXT,  -- JSON string
            aprovacoes TEXT,  -- JSON string
            historico_etapas TEXT,  -- JSON string
            itens TEXT,  -- JSON string
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
        
        # Tabela de produtos do catálogo
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalogo_produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            categoria TEXT,
            unidade TEXT NOT NULL,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabela de movimentações (histórico de mudanças)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_solicitacao INTEGER NOT NULL,
            etapa_origem TEXT NOT NULL,
            etapa_destino TEXT NOT NULL,
            usuario TEXT NOT NULL,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observacoes TEXT
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
        # Após criar tabelas, garante que bases antigas tenham colunas novas
        try:
            self._migrate_sqlite_schema()
        except Exception as e:
            print(f"SQLite schema migration warning: {e}")
    
    def create_tables_postgres(self):
        """Cria tabelas PostgreSQL para Streamlit Cloud"""
        cursor = self.conn.cursor()
        
        # Tabela de usuários
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

        # Tabela de solicitações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id SERIAL PRIMARY KEY,
            numero_solicitacao_estoque INTEGER UNIQUE NOT NULL,
            numero_pedido_compras INTEGER,
            solicitante TEXT NOT NULL,
            departamento TEXT NOT NULL,
            descricao TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            local_aplicacao TEXT NOT NULL,
            status TEXT NOT NULL,
            etapa_atual TEXT NOT NULL,
            carimbo_data_hora TEXT NOT NULL,
            data_numero_pedido TEXT,
            data_cotacao TEXT,
            data_entrega TEXT,
            sla_dias INTEGER NOT NULL,
            dias_atendimento INTEGER,
            sla_cumprido TEXT,
            observacoes TEXT,
            numero_requisicao_interno TEXT,
            data_requisicao_interna TEXT,
            responsavel_suprimentos TEXT,
            valor_estimado DOUBLE PRECISION,
            valor_final DOUBLE PRECISION,
            fornecedor_recomendado TEXT,
            fornecedor_final TEXT,
            anexos_requisicao TEXT,  -- JSON string
            cotacoes TEXT,  -- JSON string
            aprovacoes TEXT,  -- JSON string
            historico_etapas TEXT,  -- JSON string
            itens TEXT,  -- JSON string
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Tabela de configurações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            id SERIAL PRIMARY KEY,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabela de produtos do catálogo
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS catalogo_produtos (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            categoria TEXT,
            unidade TEXT NOT NULL,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tabela de movimentações (histórico de mudanças)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id SERIAL PRIMARY KEY,
            numero_solicitacao INTEGER NOT NULL,
            etapa_origem TEXT NOT NULL,
            etapa_destino TEXT NOT NULL,
            usuario TEXT NOT NULL,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observacoes TEXT
        )
        ''')

        # Tabela de notificações
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notificacoes (
            id SERIAL PRIMARY KEY,
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
    
    def _get_sqlite_columns(self, table: str) -> set:
        """Retorna conjunto de nomes de colunas existentes para uma tabela SQLite."""
        if not self.conn or self.db_type != 'sqlite':
            return set()
        cols = set()
        try:
            cur = self.conn.cursor()
            cur.execute(f"PRAGMA table_info({table})")
            for row in cur.fetchall():
                # row format: cid, name, type, notnull, dflt_value, pk
                cols.add(row[1] if not isinstance(row, sqlite3.Row) else row["name"])
        except Exception:
            pass
        return cols

    def _ensure_sqlite_column(self, table: str, coldef: str):
        """Adiciona coluna se não existir. coldef deve conter 'nome TIPO'."""
        if not self.conn or self.db_type != 'sqlite':
            return
        try:
            col_name = coldef.split()[0]
            existing = self._get_sqlite_columns(table)
            if col_name not in existing:
                cur = self.conn.cursor()
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {coldef}")
                self.conn.commit()
        except Exception as e:
            # Não interrompe o app por falha de migração
            print(f"Falha ao adicionar coluna '{coldef}' em '{table}': {e}")

    def _migrate_sqlite_schema(self):
        """Garante que a tabela 'solicitacoes' possua todas as colunas usadas pelo app."""
        if not self.conn or self.db_type != 'sqlite':
            return
            
        # Verifica se existe a coluna problemática 'aplicacao'
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(solicitacoes)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Se existe 'aplicacao' mas não 'local_aplicacao', precisa recriar a tabela
        if 'aplicacao' in column_names and 'local_aplicacao' not in column_names:
            print("Recriando tabela solicitacoes com schema correto...")
            self._recreate_solicitacoes_table()
            return
            
        required_cols = [
            # Campos adicionados em versões recentes; todos opcionais (sem NOT NULL)
            "numero_pedido_compras INTEGER",
            "etapa_atual TEXT",
            "local_aplicacao TEXT",
            "carimbo_data_hora TEXT",
            "sla_dias INTEGER",
            "data_numero_pedido TEXT",
            "data_cotacao TEXT",
            "data_entrega TEXT",
            "dias_atendimento INTEGER",
            "sla_cumprido TEXT",
            "observacoes TEXT",
            "numero_requisicao_interno TEXT",
            "data_requisicao_interna TEXT",
            "responsavel_suprimentos TEXT",
            "valor_estimado REAL",
            "valor_final REAL",
            "fornecedor_recomendado TEXT",
            "fornecedor_final TEXT",
            "anexos_requisicao TEXT",
            "cotacoes TEXT",
            "aprovacoes TEXT",
            "historico_etapas TEXT",
            "itens TEXT",
        ]
        for coldef in required_cols:
            self._ensure_sqlite_column("solicitacoes", coldef)
    
    def _recreate_solicitacoes_table(self):
        """Recria a tabela solicitacoes com o schema correto"""
        cursor = self.conn.cursor()
        
        # Backup dos dados existentes
        cursor.execute("SELECT * FROM solicitacoes")
        existing_data = cursor.fetchall()
        
        # Remove tabela antiga
        cursor.execute("DROP TABLE IF EXISTS solicitacoes")
        
        # Cria tabela com schema correto
        cursor.execute('''
        CREATE TABLE solicitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_solicitacao_estoque INTEGER UNIQUE NOT NULL,
            numero_pedido_compras INTEGER,
            solicitante TEXT NOT NULL,
            departamento TEXT NOT NULL,
            descricao TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            local_aplicacao TEXT,
            status TEXT NOT NULL,
            etapa_atual TEXT,
            carimbo_data_hora TEXT,
            data_numero_pedido TEXT,
            data_cotacao TEXT,
            data_entrega TEXT,
            sla_dias INTEGER,
            dias_atendimento INTEGER,
            sla_cumprido TEXT,
            observacoes TEXT,
            numero_requisicao_interno TEXT,
            data_requisicao_interna TEXT,
            responsavel_suprimentos TEXT,
            valor_estimado REAL,
            valor_final REAL,
            fornecedor_recomendado TEXT,
            fornecedor_final TEXT,
            anexos_requisicao TEXT,
            cotacoes TEXT,
            aprovacoes TEXT,
            historico_etapas TEXT,
            itens TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()
        print("Tabela solicitacoes recriada com schema correto")
    
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
        if not self.db_available or not self.conn:
            return False
            
        cursor = self.conn.cursor()
        
        if not is_hashed:
            # Hash da senha se necessário
            import hashlib
            SALT = "ziran_local_salt_v1"
            senha_hash = hashlib.sha256((SALT + senha_hash).encode("utf-8")).hexdigest()
        
        try:
            sql = '''
            INSERT INTO usuarios (username, nome, perfil, departamento, senha_hash)
            VALUES (?, ?, ?, ?, ?)
            '''
            cursor.execute(self._sql(sql), (username, nome, perfil, departamento, senha_hash))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Usuário já existe
        except Exception:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Autentica usuário"""
        if not self.db_available or not self.conn:
            return {}
            
        try:
            import hashlib
            SALT = "ziran_local_salt_v1"
            senha_hash = hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()
            
            cursor = self.conn.cursor()
            sql = '''
            SELECT username, nome, perfil, departamento
            FROM usuarios 
            WHERE username = ? AND senha_hash = ?
            '''
            cursor.execute(self._sql(sql), (username, senha_hash))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}
        except Exception:
            return {}
    
    def authenticate_user_by_username(self, username: str) -> Dict:
        """Busca usuário apenas pelo username (para sessões)"""
        cursor = self.conn.cursor()
        sql = '''
        SELECT username, nome, perfil, departamento
        FROM usuarios 
        WHERE username = ?
        '''
        cursor.execute(self._sql(sql), (username,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {}
    
    def get_all_users(self) -> List[Dict]:
        """Retorna todos os usuários"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT username, nome, perfil, departamento FROM usuarios')
        return [dict(row) for row in cursor.fetchall()]
    
    def update_user_password(self, username: str, new_password: str) -> bool:
        """Atualiza a senha de um usuário existente."""
        if not self.db_available or not self.conn:
            return False
        try:
            import hashlib
            SALT = "ziran_local_salt_v1"
            senha_hash = hashlib.sha256((SALT + new_password).encode("utf-8")).hexdigest()
            cursor = self.conn.cursor()
            sql = '''
            UPDATE usuarios SET senha_hash = ? WHERE username = ?
            '''
            cursor.execute(self._sql(sql), (senha_hash, username))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
    
    def create_session(self, username: str, session_id: str, expires_hours=24):
        """Cria sessão persistente"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=expires_hours)
            
            if self.db_type == 'postgres':
                cursor.execute('''
                INSERT INTO sessoes (id, username, expires_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username, expires_at = EXCLUDED.expires_at
                ''', (session_id, username, expires_at))
            else:
                cursor.execute('''
                INSERT OR REPLACE INTO sessoes (id, username, expires_at)
                VALUES (?, ?, ?)
                ''', (session_id, username, expires_at))
            self.conn.commit()
            return True
        except Exception:
            return False
    
    def validate_session(self, session_id: str) -> str:
        """Valida sessão e retorna username"""
        cursor = self.conn.cursor()
        sql = '''
        SELECT username FROM sessoes 
        WHERE id = ? AND expires_at > CURRENT_TIMESTAMP
        '''
        cursor.execute(self._sql(sql), (session_id,))
        
        row = cursor.fetchone()
        return row['username'] if row else None
    
    def delete_session(self, session_id: str):
        """Remove sessão"""
        cursor = self.conn.cursor()
        sql = 'DELETE FROM sessoes WHERE id = ?'
        cursor.execute(self._sql(sql), (session_id,))
        self.conn.commit()
    
    def set_config(self, key: str, value: str):
        """Define configuração"""
        cursor = self.conn.cursor()
        if self.db_type == 'postgres':
            cursor.execute('''
            INSERT INTO configuracoes (chave, valor, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor, updated_at = CURRENT_TIMESTAMP
            ''', (key, value))
        else:
            cursor.execute('''
            INSERT OR REPLACE INTO configuracoes (chave, valor, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
        self.conn.commit()
    
    def get_config(self, key: str, default=None):
        """Obtém configuração"""
        cursor = self.conn.cursor()
        sql = 'SELECT valor FROM configuracoes WHERE chave = ?'
        cursor.execute(self._sql(sql), (key,))
        row = cursor.fetchone()
        return row['valor'] if row else default
    
    def add_solicitacao(self, solicitacao_data: Dict) -> bool:
        """Adiciona solicitação ao banco"""
        if not self.db_available or not self.conn:
            print("Banco de dados não disponível")
            return False
            
        try:
            # Garante colunas recentes em bases SQLite legadas antes do INSERT
            if self.db_type == 'sqlite':
                try:
                    self._migrate_sqlite_schema()
                except Exception:
                    pass
            cursor = self.conn.cursor()
            
            # Debug: mostra os dados recebidos
            print(f"Dados da solicitação: {list(solicitacao_data.keys())}")
            
            # Monta SQL alinhado ao esquema atual (SQLite/Postgres)
            sql = '''
            INSERT INTO solicitacoes (
                numero_solicitacao_estoque,
                numero_pedido_compras,
                solicitante,
                departamento,
                descricao,
                prioridade,
                local_aplicacao,
                status,
                etapa_atual,
                carimbo_data_hora,
                data_numero_pedido,
                data_cotacao,
                data_entrega,
                sla_dias,
                dias_atendimento,
                sla_cumprido,
                observacoes,
                numero_requisicao_interno,
                data_requisicao_interna,
                responsavel_suprimentos,
                valor_estimado,
                valor_final,
                fornecedor_recomendado,
                fornecedor_final,
                anexos_requisicao,
                cotacoes,
                aprovacoes,
                historico_etapas,
                itens
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            # Garante valores para colunas NOT NULL e serializa JSON
            values = (
                solicitacao_data.get('numero_solicitacao_estoque'),
                solicitacao_data.get('numero_pedido_compras'),
                solicitacao_data.get('solicitante', ''),
                solicitacao_data.get('departamento', ''),
                solicitacao_data.get('descricao', ''),
                solicitacao_data.get('prioridade', 'Normal'),
                solicitacao_data.get('local_aplicacao', ''),
                solicitacao_data.get('status', 'Solicitação'),
                solicitacao_data.get('etapa_atual', solicitacao_data.get('status', 'Solicitação')),
                solicitacao_data.get('carimbo_data_hora') or datetime.datetime.now().isoformat(),
                solicitacao_data.get('data_numero_pedido'),
                solicitacao_data.get('data_cotacao'),
                solicitacao_data.get('data_entrega'),
                solicitacao_data.get('sla_dias', 3),
                solicitacao_data.get('dias_atendimento'),
                solicitacao_data.get('sla_cumprido'),
                solicitacao_data.get('observacoes'),
                solicitacao_data.get('numero_requisicao_interno'),
                solicitacao_data.get('data_requisicao_interna'),
                solicitacao_data.get('responsavel_suprimentos'),
                solicitacao_data.get('valor_estimado'),
                solicitacao_data.get('valor_final'),
                solicitacao_data.get('fornecedor_recomendado'),
                solicitacao_data.get('fornecedor_final'),
                json.dumps(solicitacao_data.get('anexos_requisicao', [])),
                json.dumps(solicitacao_data.get('cotacoes', [])),
                json.dumps(solicitacao_data.get('aprovacoes', [])),
                json.dumps(solicitacao_data.get('historico_etapas', [])),
                json.dumps(solicitacao_data.get('itens', []))
            )
            
            print(f"Executando SQL com {len(values)} valores")
            cursor.execute(self._sql(sql), values)
            self.conn.commit()
            print("Solicitação salva com sucesso no banco")
            return True
            
        except Exception as e:
            print(f"Erro detalhado ao adicionar solicitação: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_all_solicitacoes(self) -> List[Dict]:
        """Retorna todas as solicitações"""
        if not self.db_available or not self.conn:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM solicitacoes ORDER BY numero_solicitacao_estoque DESC')
            rows = cursor.fetchall()
            
            solicitacoes = []
            for row in rows:
                sol = dict(row)
                
                # Mapeia campos do banco para estrutura esperada pelo app
                if 'data_criacao' in sol:
                    sol['carimbo_data_hora'] = sol['data_criacao']
                if 'anexos' in sol:
                    sol['anexos_requisicao'] = sol['anexos']
                
                # Adiciona campos que podem não existir no banco mas são esperados pelo app
                sol.setdefault('local_aplicacao', '')
                sol.setdefault('sla_dias', 3)
                sol.setdefault('dias_atendimento', None)
                sol.setdefault('numero_pedido_compras', None)
                sol.setdefault('data_numero_pedido', None)
                sol.setdefault('data_cotacao', None)
                sol.setdefault('data_entrega', None)
                sol.setdefault('observacoes', None)
                sol.setdefault('numero_requisicao_interno', None)
                sol.setdefault('data_requisicao_interna', None)
                sol.setdefault('responsavel_suprimentos', None)
                sol.setdefault('itens', [])
                
                # Converte campos JSON de volta para objetos Python
                json_fields = ['anexos_requisicao', 'anexos', 'cotacoes', 'aprovacoes', 'historico_etapas', 'itens']
                for field in json_fields:
                    if field in sol:
                        try:
                            if isinstance(sol[field], str):
                                sol[field] = json.loads(sol[field] or '[]')
                        except:
                            sol[field] = []
                
                solicitacoes.append(sol)
            return solicitacoes
        except Exception as e:
            print(f"Erro ao buscar solicitações: {e}")
            return []
    
    def update_solicitacao(self, numero_solicitacao: int, updates: Dict) -> bool:
        """Atualiza solicitação específica"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            # Garante colunas recentes em bases SQLite legadas antes do UPDATE
            if self.db_type == 'sqlite':
                try:
                    self._migrate_sqlite_schema()
                except Exception:
                    pass
            cursor = self.conn.cursor()
            
            # Constrói query dinâmica baseada nos campos a atualizar
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                if field in ['anexos_requisicao', 'cotacoes', 'aprovacoes', 'historico_etapas', 'itens']:
                    set_clauses.append(f"{field} = ?")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            values.append(numero_solicitacao)
            
            sql = f'''
            UPDATE solicitacoes 
            SET {', '.join(set_clauses)}
            WHERE numero_solicitacao_estoque = ?
            '''
            
            cursor.execute(self._sql(sql), values)
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar solicitação: {e}")
            return False
    
    def get_solicitacao_by_numero(self, numero: int) -> Dict:
        """Busca solicitação por número"""
        if not self.db_available or not self.conn:
            return {}
            
        try:
            cursor = self.conn.cursor()
            sql = 'SELECT * FROM solicitacoes WHERE numero_solicitacao_estoque = ?'
            cursor.execute(self._sql(sql), (numero,))
            row = cursor.fetchone()
            
            if row:
                sol = dict(row)
                # Converte campos JSON
                for field in ['anexos_requisicao', 'cotacoes', 'aprovacoes', 'historico_etapas', 'itens']:
                    try:
                        sol[field] = json.loads(sol[field] or '[]')
                    except:
                        sol[field] = []
                return sol
            return {}
        except Exception as e:
            print(f"Erro ao buscar solicitação: {e}")
            return {}
    
    def add_catalogo_produto(self, codigo: str, nome: str, categoria: str, unidade: str, ativo: bool = True) -> bool:
        """Adiciona produto ao catálogo"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            sql = '''
            INSERT INTO catalogo_produtos (codigo, nome, categoria, unidade, ativo)
            VALUES (?, ?, ?, ?, ?)
            '''
            cursor.execute(self._sql(sql), (codigo, nome, categoria, unidade, ativo))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao adicionar produto: {e}")
            return False
    
    def get_catalogo_produtos(self) -> List[Dict]:
        """Retorna todos os produtos do catálogo"""
        if not self.db_available or not self.conn:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM catalogo_produtos ORDER BY codigo')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar catálogo: {e}")
            return []
    
    def update_catalogo_produtos(self, produtos: List[Dict]) -> bool:
        """Atualiza catálogo completo de produtos"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            # Limpa catálogo atual
            cursor.execute('DELETE FROM catalogo_produtos')
            
            # Insere novos produtos
            for produto in produtos:
                sql = '''
                INSERT INTO catalogo_produtos (codigo, nome, categoria, unidade, ativo)
                VALUES (?, ?, ?, ?, ?)
                '''
                cursor.execute(self._sql(sql), (
                    produto.get('codigo'),
                    produto.get('nome'),
                    produto.get('categoria', ''),
                    produto.get('unidade'),
                    produto.get('ativo', True)
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao atualizar catálogo: {e}")
            return False
    
    def add_notificacao(self, perfil: str, numero: int, mensagem: str) -> bool:
        """Adiciona notificação"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            sql = '''
            INSERT INTO notificacoes (perfil, numero, mensagem, data, lida)
            VALUES (?, ?, ?, ?, ?)
            '''
            cursor.execute(self._sql(sql), (perfil, numero, mensagem, datetime.datetime.now().isoformat(), False))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao adicionar notificação: {e}")
            return False
    
    def get_notificacoes(self, perfil: str = None) -> List[Dict]:
        """Retorna notificações"""
        if not self.db_available or not self.conn:
            return []
            
        try:
            cursor = self.conn.cursor()
            if perfil:
                sql = 'SELECT * FROM notificacoes WHERE perfil = ? ORDER BY data DESC'
                cursor.execute(self._sql(sql), (perfil,))
            else:
                cursor.execute('SELECT * FROM notificacoes ORDER BY data DESC')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar notificações: {e}")
            return []
    
    def add_movimentacao(self, numero_solicitacao: int, etapa_origem: str, etapa_destino: str, usuario: str, observacoes: str = None) -> bool:
        """Adiciona movimentação ao histórico"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            sql = '''
            INSERT INTO movimentacoes (numero_solicitacao, etapa_origem, etapa_destino, usuario, observacoes)
            VALUES (?, ?, ?, ?, ?)
            '''
            cursor.execute(self._sql(sql), (numero_solicitacao, etapa_origem, etapa_destino, usuario, observacoes))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao adicionar movimentação: {e}")
            return False

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
            # Preferir explicitamente quando houver credenciais
            try:
                if hasattr(st, 'secrets') and 'postgres' in st.secrets:
                    use_cloud_db = True
                elif hasattr(st, 'secrets') and 'database' in st.secrets:
                    use_cloud_db = True
                elif hasattr(st, 'secrets') and 'postgres_url' in st.secrets:
                    use_cloud_db = True
                elif hasattr(st, 'secrets') and 'database_url' in st.secrets:
                    use_cloud_db = True
                elif os.getenv('DATABASE_URL'):
                    use_cloud_db = True
                else:
                    use_cloud_db = os.getenv('STREAMLIT_SHARING_MODE') == 'true' or 'streamlit.app' in os.getenv('HOSTNAME', '')
            except Exception:
                use_cloud_db = False
        
        _db_instance = DatabaseManager(use_cloud_db)
    
    return _db_instance
