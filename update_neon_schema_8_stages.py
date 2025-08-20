#!/usr/bin/env python3
"""
Script para atualizar o schema do Neon DB para suportar o novo fluxo de 8 etapas
Adiciona colunas necessárias para o controle de entregas e finalização
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

def get_neon_connection():
    """Conecta ao Neon DB usando diferentes métodos de configuração"""
    try:
        # Método 1: Streamlit secrets
        if hasattr(st, 'secrets') and 'postgres' in st.secrets:
            pg = st.secrets['postgres']
            return psycopg2.connect(
                host=pg['host'],
                database=pg['database'],
                user=pg['user'],
                password=pg['password'],
                port=int(pg.get('port', 5432)),
                sslmode=pg.get('sslmode', 'require'),
                cursor_factory=RealDictCursor
            )
        
        # Método 2: Arquivo secrets_neon.toml
        try:
            import toml
            if os.path.exists('secrets_neon.toml'):
                config = toml.load('secrets_neon.toml')
                pg = config['postgres']
                return psycopg2.connect(
                    host=pg['host'],
                    database=pg['database'],
                    user=pg['user'],
                    password=pg['password'],
                    port=int(pg.get('port', 5432)),
                    sslmode=pg.get('sslmode', 'require'),
                    cursor_factory=RealDictCursor
                )
        except ImportError:
            pass
        
        # Método 3: Variável de ambiente
        if os.getenv('DATABASE_URL'):
            return psycopg2.connect(os.getenv('DATABASE_URL'), cursor_factory=RealDictCursor)
        
        raise Exception("Nenhuma configuração de banco encontrada")
        
    except Exception as e:
        print(f"Erro ao conectar ao Neon DB: {e}")
        return None

def check_column_exists(cursor, table_name, column_name):
    """Verifica se uma coluna existe na tabela"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    return cursor.fetchone() is not None

def add_missing_columns(conn):
    """Adiciona colunas necessárias para o novo fluxo de 8 etapas"""
    cursor = conn.cursor()
    
    # Colunas necessárias para o novo fluxo
    new_columns = [
        # Controle de entregas
        ('data_entrega_prevista', 'TEXT'),
        ('data_entrega_real', 'TEXT'),
        ('entrega_conforme', 'TEXT'),
        ('nota_fiscal', 'TEXT'),
        ('responsavel_recebimento', 'TEXT'),
        ('observacoes_entrega', 'TEXT'),
        ('observacoes_finalizacao', 'TEXT'),
        
        # Campos adicionais que podem ser úteis
        ('data_finalizacao', 'TEXT'),
        ('tipo_solicitacao', 'TEXT'),
        ('justificativa', 'TEXT'),
    ]
    
    added_columns = []
    
    for column_name, column_type in new_columns:
        if not check_column_exists(cursor, 'solicitacoes', column_name):
            try:
                alter_sql = f"ALTER TABLE solicitacoes ADD COLUMN {column_name} {column_type}"
                cursor.execute(alter_sql)
                added_columns.append(column_name)
                print(f"✅ Coluna '{column_name}' adicionada com sucesso")
            except Exception as e:
                print(f"❌ Erro ao adicionar coluna '{column_name}': {e}")
        else:
            print(f"ℹ️  Coluna '{column_name}' já existe")
    
    if added_columns:
        conn.commit()
        print(f"\n🎉 {len(added_columns)} nova(s) coluna(s) adicionada(s) com sucesso!")
        print("Colunas adicionadas:", ", ".join(added_columns))
    else:
        print("\n✅ Schema já está atualizado - nenhuma coluna precisou ser adicionada")
    
    return added_columns

def verify_schema(conn):
    """Verifica o schema atual da tabela solicitacoes"""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'solicitacoes'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    
    print("\n📋 Schema atual da tabela 'solicitacoes':")
    print("-" * 60)
    for col in columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        print(f"  {col['column_name']:<30} {col['data_type']:<15} {nullable}")
    
    return columns

def main():
    """Função principal"""
    print("🔄 Atualizando schema do Neon DB para suporte ao fluxo de 8 etapas...")
    print("=" * 70)
    
    # Conecta ao banco
    conn = get_neon_connection()
    if not conn:
        print("❌ Não foi possível conectar ao Neon DB")
        sys.exit(1)
    
    try:
        print("✅ Conectado ao Neon DB com sucesso!")
        
        # Verifica schema atual
        print("\n1️⃣ Verificando schema atual...")
        verify_schema(conn)
        
        # Adiciona colunas necessárias
        print("\n2️⃣ Adicionando colunas necessárias...")
        added_columns = add_missing_columns(conn)
        
        # Verifica schema final
        if added_columns:
            print("\n3️⃣ Verificando schema atualizado...")
            verify_schema(conn)
        
        print("\n🎉 Atualização do schema concluída com sucesso!")
        print("O sistema agora suporta completamente o fluxo de 8 etapas:")
        print("1. Solicitação → 2. Suprimentos → 3. Em Cotação → 4. Aguardando Aprovação")
        print("5. Aprovado/Reprovado → 6. Compra feita → 7. Aguardando Entrega → 8. Pedido Finalizado")
        
    except Exception as e:
        print(f"❌ Erro durante a atualização: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
