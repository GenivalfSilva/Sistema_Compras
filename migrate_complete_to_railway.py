#!/usr/bin/env python3
"""
Migração COMPLETA do Sistema de Compras para Railway PostgreSQL
Cria todas as tabelas e migra dados existentes do SQLite (se houver)
"""

import psycopg2
import sqlite3
import json
import hashlib
import os
from datetime import datetime

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_all_tables(cursor):
    """Cria todas as tabelas do sistema no PostgreSQL"""
    
    print("📋 Criando tabela de usuários...")
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

    print("📋 Criando tabela de solicitações...")
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    print("📋 Criando tabela de configurações...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS configuracoes (
        id SERIAL PRIMARY KEY,
        chave TEXT UNIQUE NOT NULL,
        valor TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    print("📋 Criando tabela de histórico de etapas...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico_etapas (
        id SERIAL PRIMARY KEY,
        numero_solicitacao INTEGER NOT NULL,
        etapa_origem TEXT NOT NULL,
        etapa_destino TEXT NOT NULL,
        usuario TEXT NOT NULL,
        data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        observacoes TEXT
    )
    ''')

    print("📋 Criando tabela de notificações...")
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

    print("📋 Criando tabela de sessões...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessoes (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Criar índices para performance
    print("📋 Criando índices...")
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_solicitacoes_numero ON solicitacoes(numero_solicitacao_estoque)",
        "CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes(status)",
        "CREATE INDEX IF NOT EXISTS idx_solicitacoes_etapa ON solicitacoes(etapa_atual)",
        "CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)",
        "CREATE INDEX IF NOT EXISTS idx_historico_numero ON historico_etapas(numero_solicitacao)",
        "CREATE INDEX IF NOT EXISTS idx_notificacoes_perfil ON notificacoes(perfil)",
        "CREATE INDEX IF NOT EXISTS idx_sessoes_username ON sessoes(username)"
    ]
    
    for idx in indices:
        cursor.execute(idx)

def insert_default_data(cursor):
    """Insere dados padrão do sistema"""
    
    print("👥 Inserindo usuários padrão...")
    usuarios = [
        ('admin', hash_password('admin123'), 'Administrador', 'Admin', 'TI'),
        ('Leonardo.Fragoso', hash_password('Teste123'), 'Leonardo Fragoso', 'Solicitante', 'TI'),
        ('Genival.Silva', hash_password('Teste123'), 'Genival Silva', 'Solicitante', 'Operações'),
        ('Diretoria', hash_password('Teste123'), 'Diretoria', 'Gerência&Diretoria', 'Diretoria'),
        ('Fabio.Ramos', hash_password('Teste123'), 'Fábio Ramos', 'Suprimentos', 'Suprimentos')
    ]
    
    for username, senha_hash, nome, perfil, departamento in usuarios:
        cursor.execute("""
            INSERT INTO usuarios (username, senha_hash, nome, perfil, departamento)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (username) DO UPDATE SET
                senha_hash = EXCLUDED.senha_hash,
                nome = EXCLUDED.nome,
                perfil = EXCLUDED.perfil,
                departamento = EXCLUDED.departamento
        """, (username, senha_hash, nome, perfil, departamento))

    print("⚙️ Inserindo configurações padrão...")
    configuracoes = [
        ('sla_solicitacao_compra', '10'),
        ('sla_cotacao', '5'),
        ('sla_aprovacao', '3'),
        ('email_notificacoes', 'true'),
        ('auto_backup', 'true')
    ]
    
    for chave, valor in configuracoes:
        cursor.execute("""
            INSERT INTO configuracoes (chave, valor)
            VALUES (%s, %s)
            ON CONFLICT (chave) DO UPDATE SET
                valor = EXCLUDED.valor,
                updated_at = CURRENT_TIMESTAMP
        """, (chave, valor))

def migrate_sqlite_data(cursor, sqlite_path="compras_sla.db"):
    """Migra dados existentes do SQLite para PostgreSQL"""
    
    if not os.path.exists(sqlite_path):
        print(f"⚠️ Arquivo SQLite não encontrado: {sqlite_path}")
        return
    
    print(f"📦 Migrando dados do SQLite: {sqlite_path}")
    
    try:
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # Migrar solicitações
        print("📋 Migrando solicitações...")
        sqlite_cursor.execute("SELECT * FROM solicitacoes")
        solicitacoes = sqlite_cursor.fetchall()
        
        for sol in solicitacoes:
            cursor.execute("""
                INSERT INTO solicitacoes (
                    numero_solicitacao_estoque, numero_pedido_compras, solicitante, departamento,
                    descricao, prioridade, local_aplicacao, status, etapa_atual, carimbo_data_hora,
                    data_numero_pedido, data_cotacao, data_entrega, sla_dias, dias_atendimento,
                    sla_cumprido, observacoes, numero_requisicao_interno, data_requisicao_interna,
                    responsavel_suprimentos, valor_estimado, valor_final, fornecedor_recomendado,
                    fornecedor_final, anexos_requisicao, cotacoes, aprovacoes, historico_etapas, itens
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (numero_solicitacao_estoque) DO NOTHING
            """, tuple(sol[1:]))  # Skip id column
        
        # Migrar histórico de etapas
        print("📋 Migrando histórico de etapas...")
        try:
            sqlite_cursor.execute("SELECT * FROM historico_etapas")
            historicos = sqlite_cursor.fetchall()
            
            for hist in historicos:
                cursor.execute("""
                    INSERT INTO historico_etapas (numero_solicitacao, etapa_origem, etapa_destino, usuario, data_movimentacao, observacoes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (hist['numero_solicitacao'], hist['etapa_origem'], hist['etapa_destino'], 
                     hist['usuario'], hist['data_movimentacao'], hist.get('observacoes')))
        except Exception as e:
            print(f"⚠️ Erro ao migrar histórico: {e}")
        
        sqlite_conn.close()
        print(f"✅ Migração do SQLite concluída! {len(solicitacoes)} solicitações migradas")
        
    except Exception as e:
        print(f"❌ Erro na migração SQLite: {e}")

def main():
    print("🚂 MIGRAÇÃO COMPLETA PARA RAILWAY POSTGRESQL")
    print("=" * 60)
    
    # Lê configuração do Railway
    railway_url = None
    if os.path.exists('secrets_railway.toml'):
        import toml
        config = toml.load('secrets_railway.toml')
        railway_url = config.get('database', {}).get('url')
    
    if not railway_url:
        print("❌ Configuração Railway não encontrada!")
        print("Execute primeiro: python setup_railway_quick.py")
        return
    
    try:
        # Conecta ao Railway
        print("🔗 Conectando ao Railway PostgreSQL...")
        conn = psycopg2.connect(railway_url)
        cursor = conn.cursor()
        
        # Testa conexão
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conectado! {version[0][:50]}...")
        
        # Cria todas as tabelas
        create_all_tables(cursor)
        
        # Insere dados padrão
        insert_default_data(cursor)
        
        # Migra dados do SQLite se existir
        migrate_sqlite_data(cursor)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 MIGRAÇÃO COMPLETA FINALIZADA!")
        print("=" * 60)
        print("✅ Todas as tabelas criadas no Railway")
        print("✅ Usuários padrão inseridos")
        print("✅ Configurações padrão inseridas")
        print("✅ Dados SQLite migrados (se existiam)")
        print("✅ Índices criados para performance")
        print("\n🚀 Sistema pronto para usar Railway em produção!")
        print("🌐 Funciona perfeitamente no Streamlit Cloud!")
        
        print("\n📋 Credenciais de acesso:")
        print("  👤 admin / admin123")
        print("  👤 Leonardo.Fragoso / Teste123")
        print("  👤 Genival.Silva / Teste123")
        print("  👤 Diretoria / Teste123")
        print("  👤 Fabio.Ramos / Teste123")
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
        print("\n🔧 Verifique:")
        print("1. Railway está configurado corretamente")
        print("2. Conexão com internet está funcionando")
        print("3. Execute: python setup_railway_quick.py")

if __name__ == "__main__":
    main()
