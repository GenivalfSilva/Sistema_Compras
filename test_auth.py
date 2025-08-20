#!/usr/bin/env python3
"""
Script para testar autenticação do Neon DB
"""
import sys
sys.path.append('.')

from database import get_database
import hashlib

def test_authentication():
    print('=== Testing User Authentication ===')
    db = get_database()
    
    if not db.db_available:
        print('Database not available!')
        return
    
    # Test with known credentials from memory
    test_users = [
        ('Leonardo.Fragoso', 'Teste123'),
        ('Genival.Silva', 'Teste123'),
        ('Diretoria', 'Teste123'),
        ('admin', 'admin123')
    ]
    
    for username, password in test_users:
        result = db.authenticate_user(username, password)
        status = 'SUCCESS' if result else 'FAILED'
        print(f'{username}: {status}')
        if result:
            print(f'  - Nome: {result.get("nome", "N/A")}')
            print(f'  - Perfil: {result.get("perfil", "N/A")}')
    
    # Check what users exist in the database
    print('\n=== Users in Database ===')
    cursor = db.conn.cursor()
    cursor.execute('SELECT username, nome, perfil, senha_hash FROM usuarios') 
    users = cursor.fetchall()
    
    for user in users:
        # Convert to dict for easier access
        user_dict = dict(user) if hasattr(user, 'keys') else {
            'username': user[0], 'nome': user[1], 'perfil': user[2], 'senha_hash': user[3]
        }
        
        username = user_dict['username']
        nome = user_dict['nome']
        perfil = user_dict['perfil']
        stored_hash = user_dict['senha_hash']
        
        print(f'Username: {username}, Nome: {nome}, Perfil: {perfil}')
        
        # Check if password hash matches expected
        expected_hash = hashlib.sha256('Teste123'.encode()).hexdigest()       
        admin_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        
        if username == 'admin':
            matches = stored_hash == admin_hash
        else:
            matches = stored_hash == expected_hash
        print(f'  - Hash matches expected: {matches}')
        print(f'  - Stored hash: {stored_hash[:20]}...')
        print(f'  - Expected hash: {(admin_hash if username == "admin" else expected_hash)[:20]}...')

if __name__ == '__main__':
    test_authentication()
