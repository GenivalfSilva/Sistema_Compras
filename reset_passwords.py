#!/usr/bin/env python3
"""
Script para resetar senhas específicas no Neon DB
"""

import hashlib
import os
from database import DatabaseManager

def reset_passwords():
    """Reseta senhas para valores conhecidos"""
    
    # Configurações das novas senhas
    password_updates = {
        'Leonardo.Fragoso': 'Teste123',
        'Genival.Silva': 'Teste123', 
        'Diretoria': 'Teste123',
        'admin': 'admin123'
    }
    
    print("Iniciando reset de senhas...")
    
    # Conecta ao banco
    db = DatabaseManager()
    
    if not db.db_available:
        print("❌ Erro: Banco de dados não disponível")
        return False
    
    success_count = 0
    
    for username, new_password in password_updates.items():
        try:
            # Gera hash SHA256 da nova senha
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            # Atualiza a senha no banco
            cursor = db.conn.cursor()
            
            # Usa o método _sql para compatibilidade
            sql = "UPDATE usuarios SET senha_hash = ? WHERE username = ?"
            sql = db._sql(sql)
                
            cursor.execute(sql, (password_hash, username))
            
            if cursor.rowcount > 0:
                print(f"✅ Senha atualizada para {username}")
                success_count += 1
            else:
                print(f"⚠️  Usuário {username} não encontrado")
                
        except Exception as e:
            print(f"❌ Erro ao atualizar senha de {username}: {e}")
    
    # Commit das alterações
    try:
        db.conn.commit()
        print(f"\n✅ Reset concluído! {success_count} senhas atualizadas.")
        
        # Mostra as credenciais
        print("\n🔑 Credenciais atualizadas:")
        for username, password in password_updates.items():
            print(f"   {username} : {password}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar alterações: {e}")
        db.conn.rollback()
        return False

if __name__ == "__main__":
    reset_passwords()
