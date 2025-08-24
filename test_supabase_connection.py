#!/usr/bin/env python3
"""
Script simplificado para testar e configurar conexão Supabase
"""

import subprocess
import sys

def install_dependencies():
    """Instala dependências necessárias"""
    print("📦 Instalando dependências...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary", "toml"])
        print("✅ Dependências instaladas!")
        return True
    except Exception as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def test_connection():
    """Testa conexão com Supabase"""
    try:
        import psycopg2
        
        connection_string = "postgresql://postgres:232315@db.amusiwxxishpynwzglmk.supabase.co:5432/postgres"
        
        print("🔗 Testando conexão com Supabase...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Testa conexão
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexão estabelecida! PostgreSQL: {version[0][:50]}...")
        
        # Cria tabela de usuários simples
        print("📋 Criando tabela de usuários...")
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
        
        # Insere usuários padrão
        print("👥 Inserindo usuários padrão...")
        import hashlib
        
        def hash_password(password):
            return hashlib.sha256(password.encode()).hexdigest()
        
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
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Configuração concluída com sucesso!")
        print("\n📋 Credenciais de acesso:")
        print("  👤 admin / admin123 (Administrador)")
        print("  👤 Leonardo.Fragoso / Teste123")
        print("  👤 Genival.Silva / Teste123")
        print("  👤 Diretoria / Teste123")
        print("  👤 Fabio.Ramos / Teste123")
        print("\n✅ Execute: streamlit run app.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print(f"❌ Tipo do erro: {type(e).__name__}")
        import traceback
        print(f"❌ Detalhes: {traceback.format_exc()}")
        return False

def main():
    print("🚀 Configuração Simplificada Supabase")
    print("=" * 50)
    
    # Instala dependências
    if not install_dependencies():
        return
    
    # Testa conexão e configura
    if test_connection():
        print("\n🎯 Sistema pronto para uso!")
    else:
        print("\n❌ Falha na configuração")

if __name__ == "__main__":
    main()
