#!/usr/bin/env python3
"""
Script para configurar PostgreSQL local no Windows como fallback
"""

import subprocess
import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def check_postgres_service():
    """Verifica se o serviço PostgreSQL está rodando"""
    try:
        result = subprocess.run(['sc', 'query', 'postgresql-x64-13'], 
                              capture_output=True, text=True, shell=True)
        if 'RUNNING' in result.stdout:
            print("✅ Serviço PostgreSQL está rodando")
            return True
        else:
            print("❌ Serviço PostgreSQL não está rodando")
            return False
    except Exception as e:
        print(f"⚠️ Não foi possível verificar o serviço PostgreSQL: {e}")
        return False

def start_postgres_service():
    """Tenta iniciar o serviço PostgreSQL"""
    try:
        print("🔄 Tentando iniciar o serviço PostgreSQL...")
        result = subprocess.run(['net', 'start', 'postgresql-x64-13'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("✅ Serviço PostgreSQL iniciado com sucesso")
            return True
        else:
            print(f"❌ Falha ao iniciar PostgreSQL: {result.stderr}")
            # Tenta outras versões comuns
            for version in ['postgresql-x64-14', 'postgresql-x64-12', 'postgresql-x64-15']:
                try:
                    result = subprocess.run(['net', 'start', version], 
                                          capture_output=True, text=True, shell=True)
                    if result.returncode == 0:
                        print(f"✅ Serviço PostgreSQL ({version}) iniciado com sucesso")
                        return True
                except:
                    continue
            return False
    except Exception as e:
        print(f"❌ Erro ao tentar iniciar PostgreSQL: {e}")
        return False

def test_connection_configs():
    """Testa diferentes configurações de conexão"""
    configs = [
        {
            'name': 'Configuração padrão',
            'params': {
                'host': 'localhost',
                'database': 'postgres',
                'user': 'postgres',
                'password': 'postgres',
                'port': 5432
            }
        },
        {
            'name': 'Configuração alternativa 1',
            'params': {
                'host': 'localhost',
                'database': 'postgres',
                'user': 'postgres',
                'password': 'admin',
                'port': 5432
            }
        },
        {
            'name': 'Configuração alternativa 2',
            'params': {
                'host': '127.0.0.1',
                'database': 'postgres',
                'user': 'postgres',
                'password': 'postgres123',
                'port': 5432
            }
        }
    ]
    
    working_config = None
    
    for config in configs:
        try:
            print(f"🔄 Testando {config['name']}...")
            conn = psycopg2.connect(cursor_factory=RealDictCursor, **config['params'])
            cursor = conn.cursor()
            cursor.execute('SELECT version()')
            version = cursor.fetchone()[0]
            print(f"✅ {config['name']} funcionou!")
            print(f"   PostgreSQL: {version}")
            working_config = config
            conn.close()
            break
        except Exception as e:
            print(f"❌ {config['name']} falhou: {e}")
            continue
    
    return working_config

def create_sistema_compras_db(config):
    """Cria o banco sistema_compras se não existir"""
    try:
        print("🔄 Verificando/criando banco sistema_compras...")
        conn = psycopg2.connect(**config['params'])
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verifica se o banco existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'sistema_compras'")
        if not cursor.fetchone():
            cursor.execute("CREATE DATABASE sistema_compras")
            print("✅ Banco sistema_compras criado com sucesso")
        else:
            print("✅ Banco sistema_compras já existe")
        
        conn.close()
        
        # Testa conexão com o banco sistema_compras
        test_config = config['params'].copy()
        test_config['database'] = 'sistema_compras'
        test_conn = psycopg2.connect(**test_config)
        test_conn.close()
        print("✅ Conexão com sistema_compras confirmada")
        
        return test_config
        
    except Exception as e:
        print(f"❌ Erro ao criar/verificar banco sistema_compras: {e}")
        return None

def setup_environment_variables(config):
    """Configura variáveis de ambiente para a aplicação"""
    try:
        print("🔄 Configurando variáveis de ambiente...")
        
        # Cria arquivo .env local
        env_content = f"""# Configuração PostgreSQL Local
PGHOST={config['host']}
PGPORT={config['port']}
PGDATABASE={config['database']}
PGUSER={config['user']}
PGPASSWORD={config['password']}
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ Arquivo .env criado com configurações do PostgreSQL")
        print("💡 Dica: Adicione python-dotenv ao requirements.txt se necessário")
        
    except Exception as e:
        print(f"❌ Erro ao configurar variáveis de ambiente: {e}")

def main():
    """Função principal"""
    print("🚀 Configurando PostgreSQL local para Sistema de Compras")
    print("=" * 60)
    
    # 1. Verifica se PostgreSQL está rodando
    if not check_postgres_service():
        if not start_postgres_service():
            print("\n❌ Não foi possível iniciar o PostgreSQL")
            print("💡 Instale o PostgreSQL em: https://www.postgresql.org/download/windows/")
            return False
    
    # 2. Testa configurações de conexão
    print("\n🔍 Testando configurações de conexão...")
    working_config = test_connection_configs()
    
    if not working_config:
        print("\n❌ Nenhuma configuração de conexão funcionou")
        print("💡 Verifique usuário/senha do PostgreSQL")
        return False
    
    # 3. Cria banco sistema_compras
    print(f"\n🔧 Usando configuração: {working_config['name']}")
    db_config = create_sistema_compras_db(working_config)
    
    if not db_config:
        return False
    
    # 4. Configura variáveis de ambiente
    setup_environment_variables(db_config)
    
    print("\n✅ Configuração concluída com sucesso!")
    print("🎯 Agora você pode executar: streamlit run app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
