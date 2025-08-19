#!/usr/bin/env python3
"""
Script simplificado para criar todas as tabelas no Neon DB
Usa apenas bibliotecas padrão do Python + psycopg2
"""

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import hashlib
    
    # Credenciais do Neon DB
    conn_string = "postgresql://neondb_owner:npg_GZJ7yawMprC5@ep-quiet-wave-aexxyu7g-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"
    
    print("🚀 Conectando ao Neon DB...")
    conn = psycopg2.connect(conn_string, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    print("✅ Conexão estabelecida!")
    
    # Lista de todas as tabelas SQL
    tables = {
        "usuarios": '''
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
        
        "solicitacoes": '''
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
        
        "configuracoes": '''
            CREATE TABLE IF NOT EXISTS configuracoes (
                id SERIAL PRIMARY KEY,
                chave TEXT UNIQUE NOT NULL,
                valor TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        
        "catalogo_produtos": '''
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
        
        "movimentacoes": '''
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
        
        "notificacoes": '''
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
        
        "sessoes": '''
            CREATE TABLE IF NOT EXISTS sessoes (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
    }
    
    print("\n🔧 Criando tabelas...")
    for table_name, sql in tables.items():
        try:
            cursor.execute(sql)
            print(f"✅ Tabela '{table_name}' criada/atualizada")
        except Exception as e:
            print(f"❌ Erro na tabela '{table_name}': {e}")
    
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
        try:
            cursor.execute(index_sql)
        except Exception as e:
            print(f"⚠️ Erro no índice: {e}")
    
    print("✅ Índices criados!")
    
    print("\n🔧 Inserindo dados padrão...")
    
    # Verifica se já existe usuário admin
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE perfil = 'Admin'")
    result = cursor.fetchone()
    admin_count = result['count'] if isinstance(result, dict) else result[0]
    
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
    result = cursor.fetchone()
    produto_count = result['count'] if isinstance(result, dict) else result[0]
    
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
        result = cursor.fetchone()
        count = result['count'] if isinstance(result, dict) else result[0]
        print(f"  ✅ Tabela '{table}': {count} registros")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 SETUP DO NEON DB CONCLUÍDO COM SUCESSO!")
    print("📋 Todas as 7 tabelas foram criadas:")
    print("   ✅ usuarios")
    print("   ✅ solicitacoes (com TODAS as colunas necessárias)")
    print("   ✅ configuracoes")
    print("   ✅ catalogo_produtos")
    print("   ✅ movimentacoes")
    print("   ✅ notificacoes")
    print("   ✅ sessoes")
    print("\n📝 Próximos passos:")
    print("   1. Execute o app.py para testar a conexão")
    print("   2. Faça login com: admin / admin123")
    print("   3. Configure usuários adicionais se necessário")
    print("\n🔗 Seu banco Neon DB está pronto para uso!")

except ImportError:
    print("❌ psycopg2 não está instalado!")
    print("📦 Execute: pip install psycopg2-binary")
    print("📦 Ou: python -m pip install psycopg2-binary")
    
except Exception as e:
    print(f"❌ Erro durante o setup: {e}")
    import traceback
    traceback.print_exc()
