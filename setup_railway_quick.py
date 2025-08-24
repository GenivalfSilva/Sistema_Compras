#!/usr/bin/env python3
"""
Setup rápido Railway PostgreSQL para Streamlit Cloud
"""

import psycopg2
import hashlib
import os

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    print("🚂 Railway PostgreSQL Setup")
    print("=" * 50)
    print("1. Acesse: https://railway.app")
    print("2. Login com GitHub (gratuito)")
    print("3. New Project → Provision PostgreSQL")
    print("4. Clique no PostgreSQL → Connect → Copy Database URL")
    print("=" * 50)
    
    connection_string = input("\nCole sua Railway Database URL: ").strip()
    
    if not connection_string:
        print("❌ URL não fornecida")
        return
    
    try:
        # Testa conexão
        print("🔗 Testando conexão...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conectado! PostgreSQL: {version[0][:50]}...")
        
        # Cria tabela de usuários
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
        
        # Insere usuários
        print("👥 Inserindo usuários...")
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
        
        # Salva configuração
        config_content = f"""[database]
url = "{connection_string}"

[postgres]
# Railway PostgreSQL - funciona no Streamlit Cloud
"""
        with open('secrets_railway.toml', 'w') as f:
            f.write(config_content)
        
        cursor.close()
        conn.close()
        
        print("🎉 Railway configurado com sucesso!")
        print("\n📋 Credenciais de acesso:")
        print("  👤 admin / admin123")
        print("  👤 Leonardo.Fragoso / Teste123")
        print("  👤 Genival.Silva / Teste123")
        print("  👤 Diretoria / Teste123")
        print("  👤 Fabio.Ramos / Teste123")
        print("\n✅ Execute: streamlit run app.py")
        print("✅ Funciona no Streamlit Cloud!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("\n🔧 Verifique:")
        print("1. URL está correta")
        print("2. Projeto Railway está ativo")

if __name__ == "__main__":
    main()
