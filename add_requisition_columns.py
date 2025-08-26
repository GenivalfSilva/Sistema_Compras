#!/usr/bin/env python3
"""
Script para adicionar colunas necessárias para os dados da requisição no Sistema de Compras
Executa migração segura do banco PostgreSQL local
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import toml

def get_database_connection():
    """Obtém conexão com o banco PostgreSQL local"""
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
            elif 'database' in config and 'url' in config['database']:
                conn = psycopg2.connect(config['database']['url'], cursor_factory=RealDictCursor)
        else:
            # Fallback para variáveis de ambiente
            db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres123@localhost:5432/sistema_compras')
            conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {e}")
        return None

def check_column_exists(cursor, table_name, column_name):
    """Verifica se uma coluna existe na tabela"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    return cursor.fetchone() is not None

def add_requisition_columns():
    """Adiciona colunas necessárias para dados da requisição"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Lista de colunas para dados da requisição que podem estar faltando
        requisition_columns = [
            ("numero_requisicao_interno", "TEXT", "Número da requisição no sistema interno"),
            ("data_requisicao_interna", "TEXT", "Data de criação da requisição interna"),
            ("responsavel_estoque", "TEXT", "Responsável do estoque que criou a requisição"),
            ("observacoes_requisicao", "TEXT", "Observações sobre a requisição"),
            ("data_requisicao", "TEXT", "Data da requisição (formato legível)"),
            ("numero_requisicao", "INTEGER", "Número sequencial da requisição"),
        ]
        
        print("🔍 Verificando colunas existentes na tabela 'solicitacoes'...")
        
        # Verifica quais colunas já existem
        existing_columns = []
        missing_columns = []
        
        for column_name, column_type, description in requisition_columns:
            if check_column_exists(cursor, 'solicitacoes', column_name):
                existing_columns.append(column_name)
                print(f"✅ Coluna '{column_name}' já existe")
            else:
                missing_columns.append((column_name, column_type, description))
                print(f"❌ Coluna '{column_name}' não encontrada")
        
        # Adiciona colunas faltantes
        if missing_columns:
            print(f"\n📝 Adicionando {len(missing_columns)} coluna(s) faltante(s)...")
            
            for column_name, column_type, description in missing_columns:
                try:
                    alter_sql = f"ALTER TABLE solicitacoes ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    print(f"✅ Coluna '{column_name}' adicionada com sucesso ({description})")
                except Exception as e:
                    print(f"❌ Erro ao adicionar coluna '{column_name}': {e}")
            
            # Commit das alterações
            conn.commit()
            print(f"\n✅ Migração concluída! {len(missing_columns)} coluna(s) adicionada(s)")
        else:
            print("\n✅ Todas as colunas necessárias já existem no banco!")
        
        # Verifica estrutura final da tabela
        print("\n📋 Estrutura atual da tabela 'solicitacoes':")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'solicitacoes'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  • {col['column_name']} ({col['data_type']}) - {nullable}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Função principal"""
    print("🚀 Iniciando migração para adicionar colunas de requisição...")
    print("=" * 60)
    
    success = add_requisition_columns()
    
    print("=" * 60)
    if success:
        print("✅ Migração concluída com sucesso!")
        print("\n📌 Próximos passos:")
        print("1. Reiniciar a aplicação Streamlit")
        print("2. Testar o formulário de requisições")
        print("3. Verificar se os dados são salvos corretamente")
    else:
        print("❌ Migração falhou. Verifique os logs acima.")
    
    return success

if __name__ == "__main__":
    main()
