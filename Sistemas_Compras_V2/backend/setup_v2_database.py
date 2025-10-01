#!/usr/bin/env python
"""
Script para configurar um novo banco de dados V2 com os usuários padrão
"""
import os
import sys
import hashlib
import django

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')
django.setup()

# Importar modelos após configurar o ambiente
from django.contrib.auth.models import User
from apps.usuarios.models import Usuario

def setup_database():
    """
    Configura um novo banco de dados V2 com os usuários padrão
    """
    # Lista de usuários padrão
    default_users = [
        {
            'username': 'Leonardo.Fragoso',
            'nome': 'Leonardo Fragoso',
            'perfil': 'Solicitante',
            'departamento': 'TI',
            'password': 'Teste123'
        },
        {
            'username': 'Genival.Silva',
            'nome': 'Genival Silva',
            'perfil': 'Solicitante',
            'departamento': 'Produção',
            'password': 'Teste123'
        },
        {
            'username': 'Estoque.Sistema',
            'nome': 'Estoque Sistema',
            'perfil': 'Estoque',
            'departamento': 'Estoque',
            'password': 'Teste123'
        },
        {
            'username': 'Fabio.Ramos',
            'nome': 'Fabio Ramos',
            'perfil': 'Suprimentos',
            'departamento': 'Suprimentos',
            'password': 'Teste123'
        },
        {
            'username': 'Diretoria',
            'nome': 'Diretoria',
            'perfil': 'Gerência&Diretoria',
            'departamento': 'Diretoria',
            'password': 'Teste123'
        },
        {
            'username': 'admin',
            'nome': 'Administrador',
            'perfil': 'Admin',
            'departamento': 'TI',
            'password': 'Teste123'
        }
    ]
    
    # Gerar hash SHA256 com salt
    def generate_hash(password):
        salt = "sistema_compras_2024"
        password_with_salt = f"{password}{salt}"
        return hashlib.sha256(password_with_salt.encode()).hexdigest()
    
    print("Criando usuários padrão...")
    
    # Criar usuários no modelo V1 (Usuario)
    for user_data in default_users:
        # Verificar se o usuário já existe
        if not Usuario.objects.filter(username=user_data['username']).exists():
            # Criar usuário no modelo V1
            Usuario.objects.create(
                username=user_data['username'],
                nome=user_data['nome'],
                perfil=user_data['perfil'],
                departamento=user_data['departamento'],
                senha_hash=generate_hash(user_data['password'])
            )
            print(f"Usuário V1 criado: {user_data['username']} ({user_data['perfil']})")
        else:
            print(f"Usuário V1 já existe: {user_data['username']}")
        
        # Criar usuário no modelo Django (User)
        if not User.objects.filter(username=user_data['username']).exists():
            # Criar usuário Django
            user = User.objects.create_user(
                username=user_data['username'],
                first_name=user_data['nome'],
                password=user_data['password'],
                is_staff=user_data['perfil'] == 'Admin',
                is_superuser=user_data['perfil'] == 'Admin'
            )
            print(f"Usuário Django criado: {user_data['username']}")
        else:
            print(f"Usuário Django já existe: {user_data['username']}")
    
    print("\nConfiguração concluída com sucesso!")
    print("Usuários criados com senha padrão 'Teste123'")

if __name__ == "__main__":
    print("Iniciando configuração do banco de dados V2...")
    setup_database()
