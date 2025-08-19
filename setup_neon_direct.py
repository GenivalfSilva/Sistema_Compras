#!/usr/bin/env python3
"""
Script direto para configurar Neon DB com as credenciais fornecidas
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib

# Credenciais do Neon DB
DB_CONFIG = {
    "host": "ep-quiet-wave-aexxyu7g-pooler.c-2.us-east-2.aws.neon.tech",
    "database": "neondb", 
    "user": "neondb_owner",
    "password": "npg_GZJ7yawMprC5",
    "port": 5432,
    "sslmode": "require"
}

def create_all_tables():
    """Cria todas as tabelas necessárias"""
    
    # SQL para criar todas as tabelas
    tables_sql = [
        # Tabela usuarios
        '''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            nome VARCHAR(100) NOT NULL,
            perfil VARCHAR(50) NOT NULL,
            departamento VARCHAR(50) NOT NULL,
            senha_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        
        # Tabela solicitacoes (completa)
        '''
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
        ''',
        
        # Tabela configuracoes
        '''
        CREATE TABLE IF NOT EXISTS configuracoes (
            id SERIAL PRIMARY KEY,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        
        # Tabela catalogo_produtos
        '''
        CREATE TABLE IF NOT EXISTS catalogo_produtos (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            categoria TEXT,
            unidade TEXT NOT NULL,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        
        # Tabela movimentacoes
        '''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id SERIAL PRIMARY KEY,
            numero_solicitacao INTEGER NOT NULL,
            etapa_origem TEXT NOT NULL,
            etapa_destino TEXT NOT NULL,
            usuario TEXT NOT NULL,
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observacoes TEXT
        )
        ''',
        
        # Tabela notificacoes
        '''
        CREATE TABLE IF NOT EXISTS notificacoes (
            id SERIAL PRIMARY KEY,
            perfil TEXT NOT NULL,
            numero INTEGER NOT NULL,
            mensagem TEXT NOT NULL,
            data TIMESTAMP NOT NULL,
            lida BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        
        # Tabela sessoes
        '''
        CREATE TABLE IF NOT EXISTS sessoes (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        '''
    ]
    
    try:
        print("🔌 Conectando ao Neon DB...")
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("✅ Conexão estabelecida!")
        
        print("\n🔧 Criando tabelas...")
        table_names = ["usuarios", "solicitacoes", "configuracoes", "catalogo_produtos", 
                      "movimentacoes", "notificacoes", "sessoes"]
        
        for i, sql in enumerate(tables_sql):
            cursor.execute(sql)
            print(f"✅ Tabela '{table_names[i]}' criada/atualizada")
        
        print("\n🔧 Criando índices...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_numero ON solicitacoes(numero_solicitacao_estoque)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes(status)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_etapa ON solicitacoes(etapa_atual)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_departamento ON solicitacoes(departamento)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_prioridade ON solicitacoes(prioridade)",
            "CREATE INDEX IF NOT EXISTS idx_movimentacoes_numero ON movimentacoes(numero_solicitacao)",
            "CREATE INDEX IF NOT EXISTS idx_notificacoes_perfil ON notificacoes(perfil)",
            "CREATE INDEX IF NOT EXISTS idx_sessoes_expires ON sessoes(expires_at)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        print("✅ Índices criados!")
        
        print("\n🔧 Inserindo dados padrão...")
        
        # Verifica se já existe usuário admin
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE perfil = 'Admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Cria usuário admin padrão
            SALT = "ziran_local_salt_v1"
            senha_hash = hashlib.sha256((SALT + "admin123").encode("utf-8")).hexdigest()
            
            cursor.execute("""
                INSERT INTO usuarios (username, nome, perfil, departamento, senha_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, ("admin", "Administrador", "Admin", "TI", senha_hash))
            print("  ➕ Usuário admin criado (login: admin, senha: admin123)")
        
        # Insere catálogo padrão se vazio
        cursor.execute("SELECT COUNT(*) FROM catalogo_produtos")
        produto_count = cursor.fetchone()[0]
        
        if produto_count == 0:
            produtos_padrao = [
                ("PRD-001", "Cabo de Rede Cat6", "TI", "UN", True),
                ("PRD-002", "Notebook 14\"", "TI", "UN", True),
                ("PRD-003", "Tinta Látex Branca", "Manutenção", "L", True),
                ("PRD-004", "Parafuso 5mm", "Manutenção", "CX", True),
                ("PRD-005", "Papel A4 75g", "Escritório", "CX", True),
            ]
            
            for codigo, nome, categoria, unidade, ativo in produtos_padrao:
                cursor.execute("""
                    INSERT INTO catalogo_produtos (codigo, nome, categoria, unidade, ativo)
                    VALUES (%s, %s, %s, %s, %s)
                """, (codigo, nome, categoria, unidade, ativo))
            print("  ➕ Catálogo padrão de produtos inserido")
        
        # Insere configurações padrão
        configs_padrao = [
            ("proximo_numero_solicitacao", "1"),
            ("proximo_numero_pedido", "1"),
            ("limite_gerencia", "5000.0"),
            ("limite_diretoria", "15000.0"),
            ("upload_dir", "uploads"),
            ("suprimentos_min_cotacoes", "1"),
            ("suprimentos_anexo_obrigatorio", "true"),
        ]
        
        for chave, valor in configs_padrao:
            cursor.execute("""
                INSERT INTO configuracoes (chave, valor) 
                VALUES (%s, %s) 
                ON CONFLICT (chave) DO NOTHING
            """, (chave, valor))
        
        conn.commit()
        print("✅ Dados padrão inseridos!")
        
        print("\n🔍 Verificando setup...")
        tables_to_check = [
            "usuarios", "solicitacoes", "configuracoes", 
            "catalogo_produtos", "movimentacoes", "notificacoes", "sessoes"
        ]
        
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ Tabela '{table}': {count} registros")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("🎉 Setup do Neon DB concluído com sucesso!")
        print("📋 Todas as 7 tabelas foram criadas:")
        print("   - usuarios")
        print("   - solicitacoes (com todas as colunas)")
        print("   - configuracoes")
        print("   - catalogo_produtos")
        print("   - movimentacoes")
        print("   - notificacoes")
        print("   - sessoes")
        print("\n📝 Próximos passos:")
        print("   1. Execute o app.py para testar a conexão")
        print("   2. Faça login com: admin / admin123")
        print("   3. Configure usuários adicionais se necessário")
        
    except Exception as e:
        print(f"❌ Erro durante o setup: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando setup direto do Neon DB")
    print("=" * 60)
    create_all_tables()
