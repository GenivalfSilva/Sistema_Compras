#!/usr/bin/env python
"""
Script para criar um superusuário no Django
"""
import os
import django

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')
django.setup()

# Importar modelo de usuário
from django.contrib.auth.models import User

# Verificar se o superusuário já existe
if not User.objects.filter(username='admin').exists():
    # Criar superusuário
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='Teste123',
        first_name='Administrador'
    )
    print("Superusuário 'admin' criado com senha 'Teste123'")
else:
    print("Superusuário 'admin' já existe")

# Criar usuários normais
users = [
    {
        'username': 'Leonardo.Fragoso',
        'first_name': 'Leonardo Fragoso',
        'password': 'Teste123',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'username': 'Genival.Silva',
        'first_name': 'Genival Silva',
        'password': 'Teste123',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'username': 'Estoque.Sistema',
        'first_name': 'Estoque Sistema',
        'password': 'Teste123',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'username': 'Fabio.Ramos',
        'first_name': 'Fabio Ramos',
        'password': 'Teste123',
        'is_staff': False,
        'is_superuser': False
    },
    {
        'username': 'Diretoria',
        'first_name': 'Diretoria',
        'password': 'Teste123',
        'is_staff': False,
        'is_superuser': False
    }
]

for user_data in users:
    if not User.objects.filter(username=user_data['username']).exists():
        User.objects.create_user(
            username=user_data['username'],
            first_name=user_data['first_name'],
            password=user_data['password'],
            is_staff=user_data['is_staff'],
            is_superuser=user_data['is_superuser']
        )
        print(f"Usuário '{user_data['username']}' criado com senha 'Teste123'")
    else:
        print(f"Usuário '{user_data['username']}' já existe")

print("\nTodos os usuários foram criados com sucesso!")
