#!/usr/bin/env python3
"""
Setup PostgreSQL local para Windows - Cria banco e usuários com autenticação consistente
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import toml
import os

# Configuração de autenticação consistente
SALT = "ziran_local_salt_v1"

def hash_password_with_salt(password: str) -> str:
    """Hash com salt (método consistente)"""
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()

def get_db_connection():
    """Conecta ao PostgreSQL local"""
    try:
        # Tenta carregar configuração do arquivo secrets_local.toml
        config_path = 'secrets_local.toml'
        if os.path.exists(config_path):
            config = toml.load(config_path)
            if 'postgres' in config:
                pg = config['postgres']
                conn = psycopg2.connect(
                    host=pg["host"],
                    database=pg["database"],
                    user=pg["username"],
                    password=pg["password"],
                    port=int(pg.get("port", 5432)),
                    cursor_factory=RealDictCursor,
                )
                return conn
        
        # Fallback para configuração padrão
        conn = psycopg2.connect(
            host="localhost",
            database="sistema_compras",
            user="postgres",
            password="postgres123",
            port=5432,
            cursor_factory=RealDictCursor,
        )
        return conn
        
    except Exception as e:
        print(f"❌ Erro ao conectar PostgreSQL: {e}")
        return None

def create_database():
    """Cria o banco de dados se não existir"""
    print("🔧 CRIANDO BANCO DE DADOS")
    print("=" * 30)
    
    try:
        # Conecta ao postgres padrão para criar o banco
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="postgres123",
            port=5432
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verifica se banco existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'sistema_compras'")
        if cursor.fetchone():
            print("✅ Banco 'sistema_compras' já existe")
        else:
            cursor.execute("CREATE DATABASE sistema_compras")
            print("✅ Banco 'sistema_compras' criado")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")
        return False

def setup_tables():
    """Cria todas as tabelas necessárias"""
    print("\n🔧 CRIANDO TABELAS")
    print("=" * 20)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
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
        print("✅ Tabela usuarios criada")

        # Tabela de solicitações (sem coluna duplicada)
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
        print("✅ Tabela solicitacoes criada")

        # Outras tabelas necessárias
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            id SERIAL PRIMARY KEY,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("✅ Tabela configuracoes criada")
        
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
        print("✅ Tabela catalogo_produtos criada")
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("✅ Tabela sessoes criada")

        # Criar índices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_numero ON solicitacoes(numero_solicitacao_estoque)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)')
        print("✅ Índices criados")

        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def create_default_users():
    """Cria usuários padrão com senhas corretas"""
    print("\n👥 CRIANDO USUÁRIOS PADRÃO")
    print("=" * 30)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    default_users = [
        {"username": "admin", "nome": "Administrador", "perfil": "Admin", "departamento": "TI", "senha": "admin123"},
        {"username": "Leonardo.Fragoso", "nome": "Leonardo Fragoso", "perfil": "Solicitante", "departamento": "TI", "senha": "Teste123"},
        {"username": "Genival.Silva", "nome": "Genival Silva", "perfil": "Solicitante", "departamento": "Operações", "senha": "Teste123"},
        {"username": "Diretoria", "nome": "Diretoria", "perfil": "Gerência&Diretoria", "departamento": "Diretoria", "senha": "Teste123"},
        {"username": "Fabio.Ramos", "nome": "Fabio Ramos", "perfil": "Suprimentos", "departamento": "Suprimentos", "senha": "Teste123"},
        {"username": "Estoque.Sistema", "nome": "Estoque Sistema", "perfil": "Estoque", "departamento": "Estoque", "senha": "Teste123"},
    ]
    
    try:
        cursor = conn.cursor()
        created_count = 0
        
        for user_data in default_users:
            # Verifica se usuário já existe
            cursor.execute('SELECT username FROM usuarios WHERE username = %s', (user_data["username"],))
            if cursor.fetchone():
                print(f"⚠️  Usuário {user_data['username']} já existe")
                continue
            
            # Cria usuário com hash correto (com salt)
            senha_hash = hash_password_with_salt(user_data["senha"])
            
            cursor.execute('''
                INSERT INTO usuarios (username, nome, perfil, departamento, senha_hash)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                user_data["username"],
                user_data["nome"],
                user_data["perfil"],
                user_data["departamento"],
                senha_hash
            ))
            
            print(f"✅ Usuário {user_data['username']} criado")
            created_count += 1
        
        conn.commit()
        conn.close()
        
        if created_count > 0:
            print(f"\n✅ {created_count} usuários criados com sucesso")
        else:
            print("\n✅ Todos os usuários já existem")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar usuários: {e}")
        return False

def test_authentication():
    """Testa autenticação dos usuários"""
    print("\n🧪 TESTANDO AUTENTICAÇÃO")
    print("=" * 30)
    
    from database_local import get_local_database
    
    try:
        db = get_local_database()
        
        if not db.db_available:
            print("❌ Banco não disponível")
            return False
        
        test_credentials = [
            ("admin", "admin123"),
            ("Leonardo.Fragoso", "Teste123"),
            ("Genival.Silva", "Teste123"),
        ]
        
        all_working = True
        
        for username, password in test_credentials:
            result = db.authenticate_user(username, password)
            if result:
                print(f"✅ {username}: Autenticação OK")
            else:
                print(f"❌ {username}: Falha na autenticação")
                all_working = False
        
        return all_working
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    print("🔧 SETUP POSTGRESQL LOCAL - WINDOWS")
    print("=" * 50)
    
    # 1. Criar banco de dados
    if not create_database():
        print("❌ Falha ao criar banco de dados")
        return
    
    # 2. Criar tabelas
    if not setup_tables():
        print("❌ Falha ao criar tabelas")
        return
    
    # 3. Criar usuários padrão
    if not create_default_users():
        print("❌ Falha ao criar usuários")
        return
    
    # 4. Testar autenticação
    if test_authentication():
        print("\n🎉 SETUP CONCLUÍDO COM SUCESSO!")
        print("\n📋 CREDENCIAIS DE ACESSO:")
        print("  admin / admin123")
        print("  Leonardo.Fragoso / Teste123")
        print("  Genival.Silva / Teste123")
        print("  Diretoria / Teste123")
        print("  Fabio.Ramos / Teste123")
        print("  Estoque.Sistema / Teste123")
        print("\n🌐 Execute: streamlit run app.py")
    else:
        print("\n⚠️  Setup concluído mas com problemas de autenticação")

if __name__ == "__main__":
    main()
