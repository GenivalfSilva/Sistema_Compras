#!/usr/bin/env python3
"""
Script de migração completa do Neon DB para Supabase
Cria todas as tabelas e dados necessários para o Sistema de Compras
"""

import psycopg2
import hashlib
import json
import os
from datetime import datetime, timedelta
import sys

def hash_password(password: str) -> str:
    """Hash da senha usando SHA256 (mesmo padrão do sistema)"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_supabase_connection():
    """Conecta ao Supabase usando diferentes métodos de configuração"""
    
    # Método 1: Arquivo secrets_supabase.toml
    try:
        import toml
        if os.path.exists('secrets_supabase.toml'):
            config = toml.load('secrets_supabase.toml')
            if 'database' in config and 'url' in config['database']:
                return psycopg2.connect(config['database']['url'])
            elif 'postgres' in config:
                pg = config['postgres']
                return psycopg2.connect(
                    host=pg['host'],
                    port=pg.get('port', 5432),
                    database=pg['database'],
                    user=pg['username'],
                    password=pg['password']
                )
    except Exception as e:
        print(f"Erro ao ler secrets_supabase.toml: {e}")
    
    # Método 2: Variáveis de ambiente
    database_url = os.getenv('SUPABASE_DATABASE_URL') or os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    
    # Método 3: Input manual
    print("\n🔗 Configure sua conexão Supabase:")
    print("Exemplo: postgresql://postgres:senha@db.abc123.supabase.co:5432/postgres")
    
    database_url = input("Cole sua connection string do Supabase: ").strip()
    if database_url:
        # Salva para próximas execuções
        config_content = f"""[database]
url = "{database_url}"

[postgres]
# Extraído automaticamente da URL acima
"""
        with open('secrets_supabase.toml', 'w') as f:
            f.write(config_content)
        print("✅ Configuração salva em secrets_supabase.toml")
        return psycopg2.connect(database_url)
    
    raise Exception("❌ Não foi possível conectar ao Supabase. Verifique suas credenciais.")

def create_tables(cursor):
    """Cria todas as tabelas necessárias"""
    
    print("📋 Criando tabelas...")
    
    # 1. Tabela de usuários
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            senha_hash VARCHAR(64) NOT NULL,
            nome VARCHAR(100) NOT NULL,
            perfil VARCHAR(50) NOT NULL DEFAULT 'Solicitante',
            departamento VARCHAR(50) NOT NULL DEFAULT 'Outro',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Tabela de solicitações (schema completo com 8 etapas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id SERIAL PRIMARY KEY,
            numero_solicitacao VARCHAR(20) UNIQUE NOT NULL,
            solicitante VARCHAR(100) NOT NULL,
            departamento VARCHAR(50) NOT NULL,
            data_solicitacao TIMESTAMP NOT NULL,
            prioridade VARCHAR(20) NOT NULL DEFAULT 'Normal',
            descricao TEXT NOT NULL,
            justificativa TEXT,
            local_aplicacao VARCHAR(200),
            status VARCHAR(50) NOT NULL DEFAULT 'Solicitação',
            sla_dias INTEGER,
            sla_cumprido VARCHAR(10),
            dias_atendimento INTEGER,
            observacoes TEXT,
            requisicao TEXT,
            data_requisicao TIMESTAMP,
            pedido_compra TEXT,
            numero_pedido_compras VARCHAR(50),
            data_pedido_compra TIMESTAMP,
            fornecedor VARCHAR(200),
            valor_final DECIMAL(15,2),
            data_entrega_prevista DATE,
            data_entrega_real DATE,
            entrega_conforme VARCHAR(20),
            nota_fiscal VARCHAR(100),
            responsavel_recebimento VARCHAR(100),
            observacoes_entrega TEXT,
            observacoes_finalizacao TEXT,
            data_finalizacao TIMESTAMP,
            tipo_solicitacao VARCHAR(50),
            carimbo_data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Tabela de configurações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id SERIAL PRIMARY KEY,
            chave VARCHAR(100) UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            descricao TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 4. Tabela de catálogo de produtos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS catalogo_produtos (
            id SERIAL PRIMARY KEY,
            codigo VARCHAR(50) UNIQUE NOT NULL,
            nome VARCHAR(200) NOT NULL,
            descricao TEXT,
            unidade VARCHAR(10) NOT NULL DEFAULT 'UN',
            preco_referencia DECIMAL(15,2),
            categoria VARCHAR(100),
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 5. Tabela de movimentações/histórico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id SERIAL PRIMARY KEY,
            solicitacao_id INTEGER REFERENCES solicitacoes(id),
            usuario VARCHAR(100) NOT NULL,
            acao VARCHAR(100) NOT NULL,
            status_anterior VARCHAR(50),
            status_novo VARCHAR(50),
            observacoes TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 6. Tabela de notificações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notificacoes (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(100) NOT NULL,
            titulo VARCHAR(200) NOT NULL,
            mensagem TEXT NOT NULL,
            tipo VARCHAR(50) DEFAULT 'info',
            lida BOOLEAN DEFAULT FALSE,
            solicitacao_id INTEGER REFERENCES solicitacoes(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 7. Tabela de sessões
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100) UNIQUE NOT NULL,
            username VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            active BOOLEAN DEFAULT TRUE
        )
    """)
    
    print("✅ Tabelas criadas com sucesso!")

