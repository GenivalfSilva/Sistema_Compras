#!/usr/bin/env python3
"""
Script de migração de dados existentes para PostgreSQL local
Migra dados do Railway/Supabase/Neon para PostgreSQL local na EC2
"""

import json
import os
import sys
from database_local import get_local_database

def migrate_from_railway():
    """Migra dados do Railway PostgreSQL"""
    try:
        # Importar database atual para acessar Railway
        from database import get_database
        
        # Conectar ao Railway
        railway_db = get_database(use_cloud_db=True)
        if not railway_db.db_available:
            print("❌ Railway não disponível")
            return False
        
        # Conectar ao PostgreSQL local
        local_db = get_local_database()
        if not local_db.db_available:
            print("❌ PostgreSQL local não disponível")
            return False
        
        print("🔄 Migrando dados do Railway para PostgreSQL local...")
        
        # Migrar usuários
        print("👥 Migrando usuários...")
        usuarios = railway_db.get_all_users()
        for usuario in usuarios:
            local_db.add_user(
                usuario['username'],
                usuario['nome'],
                usuario['perfil'],
                usuario['departamento'],
                usuario['senha_hash'],
                is_hashed=True
            )
        print(f"✅ {len(usuarios)} usuários migrados")
        
        # Migrar solicitações
        print("📋 Migrando solicitações...")
        solicitacoes = railway_db.get_all_solicitacoes()
        for sol in solicitacoes:
            local_db.add_solicitacao(sol)
        print(f"✅ {len(solicitacoes)} solicitações migradas")
        
        # Migrar configurações
        print("⚙️ Migrando configurações...")
        config_keys = ['sla_urgente', 'sla_alta', 'sla_normal', 'sla_baixa', 
                       'empresa_nome', 'sistema_versao', 'max_upload_size']
        
        for key in config_keys:
            value = railway_db.get_config(key)
            if value:
                local_db.set_config(key, value)
        print("✅ Configurações migradas")
        
        # Migrar catálogo de produtos
        print("📦 Migrando catálogo...")
        produtos = railway_db.get_catalogo_produtos()
        if produtos:
            local_db.update_catalogo_produtos(produtos)
        print(f"✅ {len(produtos)} produtos migrados")
        
        print("🎉 Migração do Railway concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração do Railway: {e}")
        return False

