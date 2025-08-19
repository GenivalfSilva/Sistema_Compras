#!/usr/bin/env python3
"""
Script para configurar e testar conexão com Neon DB antes do setup.
Este script ajuda a configurar as credenciais e testa a conectividade.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def test_connection_string(conn_string):
    """Testa uma string de conexão"""
    try:
        conn = psycopg2.connect(conn_string, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, version
    except Exception as e:
        return False, str(e)

def test_connection_params(host, database, user, password, port=5432, sslmode="require"):
    """Testa conexão com parâmetros individuais"""
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
            sslmode=sslmode,
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, version
    except Exception as e:
        return False, str(e)

def create_secrets_file():
    """Cria arquivo secrets.toml interativamente"""
    print("🔧 Configuração do Neon DB")
    print("=" * 40)
    
    print("\n📋 Você precisará das seguintes informações do Neon Console:")
    print("   1. Host/Endpoint (ex: ep-xxx-xxx.us-east-1.aws.neon.tech)")
    print("   2. Database name (geralmente 'neondb')")
    print("   3. User (geralmente termina com '_owner')")
    print("   4. Password")
    
    host = input("\n🌐 Host/Endpoint: ").strip()
    database = input("🗄️  Database name [neondb]: ").strip() or "neondb"
    user = input("👤 User: ").strip()
    password = input("🔐 Password: ").strip()
    port = input("🔌 Port [5432]: ").strip() or "5432"
    
    # Testa a conexão
    print("\n🔍 Testando conexão...")
    success, result = test_connection_params(host, database, user, password, int(port))
    
    if success:
        print(f"✅ Conexão bem-sucedida!")
        print(f"📊 Versão do PostgreSQL: {result}")
        
        # Cria arquivo secrets.toml
        secrets_content = f"""[postgres]
host = "{host}"
database = "{database}"
user = "{user}"
password = "{password}"
port = {port}
sslmode = "require"
"""
        
        with open("secrets.toml", "w", encoding="utf-8") as f:
            f.write(secrets_content)
        
        print("✅ Arquivo 'secrets.toml' criado com sucesso!")
        return True
    else:
        print(f"❌ Falha na conexão: {result}")
        return False

def check_existing_config():
    """Verifica configurações existentes"""
    print("🔍 Verificando configurações existentes...")
    
    configs_found = []
    
    # Verifica secrets.toml
    if os.path.exists("secrets.toml"):
        configs_found.append("secrets.toml")
        try:
            import toml
            secrets = toml.load("secrets.toml")
            if "postgres" in secrets:
                pg = secrets["postgres"]
                print(f"📄 secrets.toml encontrado:")
                print(f"   Host: {pg.get('host', 'N/A')}")
                print(f"   Database: {pg.get('database', 'N/A')}")
                print(f"   User: {pg.get('user', 'N/A')}")
                
                # Testa conexão
                success, result = test_connection_params(
                    pg.get("host"),
                    pg.get("database"),
                    pg.get("user"),
                    pg.get("password"),
                    int(pg.get("port", 5432)),
                    pg.get("sslmode", "require")
                )
                
                if success:
                    print(f"   ✅ Conexão: OK")
                    return True
                else:
                    print(f"   ❌ Conexão: {result}")
        except Exception as e:
            print(f"   ❌ Erro ao ler secrets.toml: {e}")
    
    # Verifica variáveis de ambiente
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        configs_found.append("DATABASE_URL")
        print(f"🌍 DATABASE_URL encontrada")
        success, result = test_connection_string(database_url)
        if success:
            print(f"   ✅ Conexão: OK")
            return True
        else:
            print(f"   ❌ Conexão: {result}")
    
    # Verifica variáveis individuais
    postgres_host = os.getenv("POSTGRES_HOST")
    if postgres_host:
        configs_found.append("Variáveis de ambiente individuais")
        print(f"🌍 Variáveis de ambiente encontradas:")
        print(f"   Host: {postgres_host}")
        print(f"   Database: {os.getenv('POSTGRES_DATABASE', 'N/A')}")
        print(f"   User: {os.getenv('POSTGRES_USER', 'N/A')}")
        
        success, result = test_connection_params(
            postgres_host,
            os.getenv("POSTGRES_DATABASE"),
            os.getenv("POSTGRES_USER"),
            os.getenv("POSTGRES_PASSWORD"),
            int(os.getenv("POSTGRES_PORT", 5432)),
            os.getenv("POSTGRES_SSLMODE", "require")
        )
        
        if success:
            print(f"   ✅ Conexão: OK")
            return True
        else:
            print(f"   ❌ Conexão: {result}")
    
    if not configs_found:
        print("❌ Nenhuma configuração encontrada")
    
    return False

def main():
    """Função principal"""
    print("🚀 Configurador do Neon DB - Sistema de Compras")
    print("=" * 50)
    
    # Verifica se psycopg2 está instalado
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 não está instalado!")
        print("📦 Execute: pip install psycopg2-binary")
        return 1
    
    # Verifica configurações existentes
    if check_existing_config():
        print("\n🎉 Configuração válida encontrada!")
        print("✅ Você pode executar: python setup_neon_db.py")
        return 0
    
    print("\n🔧 Configuração necessária...")
    
    # Pergunta se quer configurar
    while True:
        choice = input("\n❓ Deseja configurar agora? (s/n): ").strip().lower()
        if choice in ['s', 'sim', 'y', 'yes']:
            break
        elif choice in ['n', 'não', 'nao', 'no']:
            print("⚠️ Configure as credenciais antes de executar o setup.")
            return 1
        else:
            print("❓ Responda 's' para sim ou 'n' para não")
    
    # Cria configuração
    if create_secrets_file():
        print("\n🎉 Configuração concluída!")
        print("✅ Agora você pode executar: python setup_neon_db.py")
        return 0
    else:
        print("\n❌ Falha na configuração. Verifique as credenciais.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
