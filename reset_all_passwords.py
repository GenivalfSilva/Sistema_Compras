#!/usr/bin/env python3
"""
Script para resetar a senha de todos os usuários para "Teste123"
"""

import os
import sys
import hashlib

# Adiciona o diretório atual ao path para importar database_local
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_local import get_local_database, SALT

def reset_all_passwords():
    """Reseta a senha de todos os usuários para 'Teste123'"""
    
    # Nova senha padrão
    nova_senha = "Teste123"
    
    # Gera hash da nova senha usando o mesmo método do sistema
    senha_hash = hashlib.sha256((SALT + nova_senha).encode("utf-8")).hexdigest()
    
    # Conecta ao banco
    db = get_local_database()
    
    if not db.db_available:
        print("❌ Erro: Banco de dados não disponível")
        return False
    
    try:
        cursor = db.conn.cursor()
        
        # Busca todos os usuários
        cursor.execute('SELECT username, nome, perfil FROM usuarios')
        usuarios = cursor.fetchall()
        
        if not usuarios:
            print("⚠️ Nenhum usuário encontrado no banco de dados")
            return True
        
        print(f"🔄 Encontrados {len(usuarios)} usuários. Resetando senhas...")
        print("-" * 60)
        
        # Atualiza a senha de todos os usuários
        cursor.execute('UPDATE usuarios SET senha_hash = ?', (senha_hash,))
        
        # Confirma as alterações
        db.conn.commit()
        
        # Lista os usuários atualizados
        print("✅ Senhas atualizadas para todos os usuários:")
        for usuario in usuarios:
            user_dict = dict(usuario)
            print(f"   👤 {user_dict['username']} ({user_dict['nome']}) - {user_dict['perfil']}")
        
        print("-" * 60)
        print(f"🔑 Nova senha para TODOS os usuários: {nova_senha}")
        print("✅ Operação concluída com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao resetar senhas: {e}")
        db.conn.rollback()
        return False

def main():
    """Função principal"""
    print("🔐 Script de Reset de Senhas - Sistema de Compras")
    print("=" * 60)
    print("⚠️  ATENÇÃO: Este script irá alterar a senha de TODOS os usuários!")
    print(f"📝 Nova senha será: 'Teste123'")
    print("=" * 60)
    
    # Confirmação do usuário
    resposta = input("Deseja continuar? (s/N): ").strip().lower()
    
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("❌ Operação cancelada pelo usuário")
        return False
    
    # Executa o reset
    success = reset_all_passwords()
    
    if success:
        print("\n🎯 Dicas:")
        print("   • Use 'Teste123' para fazer login com qualquer usuário")
        print("   • Recomenda-se alterar as senhas após o primeiro login")
        print("   • Este script pode ser executado novamente se necessário")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
