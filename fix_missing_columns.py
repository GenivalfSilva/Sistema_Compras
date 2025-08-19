#!/usr/bin/env python3
"""
Script para adicionar as colunas faltantes na tabela solicitacoes
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Credenciais do Neon DB
conn_string = "postgresql://neondb_owner:npg_GZJ7yawMprC5@ep-quiet-wave-aexxyu7g-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"

try:
    print("🔧 Adicionando colunas faltantes na tabela 'solicitacoes'...")
    conn = psycopg2.connect(conn_string, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # Colunas que precisam ser adicionadas
    missing_columns = [
        ("local_aplicacao", "TEXT"),
        ("carimbo_data_hora", "TEXT NOT NULL DEFAULT ''"),
        ("sla_dias", "INTEGER NOT NULL DEFAULT 3")
    ]
    
    for column_name, column_type in missing_columns:
        try:
            # Verifica se a coluna já existe
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'solicitacoes' AND column_name = %s
            """, (column_name,))
            
            if not cursor.fetchone():
                # Coluna não existe, adiciona
                sql = f"ALTER TABLE solicitacoes ADD COLUMN {column_name} {column_type}"
                cursor.execute(sql)
                print(f"  ✅ Coluna '{column_name}' adicionada")
            else:
                print(f"  ℹ️ Coluna '{column_name}' já existe")
                
        except Exception as e:
            print(f"  ❌ Erro ao adicionar coluna '{column_name}': {e}")
    
    # Também vamos corrigir o nome da coluna 'aplicacao' para 'local_aplicacao' se necessário
    try:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'solicitacoes' AND column_name = 'aplicacao'
        """)
        
        if cursor.fetchone():
            # Existe coluna 'aplicacao', vamos renomeá-la
            cursor.execute("ALTER TABLE solicitacoes RENAME COLUMN aplicacao TO local_aplicacao_temp")
            print("  🔄 Coluna 'aplicacao' renomeada temporariamente")
            
            # Se local_aplicacao não existe, renomeia de volta
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'solicitacoes' AND column_name = 'local_aplicacao'
            """)
            
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE solicitacoes RENAME COLUMN local_aplicacao_temp TO local_aplicacao")
                cursor.execute("ALTER TABLE solicitacoes ALTER COLUMN local_aplicacao TYPE TEXT")
                print("  ✅ Coluna 'aplicacao' renomeada para 'local_aplicacao'")
            else:
                # Se local_aplicacao já existe, remove a temp
                cursor.execute("ALTER TABLE solicitacoes DROP COLUMN local_aplicacao_temp")
                print("  🗑️ Coluna temporária removida")
                
    except Exception as e:
        print(f"  ⚠️ Aviso na correção de 'aplicacao': {e}")
    
    conn.commit()
    print("\n🎉 Colunas adicionadas com sucesso!")
    
    # Verifica o resultado final
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'solicitacoes' 
        AND column_name IN ('local_aplicacao', 'carimbo_data_hora', 'sla_dias')
        ORDER BY column_name
    """)
    
    result_columns = cursor.fetchall()
    print(f"\n📋 Verificação final - {len(result_columns)} colunas adicionadas:")
    for col in result_columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        print(f"  ✅ {col['column_name']:<20} {col['data_type']:<15} {nullable}")
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*60}")
    print("🎉 SCHEMA COMPLETO! Agora você pode criar solicitações!")
    print("📝 Próximo passo: Teste criar uma solicitação no app.py")
    
except Exception as e:
    print(f"❌ Erro ao adicionar colunas: {e}")
    import traceback
    traceback.print_exc()