def migrate_from_json(json_file):
    """Migra dados de arquivo JSON"""
    try:
        if not os.path.exists(json_file):
            print(f"❌ Arquivo {json_file} não encontrado")
            return False
        
        local_db = get_local_database()
        if not local_db.db_available:
            print("❌ PostgreSQL local não disponível")
            return False
        
        print(f"🔄 Migrando dados de {json_file}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Migrar usuários
        if 'usuarios' in data:
            print("👥 Migrando usuários...")
            for usuario in data['usuarios']:
                local_db.add_user(
                    usuario['username'],
                    usuario['nome'],
                    usuario['perfil'],
                    usuario['departamento'],
                    usuario['senha_hash'],
                    is_hashed=True
                )
            print(f"✅ {len(data['usuarios'])} usuários migrados")
        
        # Migrar solicitações
        if 'solicitacoes' in data:
            print("📋 Migrando solicitações...")
            for sol in data['solicitacoes']:
                local_db.add_solicitacao(sol)
            print(f"✅ {len(data['solicitacoes'])} solicitações migradas")
        
        # Migrar configurações
        if 'configuracoes' in data:
            print("⚙️ Migrando configurações...")
            for key, value in data['configuracoes'].items():
                local_db.set_config(key, str(value))
            print("✅ Configurações migradas")
        
        # Migrar catálogo
        if 'catalogo_produtos' in data:
            print("📦 Migrando catálogo...")
            local_db.update_catalogo_produtos(data['catalogo_produtos'])
            print(f"✅ {len(data['catalogo_produtos'])} produtos migrados")
        
        print("🎉 Migração do JSON concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na migração do JSON: {e}")
        return False

def export_to_json(output_file):
    """Exporta dados do PostgreSQL local para JSON (backup)"""
    try:
        local_db = get_local_database()
        if not local_db.db_available:
            print("❌ PostgreSQL local não disponível")
            return False
        
        print(f"📤 Exportando dados para {output_file}...")
        
        data = {
            'usuarios': local_db.get_all_users(),
            'solicitacoes': local_db.get_all_solicitacoes(),
            'catalogo_produtos': local_db.get_catalogo_produtos(),
            'configuracoes': {}
        }
        
        # Exportar configurações
        config_keys = ['sla_urgente', 'sla_alta', 'sla_normal', 'sla_baixa', 
                       'empresa_nome', 'sistema_versao', 'max_upload_size']
        
        for key in config_keys:
            value = local_db.get_config(key)
            if value:
                data['configuracoes'][key] = value
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Dados exportados para {output_file}")
        print(f"📊 Estatísticas:")
        print(f"   - Usuários: {len(data['usuarios'])}")
        print(f"   - Solicitações: {len(data['solicitacoes'])}")
        print(f"   - Produtos: {len(data['catalogo_produtos'])}")
        print(f"   - Configurações: {len(data['configuracoes'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")
        return False

def verify_migration():
    """Verifica integridade dos dados migrados"""
    try:
        local_db = get_local_database()
        if not local_db.db_available:
            print("❌ PostgreSQL local não disponível")
            return False
        
        print("🔍 Verificando integridade dos dados...")
        
        # Verificar usuários
        usuarios = local_db.get_all_users()
        print(f"👥 Usuários: {len(usuarios)}")
        
        # Verificar solicitações
        solicitacoes = local_db.get_all_solicitacoes()
        print(f"📋 Solicitações: {len(solicitacoes)}")
        
        # Verificar produtos
        produtos = local_db.get_catalogo_produtos()
        print(f"📦 Produtos: {len(produtos)}")
        
        # Verificar configurações
        config_keys = ['sla_urgente', 'sla_alta', 'sla_normal', 'sla_baixa']
        configs_ok = 0
        for key in config_keys:
            if local_db.get_config(key):
                configs_ok += 1
        print(f"⚙️ Configurações: {configs_ok}/{len(config_keys)}")
        
        # Teste de autenticação
        print("🔐 Testando autenticação...")
        test_user = local_db.authenticate_user('admin', 'admin123')
        if test_user:
            print("✅ Autenticação funcionando")
        else:
            print("❌ Problema na autenticação")
        
        print("✅ Verificação concluída")
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

def main():
    """Função principal"""
    print("🔄 Script de Migração para PostgreSQL Local")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python migrate_to_local_postgres.py railway          # Migrar do Railway")
        print("  python migrate_to_local_postgres.py json <arquivo>   # Migrar de JSON")
        print("  python migrate_to_local_postgres.py export <arquivo> # Exportar para JSON")
        print("  python migrate_to_local_postgres.py verify           # Verificar dados")
        sys.exit(1)
    
    comando = sys.argv[1].lower()
    
    if comando == 'railway':
        success = migrate_from_railway()
    elif comando == 'json':
        if len(sys.argv) < 3:
            print("❌ Especifique o arquivo JSON")
            sys.exit(1)
        success = migrate_from_json(sys.argv[2])
    elif comando == 'export':
        if len(sys.argv) < 3:
            print("❌ Especifique o arquivo de saída")
            sys.exit(1)
        success = export_to_json(sys.argv[2])
    elif comando == 'verify':
        success = verify_migration()
    else:
        print(f"❌ Comando '{comando}' não reconhecido")
        sys.exit(1)
    
    if success:
        print("\n🎉 Operação concluída com sucesso!")
    else:
        print("\n❌ Operação falhou")
        sys.exit(1)

if __name__ == "__main__":
    main()
