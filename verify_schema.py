#!/usr/bin/env python3
"""
Script para verificar o schema da tabela solicitacoes no Neon DB
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Credenciais do Neon DB
conn_string = "postgresql://neondb_owner:npg_GZJ7yawMprC5@ep-quiet-wave-aexxyu7g-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"

try:
    print("🔍 Verificando schema da tabela 'solicitacoes' no Neon DB...")
    conn = psycopg2.connect(conn_string, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    
    # Consulta para obter todas as colunas da tabela solicitacoes
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns 
        WHERE table_name = 'solicitacoes' 
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    
    print(f"\n📋 Tabela 'solicitacoes' possui {len(columns)} colunas:")
    print("=" * 80)
    
    for col in columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
        print(f"  ✅ {col['column_name']:<30} {col['data_type']:<20} {nullable}{default}")
    
    # Verifica se existem registros
    cursor.execute("SELECT COUNT(*) FROM solicitacoes")
    result = cursor.fetchone()
    count = result['count'] if isinstance(result, dict) else result[0]
    
    print(f"\n📊 Total de registros: {count}")
    
    # Lista das colunas esperadas para uma solicitação completa
    expected_columns = [
        'id',
        'numero_solicitacao_estoque',
        'numero_pedido_compras',
        'solicitante',
        'departamento', 
        'descricao',
        'prioridade',
        'local_aplicacao',
        'status',
        'etapa_atual',
        'carimbo_data_hora',
        'data_numero_pedido',
        'data_cotacao',
        'data_entrega',
        'sla_dias',
        'dias_atendimento',
        'sla_cumprido',
        'observacoes',
        'numero_requisicao_interno',
        'data_requisicao_interna',
        'responsavel_suprimentos',
        'valor_estimado',
        'valor_final',
        'fornecedor_recomendado',
        'fornecedor_final',
        'anexos_requisicao',
        'cotacoes',
        'aprovacoes',
        'historico_etapas',
        'itens',
        'created_at'
    ]
    
    actual_columns = [col['column_name'] for col in columns]
    
    print(f"\n🔍 Verificação de colunas necessárias:")
    print("=" * 50)
    
    missing_columns = []
    for expected in expected_columns:
        if expected in actual_columns:
            print(f"  ✅ {expected}")
        else:
            print(f"  ❌ {expected} - FALTANDO")
            missing_columns.append(expected)
    
    if missing_columns:
        print(f"\n⚠️ ATENÇÃO: {len(missing_columns)} colunas estão faltando:")
        for col in missing_columns:
            print(f"    - {col}")
    else:
        print(f"\n🎉 PERFEITO! Todas as {len(expected_columns)} colunas necessárias estão presentes!")
    
    # Verifica também outras tabelas importantes
    print(f"\n🔍 Verificando outras tabelas importantes:")
    important_tables = ['usuarios', 'configuracoes', 'catalogo_produtos']
    
    for table in important_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        result = cursor.fetchone()
        count = result['count'] if isinstance(result, dict) else result[0]
        print(f"  ✅ {table}: {count} registros")
    
    cursor.close()
    conn.close()
    
    print(f"\n{'='*60}")
    if not missing_columns:
        print("🎉 SCHEMA COMPLETO! Pronto para criar solicitações de compras!")
    else:
        print("⚠️ Schema incompleto - algumas colunas precisam ser adicionadas")
    
except Exception as e:
    print(f"❌ Erro ao verificar schema: {e}")
    import traceback
    traceback.print_exc()
