#!/usr/bin/env python3
"""
Script para inicializar usuários padrão no PostgreSQL local da EC2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_local import get_local_database

def setup_default_users():
    """Cria usuários padrão no sistema"""
    
    print("🔧 Configurando usuários padrão no PostgreSQL local...")
    
    db = get_local_database()
    
    if not db.db_available:
        print("❌ Erro: PostgreSQL local não está disponível")
        return False
    
    # Usuários padrão baseados na memória do sistema
    default_users = [
        {
            "username": "admin",
            "nome": "Administrador",
            "perfil": "Admin",
            "departamento": "TI",
            "senha": "admin123"
        },
        {
            "username": "Leonardo.Fragoso",
            "nome": "Leonardo Fragoso",
            "perfil": "Solicitante",
            "departamento": "TI",
            "senha": "Teste123"
        },
        {
            "username": "Genival.Silva",
            "nome": "Genival Silva",
            "perfil": "Solicitante",
            "departamento": "Operações",
            "senha": "Teste123"
        },
        {
            "username": "Diretoria",
            "nome": "Diretoria",
            "perfil": "Gerência&Diretoria",
            "departamento": "Diretoria",
            "senha": "Teste123"
        },
        {
            "username": "Fabio.Ramos",
            "nome": "Fábio Ramos",
            "perfil": "Suprimentos",
            "departamento": "Suprimentos",
            "senha": "Teste123"
        },
        {
            "username": "Estoque.Sistema",
            "nome": "Responsável Estoque",
            "perfil": "Estoque",
            "departamento": "Estoque",
            "senha": "Teste123"
        }
    ]
    
    # Verifica usuários existentes
    existing_users = {u.get('username', '').lower() for u in db.get_all_users()}
    
    created_count = 0
    for user_data in default_users:
        username = user_data['username']
        
        if username.lower() in existing_users:
            print(f"⚠️  Usuário {username} já existe - pulando")
            continue
        
        success = db.add_user(
            username=username,
            nome=user_data['nome'],
            perfil=user_data['perfil'],
            departamento=user_data['departamento'],
            senha_hash=user_data['senha']  # database_local.py fará o hash
        )
        
        if success:
            print(f"✅ Usuário {username} criado com sucesso")
            created_count += 1
        else:
            print(f"❌ Erro ao criar usuário {username}")
    
    print(f"\n🎉 Setup concluído! {created_count} usuários criados.")
    
    # Configura configurações padrão
    print("\n🔧 Configurando parâmetros padrão...")
    
    default_configs = {
        'proximo_numero_solicitacao': '1',
        'proximo_numero_requisicao': '1',
        'proximo_numero_pedido': '1',
        'limite_gerencia': '5000.0',
        'limite_diretoria': '15000.0',
        'upload_dir': 'uploads',
        'suprimentos_min_cotacoes': '1',
        'suprimentos_anexo_obrigatorio': 'True'
    }
    
    for key, value in default_configs.items():
        if db.set_config(key, value):
            print(f"✅ Configuração {key} definida")
        else:
            print(f"❌ Erro ao definir configuração {key}")
    
    print("\n🚀 Sistema pronto para uso!")
    print("\n📋 Credenciais de acesso:")
    print("- admin / admin123 (Administrador)")
    print("- Leonardo.Fragoso / Teste123 (Solicitante)")
    print("- Genival.Silva / Teste123 (Solicitante)")
    print("- Diretoria / Teste123 (Aprovador)")
    print("- Fabio.Ramos / Teste123 (Suprimentos)")
    print("- Estoque.Sistema / Teste123 (Estoque)")
    
    return True

if __name__ == "__main__":
    try:
        setup_default_users()
    except Exception as e:
        print(f"❌ Erro durante setup: {e}")
        sys.exit(1)
