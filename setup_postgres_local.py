#!/usr/bin/env python3
"""
Script de setup para PostgreSQL local na EC2
Cria o banco de dados e todas as tabelas necessárias
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import json
import datetime
import sys
import os

# Configurações padrão
DEFAULT_CONFIG = {
    'host': 'localhost',
    'database': 'sistema_compras',
    'username': 'postgres',
    'password': 'postgres123',
    'port': 5432
}

def create_database_if_not_exists(config):
    """Cria o banco de dados se não existir"""
    try:
        # Conecta ao banco postgres padrão para criar o banco sistema_compras
        temp_config = config.copy()
        temp_config['database'] = 'postgres'
        
        conn = psycopg2.connect(
            host=temp_config['host'],
            database=temp_config['database'],
            user=temp_config['username'],
            password=temp_config['password'],
            port=temp_config['port']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verifica se o banco já existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (config['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {config['database']}")
            print(f"✅ Banco de dados '{config['database']}' criado com sucesso")
        else:
            print(f"ℹ️  Banco de dados '{config['database']}' já existe")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar banco de dados: {e}")
        return False

def setup_database(config):
    """Configura o banco de dados completo"""
    try:
        # Conecta ao banco sistema_compras
        conn = psycopg2.connect(
            host=config['host'],
            database=config['database'],
            user=config['username'],
            password=config['password'],
            port=config['port'],
            cursor_factory=RealDictCursor
        )
        
        cursor = conn.cursor()
        
        print("🔧 Criando tabelas...")
        
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

        # Tabela de solicitações com schema completo
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
            anexos_requisicao TEXT,
            cotacoes TEXT,
            aprovacoes TEXT,
            historico_etapas TEXT,
            itens TEXT,
            -- Campos adicionais para 8 etapas
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
        
        # Tabela de movimentações
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

        # Tabela de sessões
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        print("✅ Tabelas criadas com sucesso")
        
        # Criar índices para performance
        print("🔧 Criando índices de performance...")
        indices = [
            'CREATE INDEX IF NOT EXISTS idx_solicitacoes_numero ON solicitacoes(numero_solicitacao_estoque)',
            'CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes(status)',
            'CREATE INDEX IF NOT EXISTS idx_solicitacoes_solicitante ON solicitacoes(solicitante)',
            'CREATE INDEX IF NOT EXISTS idx_solicitacoes_departamento ON solicitacoes(departamento)',
            'CREATE INDEX IF NOT EXISTS idx_solicitacoes_prioridade ON solicitacoes(prioridade)',
            'CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)',
            'CREATE INDEX IF NOT EXISTS idx_sessoes_expires ON sessoes(expires_at)',
            'CREATE INDEX IF NOT EXISTS idx_movimentacoes_numero ON movimentacoes(numero_solicitacao)',
            'CREATE INDEX IF NOT EXISTS idx_notificacoes_perfil ON notificacoes(perfil)'
        ]
        
        for indice in indices:
            cursor.execute(indice)
        
        print("✅ Índices criados com sucesso")
        
        # Inserir usuários padrão
        print("🔧 Inserindo usuários padrão...")
        usuarios_padrao = [
            ('admin', 'Administrador', 'admin', 'TI', 'admin123'),
            ('Leonardo.Fragoso', 'Leonardo Fragoso', 'solicitante', 'TI', 'Teste123'),
            ('Genival.Silva', 'Genival Silva', 'solicitante', 'Operações', 'Teste123'),
            ('Diretoria', 'Diretoria', 'aprovador', 'Diretoria', 'Teste123'),
            ('Fabio.Ramos', 'Fábio Ramos', 'suprimentos', 'Suprimentos', 'Teste123')
        ]
        
        for username, nome, perfil, departamento, senha in usuarios_padrao:
            try:
                senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                cursor.execute('''
                INSERT INTO usuarios (username, nome, perfil, departamento, senha_hash)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                ''', (username, nome, perfil, departamento, senha_hash))
            except Exception as e:
                print(f"⚠️  Usuário {username} já existe ou erro: {e}")
        
        print("✅ Usuários padrão inseridos")
        
        # Inserir configurações padrão
        print("🔧 Inserindo configurações padrão...")
        configuracoes_padrao = [
            ('sla_urgente', '1'),
            ('sla_alta', '3'),
            ('sla_normal', '5'),
            ('sla_baixa', '7'),
            ('empresa_nome', 'Sistema de Compras'),
            ('sistema_versao', '2.0'),
            ('max_upload_size', '10485760')  # 10MB
        ]
        
        for chave, valor in configuracoes_padrao:
            cursor.execute('''
            INSERT INTO configuracoes (chave, valor)
            VALUES (%s, %s)
            ON CONFLICT (chave) DO NOTHING
            ''', (chave, valor))
        
        print("✅ Configurações padrão inseridas")
        
        # Inserir produtos padrão no catálogo
        print("🔧 Inserindo catálogo de produtos padrão...")
        produtos_padrao = [
            ('MAT001', 'Material de Escritório', 'Escritório', 'UN'),
            ('EPI001', 'Equipamento de Proteção Individual', 'Segurança', 'UN'),
            ('FERRA001', 'Ferramentas Diversas', 'Ferramentas', 'UN'),
            ('CONS001', 'Material de Construção', 'Construção', 'UN'),
            ('INFO001', 'Equipamento de Informática', 'Informática', 'UN')
        ]
        
        for codigo, nome, categoria, unidade in produtos_padrao:
            cursor.execute('''
            INSERT INTO catalogo_produtos (codigo, nome, categoria, unidade)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (codigo) DO NOTHING
            ''', (codigo, nome, categoria, unidade))
        
        print("✅ Catálogo de produtos inserido")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 Setup do PostgreSQL local concluído com sucesso!")
        print("\n📋 Credenciais de acesso:")
        print("- admin / admin123 (Administrador)")
        print("- Leonardo.Fragoso / Teste123 (Solicitante)")
        print("- Genival.Silva / Teste123 (Solicitante)")
        print("- Diretoria / Teste123 (Aprovador)")
        print("- Fabio.Ramos / Teste123 (Suprimentos)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o setup: {e}")
        return False

def test_connection(config):
    """Testa a conexão com o banco"""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            database=config['database'],
            user=config['username'],
            password=config['password'],
            port=config['port']
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"✅ Conexão testada com sucesso!")
        print(f"📊 PostgreSQL: {version}")
        return True
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Iniciando setup do PostgreSQL local para Sistema de Compras")
    print("=" * 60)
    
    # Usar configuração padrão ou solicitar do usuário
    config = DEFAULT_CONFIG.copy()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        print("\n📝 Configuração interativa:")
        config['host'] = input(f"Host [{config['host']}]: ") or config['host']
        config['database'] = input(f"Database [{config['database']}]: ") or config['database']
        config['username'] = input(f"Username [{config['username']}]: ") or config['username']
        config['password'] = input(f"Password [{config['password']}]: ") or config['password']
        config['port'] = int(input(f"Port [{config['port']}]: ") or config['port'])
    
    print(f"\n🔧 Configuração:")
    print(f"   Host: {config['host']}")
    print(f"   Database: {config['database']}")
    print(f"   Username: {config['username']}")
    print(f"   Port: {config['port']}")
    
    # Criar banco de dados
    if not create_database_if_not_exists(config):
        print("❌ Falha ao criar banco de dados")
        sys.exit(1)
    
    # Setup completo
    if not setup_database(config):
        print("❌ Falha no setup do banco")
        sys.exit(1)
    
    # Teste final
    if not test_connection(config):
        print("❌ Falha no teste de conexão")
        sys.exit(1)
    
    # Criar arquivo de configuração
    config_content = f"""[postgres]
host = "{config['host']}"
database = "{config['database']}"
username = "{config['username']}"
password = "{config['password']}"
port = {config['port']}

[database]
url = "postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
"""
    
    with open('secrets_local.toml', 'w') as f:
        f.write(config_content)
    
    print(f"\n✅ Arquivo de configuração 'secrets_local.toml' criado")
    print("\n🎯 Próximos passos:")
    print("1. Instalar PostgreSQL na EC2 se ainda não instalado")
    print("2. Executar este script na EC2: python setup_postgres_local.py")
    print("3. Atualizar app.py para usar database_local.py")
    print("4. Testar a aplicação localmente")
    
    print("\n✨ Setup concluído com sucesso!")

if __name__ == "__main__":
    main()
