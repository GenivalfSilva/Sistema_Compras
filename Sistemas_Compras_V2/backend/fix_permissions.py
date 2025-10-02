#!/usr/bin/env python
"""
Script para adicionar a permissão can_create_solicitation ao usuário Leonardo.Fragoso
"""

import os
import sys
import django

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')
django.setup()

# Importar modelos após configurar o ambiente
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def add_permission_to_user(username, permission_name):
    """Adiciona uma permissão ao usuário especificado."""
    try:
        with transaction.atomic():
            user = User.objects.get(username=username)
            
            # Verificar se o usuário já tem permissões
            if not hasattr(user, 'permissions') or user.permissions is None:
                user.permissions = {}
            
            # Adicionar a permissão
            user.permissions[permission_name] = True
            user.save()
            
            print(f"Permissão '{permission_name}' adicionada ao usuário '{username}'")
            print(f"Permissões atuais: {user.permissions}")
            
            return True
    except User.DoesNotExist:
        print(f"Usuário '{username}' não encontrado")
        return False
    except Exception as e:
        print(f"Erro ao adicionar permissão: {e}")
        return False

if __name__ == "__main__":
    # Adicionar permissão ao usuário Leonardo.Fragoso
    add_permission_to_user("Leonardo.Fragoso", "can_create_solicitation")