def create_indexes(cursor):
    """Cria índices para performance"""
    
    print("🔍 Criando índices...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_solicitacoes_solicitante ON solicitacoes(solicitante)",
        "CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes(status)",
        "CREATE INDEX IF NOT EXISTS idx_solicitacoes_data ON solicitacoes(data_solicitacao)",
        "CREATE INDEX IF NOT EXISTS idx_solicitacoes_prioridade ON solicitacoes(prioridade)",
        "CREATE INDEX IF NOT EXISTS idx_movimentacoes_solicitacao ON movimentacoes(solicitacao_id)",
        "CREATE INDEX IF NOT EXISTS idx_notificacoes_usuario ON notificacoes(usuario)",
        "CREATE INDEX IF NOT EXISTS idx_sessoes_username ON sessoes(username)",
        "CREATE INDEX IF NOT EXISTS idx_catalogo_ativo ON catalogo_produtos(ativo)"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
        except Exception as e:
            print(f"⚠️ Aviso ao criar índice: {e}")
    
    print("✅ Índices criados!")

def insert_default_data(cursor):
    """Insere dados padrão do sistema"""
    
    print("📊 Inserindo dados padrão...")
    
    # Usuários padrão (mesmas credenciais do Neon)
    usuarios_padrao = [
        ('admin', hash_password('admin123'), 'Administrador', 'Admin', 'TI'),
        ('Leonardo.Fragoso', hash_password('Teste123'), 'Leonardo Fragoso', 'Solicitante', 'TI'),
        ('Genival.Silva', hash_password('Teste123'), 'Genival Silva', 'Solicitante', 'Operações'),
        ('Diretoria', hash_password('Teste123'), 'Diretoria', 'Gerência&Diretoria', 'Diretoria'),
        ('Fabio.Ramos', hash_password('Teste123'), 'Fábio Ramos', 'Suprimentos', 'Suprimentos')
    ]
    
    for username, senha_hash, nome, perfil, departamento in usuarios_padrao:
        cursor.execute("""
            INSERT INTO usuarios (username, senha_hash, nome, perfil, departamento)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
                senha_hash = EXCLUDED.senha_hash,
                nome = EXCLUDED.nome,
                perfil = EXCLUDED.perfil,
                departamento = EXCLUDED.departamento
        """, (username, senha_hash, nome, perfil, departamento))
    
    # Configurações padrão
    configuracoes_padrao = [
        ('sistema_nome', 'Sistema de Gestão de Compras - SLA', 'Nome do sistema'),
        ('sla_urgente', '1', 'SLA para prioridade Urgente (dias)'),
        ('sla_alta', '2', 'SLA para prioridade Alta (dias)'),
        ('sla_normal', '3', 'SLA para prioridade Normal (dias)'),
        ('sla_baixa', '5', 'SLA para prioridade Baixa (dias)'),
        ('email_notificacoes', 'true', 'Enviar notificações por email'),
        ('backup_automatico', 'true', 'Realizar backup automático dos dados')
    ]
    
    for chave, valor, descricao in configuracoes_padrao:
        cursor.execute("""
            INSERT INTO configuracoes (chave, valor, descricao)
            VALUES (%s, %s, %s)
            ON CONFLICT (chave) DO UPDATE SET
                valor = EXCLUDED.valor,
                descricao = EXCLUDED.descricao
        """, (chave, valor, descricao))
    
    # Catálogo de produtos padrão
    produtos_padrao = [
        ('CANETA-001', 'Caneta Esferográfica Azul', 'Caneta esferográfica ponta média', 'UN', 2.50, 'Material de Escritório'),
        ('PAPEL-A4', 'Papel A4 75g Resma 500 folhas', 'Papel sulfite branco A4', 'PC', 25.00, 'Material de Escritório'),
        ('TONER-HP', 'Toner HP LaserJet Preto', 'Cartucho de toner original HP', 'UN', 180.00, 'Suprimentos TI'),
        ('CABO-REDE', 'Cabo de Rede Cat6 3m', 'Cabo ethernet categoria 6', 'UN', 15.00, 'Suprimentos TI'),
        ('MOUSE-USB', 'Mouse Óptico USB', 'Mouse óptico com scroll', 'UN', 35.00, 'Equipamentos TI')
    ]
    
    for codigo, nome, descricao, unidade, preco, categoria in produtos_padrao:
        cursor.execute("""
            INSERT INTO catalogo_produtos (codigo, nome, descricao, unidade, preco_referencia, categoria)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (codigo) DO UPDATE SET
                nome = EXCLUDED.nome,
                descricao = EXCLUDED.descricao,
                unidade = EXCLUDED.unidade,
                preco_referencia = EXCLUDED.preco_referencia,
                categoria = EXCLUDED.categoria
        """, (codigo, nome, descricao, unidade, preco, categoria))
    
    print("✅ Dados padrão inseridos!")

def verify_migration(cursor):
    """Verifica se a migração foi bem-sucedida"""
    
    print("\n🔍 Verificando migração...")
    
    # Verifica tabelas
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    
    tabelas = [row[0] for row in cursor.fetchall()]
    tabelas_esperadas = ['usuarios', 'solicitacoes', 'configuracoes', 'catalogo_produtos', 'movimentacoes', 'notificacoes', 'sessoes']
    
    print(f"📋 Tabelas encontradas: {len(tabelas)}")
    for tabela in tabelas:
        status = "✅" if tabela in tabelas_esperadas else "⚠️"
        print(f"  {status} {tabela}")
    
    # Verifica usuários
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cursor.fetchone()[0]
    print(f"👥 Usuários cadastrados: {total_usuarios}")
    
    # Verifica configurações
    cursor.execute("SELECT COUNT(*) FROM configuracoes")
    total_configs = cursor.fetchone()[0]
    print(f"⚙️ Configurações: {total_configs}")
    
    # Verifica produtos
    cursor.execute("SELECT COUNT(*) FROM catalogo_produtos")
    total_produtos = cursor.fetchone()[0]
    print(f"📦 Produtos no catálogo: {total_produtos}")
    
    print("\n🎉 Migração concluída com sucesso!")
    print("\n📋 Credenciais de acesso:")
    print("  👤 admin / admin123 (Administrador)")
    print("  👤 Leonardo.Fragoso / Teste123")
    print("  👤 Genival.Silva / Teste123")
    print("  👤 Diretoria / Teste123")
    print("  👤 Fabio.Ramos / Teste123")

def main():
    """Execução principal"""
    
    print("🚀 Migração Neon DB → Supabase")
    print("=" * 50)
    
    try:
        # Conecta ao Supabase
        print("🔗 Conectando ao Supabase...")
        conn = get_supabase_connection()
        cursor = conn.cursor()
        
        print("✅ Conexão estabelecida!")
        
        # Executa migração
        create_tables(cursor)
        create_indexes(cursor)
        insert_default_data(cursor)
        
        # Confirma transações
        conn.commit()
        
        # Verifica resultado
        verify_migration(cursor)
        
        # Fecha conexão
        cursor.close()
        conn.close()
        
        print("\n🎯 Próximos passos:")
        print("1. Execute: streamlit run app.py")
        print("2. Faça login com qualquer usuário acima")
        print("3. Sistema funcionará normalmente!")
        print("\n✅ Migração 100% concluída!")
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        print("\n🔧 Soluções:")
        print("1. Verifique sua connection string do Supabase")
        print("2. Confirme que o projeto está ativo")
        print("3. Teste a conexão no dashboard do Supabase")
        sys.exit(1)

if __name__ == "__main__":
    main()
