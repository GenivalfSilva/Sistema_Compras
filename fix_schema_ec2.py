#!/usr/bin/env python3
"""
Script para corrigir o schema do PostgreSQL - remove coluna duplicada responsavel_estoque
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import toml
import os

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
        
        # Fallback para variáveis de ambiente
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres123@localhost:5432/sistema_compras')
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        
    except Exception as e:
        print(f"❌ Erro ao conectar PostgreSQL: {e}")
        return None

def fix_schema():
    """Corrige o schema removendo a tabela e recriando corretamente"""
    print("🔧 CORRIGINDO SCHEMA DO POSTGRESQL")
    print("=" * 50)
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # 1. Remove tabela com problema
        print("1. Removendo tabela solicitacoes...")
        cursor.execute('DROP TABLE IF EXISTS solicitacoes CASCADE')
        
        # 2. Recria tabela com schema correto (sem duplicação)
        print("2. Recriando tabela com schema correto...")
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
        
        # 3. Recria índices
        print("3. Recriando índices...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_numero ON solicitacoes(numero_solicitacao_estoque)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_solicitante ON solicitacoes(solicitante)')
        
        conn.commit()
        print("✅ Schema corrigido com sucesso!")
        
        # 4. Testa conexão
        print("4. Testando conexão...")
        cursor.execute('SELECT COUNT(*) FROM solicitacoes')
        count = cursor.fetchone()[0]
        print(f"✅ Tabela solicitacoes: {count} registros")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao corrigir schema: {e}")
        return False
    
    finally:
        conn.close()

def test_database_connection():
    """Testa se o database_local.py funciona após correção"""
    print("\n🧪 TESTANDO CONEXÃO APÓS CORREÇÃO")
    print("=" * 40)
    
    try:
        from database_local import get_local_database
        db = get_local_database()
        
        print(f"DB Available: {db.db_available}")
        
        if db.db_available:
            users = db.get_all_users()
            print(f"✅ Usuários encontrados: {len(users)}")
            
            # Testa autenticação
            result = db.authenticate_user('admin', 'admin123')
            if result:
                print("✅ Autenticação funcionando!")
                return True
            else:
                print("❌ Autenticação ainda com problema")
                return False
        else:
            print("❌ Banco ainda não disponível")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    print("🔧 CORREÇÃO DE SCHEMA - POSTGRESQL EC2")
    print("=" * 50)
    
    # Corrige schema
    if fix_schema():
        # Testa conexão
        if test_database_connection():
            print("\n🎉 SUCESSO! Sistema pronto para uso")
            print("\n📋 CREDENCIAIS DE TESTE:")
            print("  admin / admin123")
            print("  Leonardo.Fragoso / Teste123")
            print("  Genival.Silva / Teste123")
        else:
            print("\n⚠️  Schema corrigido mas autenticação ainda com problema")
    else:
        print("\n❌ Falha na correção do schema")

if __name__ == "__main__":
    main()
