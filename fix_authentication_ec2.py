#!/usr/bin/env python3
"""
Script para diagnosticar e corrigir problemas de autenticação no EC2
Verifica e corrige incompatibilidades de hash de senha entre sistemas
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import toml
import os

# Configurações
SALT = "ziran_local_salt_v1"  # Mesmo salt usado no app.py

def hash_password_with_salt(password: str) -> str:
    """Hash com salt (método usado no app.py)"""
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()

def hash_password_plain(password: str) -> str:
    """Hash sem salt (método usado no database_local.py)"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    """Conecta ao PostgreSQL local"""
    try:
        # Tenta carregar configuração do arquivo secrets_local.toml
        config_path = 'secrets_local.toml'
        if os.path.exists(config_path):
            config = toml.load(config_path)
            if 'postgres' in config:
                pg = config['postgres']
                conn = psycopg2.connect(
                    host=pg["host"],
                    database=pg["database"],
                    user=pg["username"],
                    password=pg["password"],
                    port=int(pg.get("port", 5432)),
                    cursor_factory=RealDictCursor,
                )
                return conn
        
        # Fallback para variáveis de ambiente
        db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres123@localhost:5432/sistema_compras')
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        
    except Exception as e:
        print(f"❌ Erro ao conectar PostgreSQL: {e}")
        return None

def diagnose_users(conn):
    """Diagnostica usuários existentes"""
    print("\n🔍 DIAGNÓSTICO DE USUÁRIOS")
    print("=" * 50)
    
    cursor = conn.cursor()
    cursor.execute('SELECT username, nome, perfil, senha_hash FROM usuarios ORDER BY username')
    users = cursor.fetchall()
    
    if not users:
        print("❌ Nenhum usuário encontrado na tabela usuarios")
        return []
    
    print(f"✅ Encontrados {len(users)} usuários:")
    for user in users:
        print(f"  - {user['username']} ({user['perfil']}) - Hash: {user['senha_hash'][:16]}...")
    
    return users

def test_authentication(conn, username, password):
    """Testa autenticação com diferentes métodos de hash"""
    print(f"\n🧪 TESTANDO AUTENTICAÇÃO: {username}")
    print("-" * 40)
    
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE username = %s', (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ Usuário '{username}' não encontrado")
        return False
    
    stored_hash = user['senha_hash']
    
    # Testa hash com salt (app.py)
    hash_with_salt = hash_password_with_salt(password)
    print(f"Hash com salt: {hash_with_salt}")
    
    # Testa hash sem salt (database_local.py)
    hash_plain = hash_password_plain(password)
    print(f"Hash sem salt: {hash_plain}")
    
    print(f"Hash armazenado: {stored_hash}")
    
    if stored_hash == hash_with_salt:
        print("✅ Autenticação OK com método SALT")
        return True
    elif stored_hash == hash_plain:
        print("⚠️  Autenticação OK com método PLAIN (precisa correção)")
        return "needs_fix"
    else:
        print("❌ Falha na autenticação com ambos os métodos")
        return False

def fix_user_password(conn, username, password):
    """Corrige hash da senha para usar método com salt"""
    print(f"\n🔧 CORRIGINDO SENHA: {username}")
    print("-" * 30)
    
    try:
        cursor = conn.cursor()
        correct_hash = hash_password_with_salt(password)
        
        cursor.execute(
            'UPDATE usuarios SET senha_hash = %s WHERE username = %s',
            (correct_hash, username)
        )
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ Senha corrigida para {username}")
            return True
        else:
            print(f"❌ Usuário {username} não encontrado para correção")
            return False
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao corrigir senha: {e}")
        return False

def create_missing_users(conn):
    """Cria usuários padrão se não existirem"""
    print("\n👥 CRIANDO USUÁRIOS PADRÃO")
    print("=" * 30)
    
    default_users = [
        {"username": "admin", "nome": "Administrador", "perfil": "Admin", "departamento": "TI", "senha": "admin123"},
        {"username": "Leonardo.Fragoso", "nome": "Leonardo Fragoso", "perfil": "Solicitante", "departamento": "TI", "senha": "Teste123"},
        {"username": "Genival.Silva", "nome": "Genival Silva", "perfil": "Solicitante", "departamento": "Operações", "senha": "Teste123"},
        {"username": "Diretoria", "nome": "Diretoria", "perfil": "Gerência&Diretoria", "departamento": "Diretoria", "senha": "Teste123"},
        {"username": "Fabio.Ramos", "nome": "Fabio Ramos", "perfil": "Suprimentos", "departamento": "Suprimentos", "senha": "Teste123"},
        {"username": "Estoque.Sistema", "nome": "Estoque Sistema", "perfil": "Estoque", "departamento": "Estoque", "senha": "Teste123"},
    ]
    
    cursor = conn.cursor()
    created_count = 0
    
    for user_data in default_users:
        try:
            # Verifica se usuário já existe
            cursor.execute('SELECT username FROM usuarios WHERE username = %s', (user_data["username"],))
            if cursor.fetchone():
                print(f"⚠️  Usuário {user_data['username']} já existe")
                continue
            
            # Cria usuário com hash correto (com salt)
            senha_hash = hash_password_with_salt(user_data["senha"])
            
            cursor.execute('''
                INSERT INTO usuarios (username, nome, perfil, departamento, senha_hash)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                user_data["username"],
                user_data["nome"],
                user_data["perfil"],
                user_data["departamento"],
                senha_hash
            ))
            
            print(f"✅ Usuário {user_data['username']} criado")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Erro ao criar usuário {user_data['username']}: {e}")
    
    if created_count > 0:
        conn.commit()
        print(f"\n✅ {created_count} usuários criados com sucesso")
    else:
        print("\n✅ Todos os usuários já existem")

def main():
    print("🔐 DIAGNÓSTICO E CORREÇÃO DE AUTENTICAÇÃO - EC2")
    print("=" * 60)
    
    # Conecta ao banco
    conn = get_db_connection()
    if not conn:
        print("❌ Não foi possível conectar ao banco de dados")
        return
    
    print("✅ Conectado ao PostgreSQL local")
    
    try:
        # Diagnóstica usuários existentes
        users = diagnose_users(conn)
        
        # Cria usuários padrão se necessário
        create_missing_users(conn)
        
        # Testa credenciais conhecidas
        test_credentials = [
            ("admin", "admin123"),
            ("Leonardo.Fragoso", "Teste123"),
            ("Genival.Silva", "Teste123"),
            ("Diretoria", "Teste123"),
            ("Fabio.Ramos", "Teste123"),
            ("Estoque.Sistema", "Teste123"),
        ]
        
        print("\n🧪 TESTANDO CREDENCIAIS PADRÃO")
        print("=" * 40)
        
        users_to_fix = []
        
        for username, password in test_credentials:
            result = test_authentication(conn, username, password)
            if result == "needs_fix":
                users_to_fix.append((username, password))
            elif result is False:
                print(f"⚠️  Usuário {username} precisa de correção manual")
        
        # Corrige usuários que precisam
        if users_to_fix:
            print(f"\n🔧 CORRIGINDO {len(users_to_fix)} USUÁRIOS")
            print("=" * 40)
            
            for username, password in users_to_fix:
                fix_user_password(conn, username, password)
        
        # Teste final
        print("\n✅ TESTE FINAL DE AUTENTICAÇÃO")
        print("=" * 40)
        
        all_working = True
        for username, password in test_credentials:
            result = test_authentication(conn, username, password)
            if result is not True:
                all_working = False
        
        if all_working:
            print("\n🎉 SUCESSO! Todos os usuários podem fazer login")
            print("\n📋 CREDENCIAIS DE ACESSO:")
            print("-" * 30)
            for username, password in test_credentials:
                print(f"  {username} / {password}")
        else:
            print("\n⚠️  Alguns usuários ainda têm problemas de autenticação")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
