#!/usr/bin/env python
"""
Script para corrigir permissões dos usuários com base no modelo V1
"""

import os
import sys
import django

# Configurar o ambiente Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')
django.setup()

# Importar modelos após configurar o ambiente
from django.contrib.auth.models import User
from apps.usuarios.models import Usuario as V1Usuario
from django.db import transaction

# Mapeamento de perfis para permissões
ROLE_PERMISSIONS = {
    'Solicitante': ['can_create_solicitation'],
    'Estoque': ['can_manage_stock'],
    'Suprimentos': ['can_manage_procurement'],
    'Gerência&Diretoria': ['can_approve'],
    'Admin': ['is_admin', 'can_create_solicitation', 'can_manage_stock', 'can_manage_procurement', 'can_approve'],
}

def fix_user_permissions():
    """
    Corrige as permissões dos usuários Django com base nos perfis do modelo V1
    """
    try:
        with transaction.atomic():
            # Obter todos os usuários do modelo V1
            v1_users = V1Usuario.objects.all()
            print(f"Encontrados {v1_users.count()} usuários no modelo V1")
            
            updated_users = 0
            
            for v1_user in v1_users:
                # Obter ou criar usuário Django correspondente
                try:
                    django_user = User.objects.get(username=v1_user.username)
                except User.DoesNotExist:
                    print(f"Usuário Django não encontrado para {v1_user.username}, criando...")
                    django_user = User.objects.create_user(
                        username=v1_user.username,
                        first_name=v1_user.nome,
                        is_active=True,
                        is_staff=v1_user.perfil == 'Admin',
                        is_superuser=v1_user.perfil == 'Admin',
                    )
                
                # Obter permissões para o perfil
                perfil = v1_user.perfil
                permissions_to_add = ROLE_PERMISSIONS.get(perfil, [])
                
                if not permissions_to_add:
                    print(f"Perfil '{perfil}' não tem permissões mapeadas para {v1_user.username}")
                    continue
                
                # Inicializar permissions se não existir
                if not hasattr(django_user, 'permissions') or django_user.permissions is None:
                    django_user.permissions = {}
                
                # Adicionar permissões com base no perfil
                updated = False
                for permission in permissions_to_add:
                    if permission not in django_user.permissions or not django_user.permissions.get(permission):
                        django_user.permissions[permission] = True
                        updated = True
                
                if updated:
                    django_user.save()
                    updated_users += 1
                    print(f"Atualizadas permissões para '{v1_user.username}' (Perfil: {perfil})")
                    print(f"  Permissões: {django_user.permissions}")
            
            print(f"\nTotal de usuários atualizados: {updated_users}")
            return updated_users
    except Exception as e:
        print(f"Erro ao corrigir permissões: {e}")
        return 0

if __name__ == "__main__":
    print("Corrigindo permissões dos usuários...")
    fix_user_permissions()
    print("\nProcesso concluído. Reinicie o servidor Django para aplicar as alterações.")
