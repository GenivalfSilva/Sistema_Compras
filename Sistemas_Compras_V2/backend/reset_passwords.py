#!/usr/bin/env python
"""
Script para redefinir todas as senhas de usuários para 'Teste123'
"""
import os
import sys
import sqlite3
import hashlib
import django

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')
django.setup()

# Importar modelos após configurar o ambiente
from apps.usuarios.models import Usuario

def reset_passwords():
    """
    Redefine todas as senhas para 'Teste123' e gera o hash SHA256 correto
    """
    # Senha padrão
    default_password = "Teste123"
    
    # Gerar hash SHA256 com salt
    salt = "sistema_compras_2024"
    password_with_salt = f"{default_password}{salt}"
    hashed_password = hashlib.sha256(password_with_salt.encode()).hexdigest()
    
    print(f"Redefinindo senhas para '{default_password}'")
    print(f"Hash gerado: {hashed_password}")
    
    # Obter conexão direta com o banco SQLite
    db_path = os.path.join('db', 'sistema_compras_v1.db')
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados não encontrado em {db_path}")
        return False
    
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela usuarios existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if not cursor.fetchone():
            print("Erro: Tabela 'usuarios' não encontrada no banco de dados")
            conn.close()
            return False
        
        # Obter todos os usuários
        cursor.execute("SELECT username, senha_hash FROM usuarios")
        users = cursor.fetchall()
        
        if not users:
            print("Nenhum usuário encontrado no banco de dados")
            conn.close()
            return False
        
        print(f"Encontrados {len(users)} usuários:")
        for username, old_hash in users:
            print(f"- {username} (hash antigo: {old_hash[:10]}...)")
        
        # Atualizar senhas
        cursor.execute("UPDATE usuarios SET senha_hash = ?", (hashed_password,))
        conn.commit()
        
        # Verificar se as senhas foram atualizadas
        cursor.execute("SELECT username, senha_hash FROM usuarios")
        updated_users = cursor.fetchall()
        
        print("\nSenhas atualizadas com sucesso:")
        for username, new_hash in updated_users:
            print(f"- {username} (novo hash: {new_hash})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erro ao atualizar senhas: {str(e)}")
        return False

if __name__ == "__main__":
    print("Iniciando redefinição de senhas...")
    if reset_passwords():
        print("\nTodas as senhas foram redefinidas para 'Teste123' com sucesso!")
        print("Agora você pode fazer login com qualquer usuário usando a senha 'Teste123'")
    else:
        print("\nFalha ao redefinir senhas. Verifique os erros acima.")
