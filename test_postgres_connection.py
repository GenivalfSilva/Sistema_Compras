#!/usr/bin/env python3
"""
Diagnóstico de conexão PostgreSQL - Windows
"""

import psycopg2
import subprocess
import sys
import os

def test_postgres_service():
    """Testa se o serviço PostgreSQL está rodando"""
    print("🔍 VERIFICANDO SERVIÇO POSTGRESQL")
    print("=" * 40)
    
    try:
        # Tenta encontrar serviços PostgreSQL
        result = subprocess.run(['sc', 'query', 'postgresql'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("✅ Serviço PostgreSQL encontrado")
            print(result.stdout)
        else:
            print("❌ Serviço PostgreSQL não encontrado")
            
        # Tenta versões alternativas
        for service_name in ['postgresql-x64-16', 'postgresql-x64-15', 'postgresql-x64-14']:
            result = subprocess.run(['sc', 'query', service_name], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print(f"✅ Serviço {service_name} encontrado")
                print(result.stdout)
                return True
                
    except Exception as e:
        print(f"❌ Erro ao verificar serviços: {e}")
    
    return False

def test_psql_command():
    """Testa se psql está no PATH"""
    print("\n🔍 VERIFICANDO COMANDO PSQL")
    print("=" * 30)
    
    try:
        result = subprocess.run(['psql', '--version'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("✅ psql encontrado:", result.stdout.strip())
            return True
        else:
            print("❌ psql não encontrado no PATH")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar psql: {e}")
        return False

def test_connection_variations():
    """Testa diferentes variações de conexão"""
    print("\n🔍 TESTANDO CONEXÕES")
    print("=" * 25)
    
    # Diferentes combinações de credenciais
    test_configs = [
        {"host": "localhost", "port": 5432, "user": "postgres", "password": "postgres123", "database": "postgres"},
        {"host": "localhost", "port": 5432, "user": "postgres", "password": "postgres", "database": "postgres"},
        {"host": "127.0.0.1", "port": 5432, "user": "postgres", "password": "postgres123", "database": "postgres"},
        {"host": "localhost", "port": 5433, "user": "postgres", "password": "postgres123", "database": "postgres"},
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n🧪 Teste {i}: {config['user']}@{config['host']}:{config['port']}")
        try:
            conn = psycopg2.connect(**config)
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ SUCESSO! PostgreSQL: {version[:50]}...")
            conn.close()
            return config
        except psycopg2.OperationalError as e:
            print(f"❌ Falha: {e}")
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    return None

def check_postgres_installation():
    """Verifica instalação do PostgreSQL"""
    print("\n🔍 VERIFICANDO INSTALAÇÃO")
    print("=" * 30)
    
    # Locais comuns de instalação
    common_paths = [
        r"C:\Program Files\PostgreSQL",
        r"C:\Program Files (x86)\PostgreSQL",
        r"C:\PostgreSQL",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"✅ PostgreSQL encontrado em: {path}")
            # Lista versões
            try:
                versions = os.listdir(path)
                print(f"   Versões: {', '.join(versions)}")
                return True
            except:
                pass
        else:
            print(f"❌ Não encontrado em: {path}")
    
    return False

def main():
    print("🔧 DIAGNÓSTICO POSTGRESQL - WINDOWS")
    print("=" * 50)
    
    # 1. Verificar instalação
    installation_found = check_postgres_installation()
    
    # 2. Verificar serviços
    service_running = test_postgres_service()
    
    # 3. Verificar psql
    psql_available = test_psql_command()
    
    # 4. Testar conexões
    working_config = test_connection_variations()
    
    print("\n" + "=" * 50)
    print("📋 RESUMO DO DIAGNÓSTICO")
    print("=" * 50)
    print(f"PostgreSQL instalado: {'✅' if installation_found else '❌'}")
    print(f"Serviço rodando: {'✅' if service_running else '❌'}")
    print(f"psql disponível: {'✅' if psql_available else '❌'}")
    print(f"Conexão funciona: {'✅' if working_config else '❌'}")
    
    if working_config:
        print(f"\n🎉 CONFIGURAÇÃO QUE FUNCIONA:")
        print(f"   Host: {working_config['host']}")
        print(f"   Porta: {working_config['port']}")
        print(f"   Usuário: {working_config['user']}")
        print(f"   Senha: {working_config['password']}")
        
        # Criar arquivo de configuração
        config_content = f"""[postgres]
host = "{working_config['host']}"
port = {working_config['port']}
username = "{working_config['user']}"
password = "{working_config['password']}"
database = "sistema_compras"
"""
        
        with open('secrets_local.toml', 'w') as f:
            f.write(config_content)
        print(f"\n✅ Arquivo secrets_local.toml criado!")
        
    else:
        print(f"\n❌ NENHUMA CONEXÃO FUNCIONOU")
        print(f"\n🔧 SOLUÇÕES POSSÍVEIS:")
        print(f"   1. Verificar se PostgreSQL está instalado")
        print(f"   2. Iniciar o serviço PostgreSQL")
        print(f"   3. Verificar credenciais (usuário/senha)")
        print(f"   4. Verificar porta (5432 ou 5433)")
        print(f"   5. Verificar se pg_hba.conf permite conexões locais")

if __name__ == "__main__":
    main()
