#!/usr/bin/env python3
"""
Script para debug da conexão Supabase
"""

import psycopg2
import sys

def test_connections():
    """Testa diferentes configurações de conexão"""
    
    # Configurações para testar
    configs = [
        {
            "name": "Connection String Padrão",
            "conn_str": "postgresql://postgres:232315@db.amusiwxxishpynwzglmk.supabase.co:5432/postgres"
        },
        {
            "name": "Connection String com SSL require",
            "conn_str": "postgresql://postgres:232315@db.amusiwxxishpynwzglmk.supabase.co:5432/postgres?sslmode=require"
        },
        {
            "name": "Connection String com SSL disable",
            "conn_str": "postgresql://postgres:232315@db.amusiwxxishpynwzglmk.supabase.co:5432/postgres?sslmode=disable"
        },
        {
            "name": "Parâmetros individuais",
            "params": {
                "host": "db.amusiwxxishpynwzglmk.supabase.co",
                "port": 5432,
                "database": "postgres",
                "user": "postgres",
                "password": "232315",
                "sslmode": "require"
            }
        },
        {
            "name": "Parâmetros individuais sem SSL",
            "params": {
                "host": "db.amusiwxxishpynwzglmk.supabase.co",
                "port": 5432,
                "database": "postgres",
                "user": "postgres",
                "password": "232315",
                "sslmode": "disable"
            }
        }
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n{i}. Testando: {config['name']}")
        print("-" * 50)
        
        try:
            if "conn_str" in config:
                conn = psycopg2.connect(config["conn_str"])
            else:
                conn = psycopg2.connect(**config["params"])
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            print(f"✅ SUCESSO!")
            print(f"   PostgreSQL: {version[0][:80]}...")
            
            # Testa criação de tabela
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50)
                )
            """)
            
            cursor.execute("INSERT INTO test_table (name) VALUES ('test') ON CONFLICT DO NOTHING")
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM test_table")
            count = cursor.fetchone()[0]
            print(f"   Tabela de teste criada com {count} registro(s)")
            
            cursor.close()
            conn.close()
            
            print(f"🎉 CONFIGURAÇÃO FUNCIONOU!")
            print(f"   Use esta configuração no sistema:")
            if "conn_str" in config:
                print(f"   {config['conn_str']}")
            else:
                print(f"   {config['params']}")
            
            return True
            
        except Exception as e:
            print(f"❌ FALHOU: {e}")
            print(f"   Tipo: {type(e).__name__}")
    
    return False

def main():
    print("🔍 Debug de Conexão Supabase")
    print("=" * 60)
    
    if test_connections():
        print(f"\n🎯 Encontrou configuração que funciona!")
    else:
        print(f"\n❌ Nenhuma configuração funcionou")
        print(f"\n🔧 Possíveis soluções:")
        print(f"1. Verifique se o projeto Supabase está ativo")
        print(f"2. Confirme a senha no dashboard")
        print(f"3. Verifique se não há firewall bloqueando")
        print(f"4. Tente resetar a senha do banco no Supabase")

if __name__ == "__main__":
    main()
