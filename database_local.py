import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import hashlib
from typing import Dict, List
import datetime
import toml

class LocalDatabaseManager:
    """Gerenciador de banco PostgreSQL local para EC2"""
    
    def __init__(self):
        self.db_type = 'postgres'
        self.db_available = False
        self.conn = None
        self.setup_local_postgres()
    
    def setup_local_postgres(self):
        """Configura conexão PostgreSQL local"""
        try:
            # Tenta carregar configuração do arquivo secrets_local.toml
            config_path = 'secrets_local.toml'
            if os.path.exists(config_path):
                config = toml.load(config_path)
                if 'postgres' in config:
                    pg = config['postgres']
                    self.conn = psycopg2.connect(
                        host=pg["host"],
                        database=pg["database"],
                        user=pg["username"],
                        password=pg["password"],
                        port=int(pg.get("port", 5432)),
                        cursor_factory=RealDictCursor,
                    )
                elif 'database' in config and 'url' in config['database']:
                    self.conn = psycopg2.connect(config['database']['url'], cursor_factory=RealDictCursor)
            else:
                # Fallback para variáveis de ambiente
                db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres123@localhost:5432/sistema_compras')
                self.conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
            
            if self.conn:
                self.create_tables()
                self.db_available = True
                print("✅ PostgreSQL local conectado com sucesso")
                
        except Exception as e:
            print(f"❌ Erro ao conectar PostgreSQL local: {e}")
            self.db_available = False
            self.conn = None
    
    def create_tables(self):
        """Cria todas as tabelas necessárias"""
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

        # Tabela de solicitações com schema completo incluindo Requisição
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id SERIAL PRIMARY KEY,
            numero_solicitacao_estoque INTEGER UNIQUE NOT NULL,
            numero_requisicao INTEGER,
            numero_pedido_compras INTEGER,
            solicitante TEXT NOT NULL,
            departamento TEXT NOT NULL,
            descricao TEXT NOT NULL,
            prioridade TEXT NOT NULL,
            local_aplicacao TEXT NOT NULL,
            status TEXT NOT NULL,
            etapa_atual TEXT NOT NULL,
            carimbo_data_hora TEXT NOT NULL,
            data_requisicao TEXT,
            responsavel_estoque TEXT,
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
            anexos_requisicao TEXT,
            cotacoes TEXT,
            aprovacoes TEXT,
            historico_etapas TEXT,
            itens TEXT,
            -- Campos adicionais para fluxo completo
            data_entrega_prevista TEXT,
            data_entrega_real TEXT,
            entrega_conforme TEXT,
            nota_fiscal TEXT,
            responsavel_recebimento TEXT,
            observacoes_entrega TEXT,
            observacoes_finalizacao TEXT,
            data_finalizacao TEXT,
            tipo_solicitacao TEXT,
            justificativa TEXT,
            observacoes_requisicao TEXT,
            observacoes_pedido_compras TEXT,
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
        
        # Tabela de auditoria para ações do Admin
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS auditoria_admin (
            id SERIAL PRIMARY KEY,
            usuario TEXT NOT NULL,
            acao TEXT NOT NULL,
            modulo TEXT NOT NULL,
            detalhes TEXT,
            solicitacao_id INTEGER,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

        # Criar índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_numero ON solicitacoes(numero_solicitacao_estoque)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_solicitante ON solicitacoes(solicitante)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessoes_expires ON sessoes(expires_at)')

        self.conn.commit()
        print("✅ Todas as tabelas criadas com sucesso")
    
    def add_user(self, username: str, nome: str, perfil: str, departamento: str, senha_hash: str, is_hashed=False):
        """Adiciona usuário ao banco"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            if not is_hashed:
                senha_hash = hashlib.sha256(senha_hash.encode()).hexdigest()
            
            sql = '''
            INSERT INTO usuarios (username, nome, perfil, departamento, senha_hash)
            VALUES (%s, %s, %s, %s, %s)
            '''
            cursor.execute(sql, (username, nome, perfil, departamento, senha_hash))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao adicionar usuário: {e}")
            return False
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Autentica usuário e retorna dados se válido"""
        if not self.db_available or not self.conn:
            return {}
            
        try:
            cursor = self.conn.cursor()
            sql = 'SELECT * FROM usuarios WHERE username = %s'
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
            
            if user:
                user_dict = dict(user)
                stored_hash = user_dict.get('senha_hash', '')
                senha_hash = hashlib.sha256(password.encode()).hexdigest()
                
                if stored_hash == senha_hash:
                    return user_dict
            return {}
        except Exception as e:
            print(f"Erro ao autenticar usuário: {e}")
            return {}
    
    def get_all_users(self) -> List[Dict]:
        """Retorna todos os usuários"""
        if not self.db_available or not self.conn:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM usuarios ORDER BY username')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar usuários: {e}")
            return []
    
    def update_user_password(self, username: str, nova_senha: str) -> bool:
        """Atualiza senha do usuário"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
            sql = 'UPDATE usuarios SET senha_hash = %s WHERE username = %s'
            cursor.execute(sql, (senha_hash, username))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao atualizar senha: {e}")
            return False
    
    def get_config(self, key: str, default: str = None) -> str:
        """Busca configuração"""
        if not self.db_available or not self.conn:
            return default
            
        try:
            cursor = self.conn.cursor()
            sql = 'SELECT valor FROM configuracoes WHERE chave = %s'
            cursor.execute(sql, (key,))
            result = cursor.fetchone()
            return result[0] if result else default
        except Exception as e:
            return default
    
    def set_config(self, key: str, value: str) -> bool:
        """Define configuração"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            sql = '''INSERT INTO configuracoes (chave, valor) VALUES (%s, %s) 
                    ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor'''
            cursor.execute(sql, (key, value))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao definir configuração: {e}")
            return False
    
    def add_solicitacao(self, solicitacao_data: Dict) -> bool:
        """Adiciona nova solicitação"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            sql = '''
            INSERT INTO solicitacoes (
                numero_solicitacao_estoque, numero_pedido_compras, solicitante, departamento,
                descricao, prioridade, local_aplicacao, status, etapa_atual, carimbo_data_hora,
                data_numero_pedido, data_cotacao, data_entrega, sla_dias, dias_atendimento,
                sla_cumprido, observacoes, numero_requisicao_interno, data_requisicao_interna,
                responsavel_suprimentos, valor_estimado, valor_final, fornecedor_recomendado,
                fornecedor_final, anexos_requisicao, cotacoes, aprovacoes, historico_etapas, itens,
                data_entrega_prevista, data_entrega_real, entrega_conforme, nota_fiscal,
                responsavel_recebimento, observacoes_entrega, observacoes_finalizacao,
                data_finalizacao, tipo_solicitacao, justificativa
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            
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
                json.dumps(solicitacao_data.get('itens', [])),
                solicitacao_data.get('data_entrega_prevista'),
                solicitacao_data.get('data_entrega_real'),
                solicitacao_data.get('entrega_conforme'),
                solicitacao_data.get('nota_fiscal'),
                solicitacao_data.get('responsavel_recebimento'),
                solicitacao_data.get('observacoes_entrega'),
                solicitacao_data.get('observacoes_finalizacao'),
                solicitacao_data.get('data_finalizacao'),
                solicitacao_data.get('tipo_solicitacao'),
                solicitacao_data.get('justificativa')
            )
            
            cursor.execute(sql, values)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao salvar solicitação: {e}")
            return False
    
    def get_all_solicitacoes(self) -> List[Dict]:
        """Retorna todas as solicitações"""
        if not self.db_available or not self.conn:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM solicitacoes ORDER BY numero_solicitacao_estoque DESC')
            solicitacoes = []
            for row in cursor.fetchall():
                sol = dict(row)
                # Deserializa campos JSON
                for field in ['anexos_requisicao', 'cotacoes', 'aprovacoes', 'historico_etapas', 'itens']:
                    try:
                        if sol.get(field):
                            sol[field] = json.loads(sol[field])
                        else:
                            sol[field] = []
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
            cursor = self.conn.cursor()
            
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                if field in ['anexos_requisicao', 'cotacoes', 'aprovacoes', 'historico_etapas', 'itens']:
                    set_clauses.append(f"{field} = %s")
                    values.append(json.dumps(value))
                else:
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
            
            values.append(numero_solicitacao)
            
            sql = f'''
            UPDATE solicitacoes 
            SET {', '.join(set_clauses)}
            WHERE numero_solicitacao_estoque = %s
            '''
            
            cursor.execute(sql, values)
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao atualizar solicitação: {e}")
            return False
    
    def get_solicitacao_by_numero(self, numero: int) -> Dict:
        """Busca solicitação por número"""
        if not self.db_available or not self.conn:
            return {}
            
        try:
            cursor = self.conn.cursor()
            sql = 'SELECT * FROM solicitacoes WHERE numero_solicitacao_estoque = %s'
            cursor.execute(sql, (numero,))
            row = cursor.fetchone()
            if row:
                sol = dict(row)
                # Deserializa campos JSON
                for field in ['anexos_requisicao', 'cotacoes', 'aprovacoes', 'historico_etapas', 'itens']:
                    try:
                        if sol.get(field):
                            sol[field] = json.loads(sol[field])
                        else:
                            sol[field] = []
                    except:
                        sol[field] = []
                return sol
            return {}
        except Exception as e:
            print(f"Erro ao buscar solicitação: {e}")
            return {}
    
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
            cursor.execute('DELETE FROM catalogo_produtos')
            
            for produto in produtos:
                sql = '''
                INSERT INTO catalogo_produtos (codigo, nome, categoria, unidade, ativo)
                VALUES (%s, %s, %s, %s, %s)
                '''
                cursor.execute(sql, (
                    produto.get('codigo'),
                    produto.get('nome'),
                    produto.get('categoria', ''),
                    produto.get('unidade'),
                    produto.get('ativo', True)
                ))
            
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao atualizar catálogo: {e}")
            return False
    
    def create_session(self, username: str, session_id: str) -> bool:
        """Cria nova sessão"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=24)
            
            sql = '''INSERT INTO sessoes (id, username, expires_at) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET 
                    username = EXCLUDED.username,
                    expires_at = EXCLUDED.expires_at'''
            cursor.execute(sql, (session_id, username, expires_at))
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao criar sessão: {e}")
            return False
    
    def validate_session(self, session_id: str) -> str:
        """Valida sessão e retorna username se válida"""
        if not self.db_available or not self.conn:
            return ""
            
        try:
            cursor = self.conn.cursor()
            sql = 'SELECT * FROM sessoes WHERE id = %s'
            cursor.execute(sql, (session_id,))
            session = cursor.fetchone()
            
            if session:
                session_dict = dict(session)
                expires_at = session_dict.get('expires_at')
                if expires_at and datetime.datetime.now() < expires_at:
                    return session_dict.get('username', '')
            return ""
        except Exception as e:
            print(f"Erro ao validar sessão: {e}")
            return ""
    
    def get_next_numero_requisicao(self) -> int:
        """Retorna próximo número de requisição disponível"""
        if not self.db_available or not self.conn:
            return 1
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT MAX(numero_requisicao) FROM solicitacoes WHERE numero_requisicao IS NOT NULL')
            result = cursor.fetchone()
            max_num = result[0] if result and result[0] else 0
            return max_num + 1
        except Exception as e:
            print(f"Erro ao buscar próximo número de requisição: {e}")
            return 1
    
    def get_next_numero_pedido(self) -> int:
        """Retorna próximo número de pedido de compras disponível"""
        if not self.db_available or not self.conn:
            return 1
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT MAX(numero_pedido_compras) FROM solicitacoes WHERE numero_pedido_compras IS NOT NULL')
            result = cursor.fetchone()
            max_num = result[0] if result and result[0] else 0
            return max_num + 1
        except Exception as e:
            print(f"Erro ao buscar próximo número de pedido: {e}")
            return 1
    
    def log_admin_action(self, usuario: str, acao: str, modulo: str, detalhes: str = None, solicitacao_id: int = None, ip_address: str = None):
        """Registra ação do Admin para auditoria"""
        if not self.db_available or not self.conn:
            return False
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO auditoria_admin (usuario, acao, modulo, detalhes, solicitacao_id, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (usuario, acao, modulo, detalhes, solicitacao_id, ip_address))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao registrar log de auditoria: {e}")
            return False
    
    def get_admin_audit_logs(self, limit: int = 100, offset: int = 0):
        """Recupera logs de auditoria do Admin"""
        if not self.db_available or not self.conn:
            return []
            
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM auditoria_admin 
                ORDER BY timestamp DESC 
                LIMIT %s OFFSET %s
            ''', (limit, offset))
            return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao buscar logs de auditoria: {e}")
            return []
    
    def close(self):
        """Fecha conexão"""
        if self.conn:
            self.conn.close()

# Singleton para gerenciar instância única
_local_db_instance = None

def get_local_database():
    """Retorna instância única do banco local"""
    global _local_db_instance
    
    if _local_db_instance is None:
        _local_db_instance = LocalDatabaseManager()
    
    return _local_db_instance
