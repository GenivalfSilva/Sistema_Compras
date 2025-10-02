#!/usr/bin/env python
"""
Script para sincronizar permissões com base nos perfis dos usuários
"""

import os
import sys
import django
import json

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')
django.setup()

# Importar modelos após configurar o ambiente
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

# Mapeamento de perfis para permissões
ROLE_PERMISSIONS = {
    'Solicitante': ['can_create_solicitation'],
    'Estoque': ['can_manage_stock'],
    'Suprimentos': ['can_manage_procurement'],
    'Diretoria': ['can_approve'],
    'Admin': ['is_admin', 'can_create_solicitation', 'can_manage_stock', 'can_manage_procurement', 'can_approve'],
}

def sync_permissions_by_role():
    """Sincroniza as permissões de todos os usuários com base em seus perfis."""
    try:
        with transaction.atomic():
            users = User.objects.all()
            updated_users = 0
            
            for user in users:
                perfil = getattr(user, 'perfil', None)
                if not perfil:
                    print(f"Usuário '{user.username}' não tem perfil definido")
                    continue
                
                permissions_to_add = ROLE_PERMISSIONS.get(perfil, [])
                if not permissions_to_add:
                    print(f"Perfil '{perfil}' não tem permissões mapeadas")
                    continue
                
                # Inicializar permissions se não existir
                if not hasattr(user, 'permissions') or user.permissions is None:
                    user.permissions = {}
                
                # Adicionar permissões com base no perfil
                updated = False
                for permission in permissions_to_add:
                    if permission not in user.permissions or not user.permissions.get(permission):
                        user.permissions[permission] = True
                        updated = True
                
                if updated:
                    user.save()
                    updated_users += 1
                    print(f"Atualizadas permissões para '{user.username}' (Perfil: {perfil})")
                    print(f"  Permissões: {json.dumps(user.permissions, indent=2)}")
            
            print(f"\nTotal de usuários atualizados: {updated_users}")
            return updated_users
    except Exception as e:
        print(f"Erro ao sincronizar permissões: {e}")
        return 0

def fix_specific_user(username):
    """Corrige as permissões para um usuário específico."""
    try:
        with transaction.atomic():
            user = User.objects.get(username=username)
            perfil = getattr(user, 'perfil', None)
            
            if not perfil:
                print(f"Usuário '{username}' não tem perfil definido")
                return False
            
            permissions_to_add = ROLE_PERMISSIONS.get(perfil, [])
            if not permissions_to_add:
                print(f"Perfil '{perfil}' não tem permissões mapeadas")
                return False
            
            # Inicializar permissions se não existir
            if not hasattr(user, 'permissions') or user.permissions is None:
                user.permissions = {}
            
            # Adicionar permissões com base no perfil
            updated = False
            for permission in permissions_to_add:
                if permission not in user.permissions or not user.permissions.get(permission):
                    user.permissions[permission] = True
                    updated = True
            
            if updated:
                user.save()
                print(f"Atualizadas permissões para '{username}' (Perfil: {perfil})")
                print(f"  Permissões: {json.dumps(user.permissions, indent=2)}")
                return True
            else:
                print(f"Usuário '{username}' já possui todas as permissões necessárias")
                return False
    except User.DoesNotExist:
        print(f"Usuário '{username}' não encontrado")
        return False
    except Exception as e:
        print(f"Erro ao corrigir permissões para '{username}': {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Se um usuário específico foi fornecido como argumento
        username = sys.argv[1]
        print(f"Corrigindo permissões para o usuário: {username}")
        fix_specific_user(username)
    else:
        # Sincronizar todos os usuários
        print("Sincronizando permissões para todos os usuários...")
        sync_permissions_by_role()
