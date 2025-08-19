#!/usr/bin/env python3
"""
Script para migrar dados do arquivo JSON para o banco de dados Neon
"""

import json
import os
import sys
from datetime import datetime
from database import get_database

def migrate_json_to_database():
    """Migra dados do JSON para o banco de dados"""
    
    json_file = "compras_sla_data.json"
    
    if not os.path.exists(json_file):
        print(f"❌ Arquivo {json_file} não encontrado.")
        return False
    
    print("🔄 Iniciando migração do JSON para o banco de dados...")
    
    try:
        # Carrega dados do JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📄 Dados carregados do JSON: {len(data.get('solicitacoes', []))} solicitações")
        
        # Conecta ao banco
        db = get_database(use_cloud_db=True)  # Força uso do banco cloud (Neon)
        
        if not db.db_available:
            print("❌ Banco de dados não disponível. Verifique as configurações.")
            return False
        
        print("✅ Conectado ao banco de dados Neon")
        
        # Migra usuários
        usuarios_migrados = 0
        for usuario in data.get('usuarios', []):
            success = db.add_user(
                usuario['username'],
                usuario['nome'],
                usuario['perfil'],
                usuario['departamento'],
                usuario['senha_hash'],
                is_hashed=True
            )
            if success:
                usuarios_migrados += 1
        
        print(f"👥 Usuários migrados: {usuarios_migrados}")
        
        # Migra solicitações
        solicitacoes_migradas = 0
        for solicitacao in data.get('solicitacoes', []):
            success = db.add_solicitacao(solicitacao)
            if success:
                solicitacoes_migradas += 1
            else:
                print(f"⚠️  Falha ao migrar solicitação #{solicitacao.get('numero_solicitacao_estoque')}")
        
        print(f"📋 Solicitações migradas: {solicitacoes_migradas}")
        
        # Migra configurações
        config_migradas = 0
        configuracoes = data.get('configuracoes', {})
        for key, value in configuracoes.items():
            if key != 'catalogo_produtos':  # Catálogo tem tratamento especial
                db.set_config(key, json.dumps(value) if isinstance(value, (dict, list)) else str(value))
                config_migradas += 1
        
        print(f"⚙️  Configurações migradas: {config_migradas}")
        
        # Migra catálogo de produtos
        produtos_migrados = 0
        catalogo = configuracoes.get('catalogo_produtos', [])
        if catalogo:
            success = db.update_catalogo_produtos(catalogo)
            if success:
                produtos_migrados = len(catalogo)
        
        print(f"📦 Produtos do catálogo migrados: {produtos_migrados}")
        
        # Migra notificações
        notif_migradas = 0
        for notif in data.get('notificacoes', []):
            success = db.add_notificacao(
                notif['perfil'],
                notif['numero'],
                notif['mensagem']
            )
            if success:
                notif_migradas += 1
        
        print(f"🔔 Notificações migradas: {notif_migradas}")
        
        print("\n✅ Migração concluída com sucesso!")
        print(f"📊 Resumo:")
        print(f"   - {usuarios_migrados} usuários")
        print(f"   - {solicitacoes_migradas} solicitações")
        print(f"   - {config_migradas} configurações")
        print(f"   - {produtos_migrados} produtos")
        print(f"   - {notif_migradas} notificações")
        
        # Cria backup do JSON
        backup_name = f"compras_sla_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.rename(json_file, backup_name)
        print(f"💾 Backup criado: {backup_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        return False

def test_database_connection():
    """Testa a conexão com o banco de dados"""
    print("🔍 Testando conexão com o banco de dados...")
    
    try:
        db = get_database(use_cloud_db=True)
        
        if not db.db_available:
            print("❌ Banco de dados não disponível")
            return False
        
        print(f"✅ Conectado ao banco: {db.db_type}")
        
        # Testa operações básicas
        usuarios = db.get_all_users()
        print(f"👥 Usuários no banco: {len(usuarios)}")
        
        solicitacoes = db.get_all_solicitacoes()
        print(f"📋 Solicitações no banco: {len(solicitacoes)}")
        
        catalogo = db.get_catalogo_produtos()
        print(f"📦 Produtos no catálogo: {len(catalogo)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar banco: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Script de Migração - Sistema de Compras")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Apenas testa a conexão
        test_database_connection()
    else:
        # Executa migração completa
        if test_database_connection():
            print("\n" + "=" * 50)
            migrate_json_to_database()
        else:
            print("❌ Falha no teste de conexão. Migração cancelada.")
