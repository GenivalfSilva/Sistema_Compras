#!/usr/bin/env python3
"""
Script para migrar dados do JSON para o banco de dados SQLite/PostgreSQL
"""

import os
import sys
import json
from database import get_database

def migrate_json_to_database(json_file="compras_sla_data.json"):
    """Migra dados do arquivo JSON para o banco de dados"""
    
    print(f"🔄 Iniciando migração de {json_file}...")
    
    if not os.path.exists(json_file):
        print(f"❌ Arquivo {json_file} não encontrado!")
        return False
    
    try:
        # Carrega dados do JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📂 Dados carregados: {len(data.get('usuarios', []))} usuários, {len(data.get('solicitacoes', []))} solicitações")
        
        # Inicializa banco de dados
        db = get_database(use_cloud_db=False)  # Usar SQLite local para migração
        
        # Migra usuários
        usuarios_migrados = 0
        for user in data.get('usuarios', []):
            try:
                success = db.add_user(
                    username=user['username'],
                    nome=user['nome'],
                    perfil=user['perfil'],
                    departamento=user['departamento'],
                    senha_hash=user['senha_hash'],
                    is_hashed=True  # Senha já está hasheada
                )
                if success:
                    usuarios_migrados += 1
                    print(f"✅ Usuário migrado: {user['username']} ({user['perfil']})")
                else:
                    print(f"⚠️ Usuário já existe: {user['username']}")
            except Exception as e:
                print(f"❌ Erro ao migrar usuário {user['username']}: {e}")
        
        # Migra configurações
        config_migradas = 0
        configuracoes = data.get('configuracoes', {})
        for key, value in configuracoes.items():
            try:
                # Converte para string JSON se for dict/list
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                
                db.set_config(key, value_str)
                config_migradas += 1
                print(f"✅ Configuração migrada: {key}")
            except Exception as e:
                print(f"❌ Erro ao migrar configuração {key}: {e}")
        
        # TODO: Migrar solicitações (implementar quando necessário)
        # Por enquanto, manter no JSON para compatibilidade
        
        print(f"\n🎉 Migração concluída!")
        print(f"📊 Resumo:")
        print(f"   - Usuários migrados: {usuarios_migrados}")
        print(f"   - Configurações migradas: {config_migradas}")
        print(f"   - Solicitações: mantidas no JSON (compatibilidade)")
        
        # Cria backup do JSON original
        backup_file = f"{json_file}.backup"
        if not os.path.exists(backup_file):
            import shutil
            shutil.copy2(json_file, backup_file)
            print(f"💾 Backup criado: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def test_database():
    """Testa a conexão e estrutura do banco"""
    print("🔍 Testando banco de dados...")
    
    try:
        db = get_database(use_cloud_db=False)
        
        # Testa usuários
        users = db.get_all_users()
        print(f"👥 Usuários no banco: {len(users)}")
        for user in users:
            print(f"   - {user['username']} ({user['perfil']})")
        
        # Testa autenticação
        if users:
            test_user = users[0]
            print(f"🔐 Testando autenticação com usuário: {test_user['username']}")
            # Nota: não podemos testar senha pois está hasheada
        
        print("✅ Banco de dados funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar banco: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Função principal"""
    print("🚀 Sistema de Migração - JSON para Banco de Dados")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_database()
            return
        elif sys.argv[1] == "migrate":
            json_file = sys.argv[2] if len(sys.argv) > 2 else "compras_sla_data.json"
            migrate_json_to_database(json_file)
            return
    
    # Menu interativo
    while True:
        print("\nOpções:")
        print("1. Migrar dados do JSON")
        print("2. Testar banco de dados")
        print("3. Sair")
        
        choice = input("\nEscolha uma opção (1-3): ").strip()
        
        if choice == "1":
            json_file = input("Arquivo JSON (padrão: compras_sla_data.json): ").strip()
            if not json_file:
                json_file = "compras_sla_data.json"
            migrate_json_to_database(json_file)
        
        elif choice == "2":
            test_database()
        
        elif choice == "3":
            print("👋 Saindo...")
            break
        
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    main()
