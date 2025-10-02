from django.core.management.base import BaseCommand
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

class Command(BaseCommand):
    help = 'Sincroniza permissões dos usuários com base em seus perfis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Sincronizar apenas um usuário específico',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        try:
            with transaction.atomic():
                if username:
                    # Sincronizar apenas um usuário específico
                    try:
                        user = User.objects.get(username=username)
                        self.sync_user_permissions(user)
                    except User.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Usuário '{username}' não encontrado"))
                else:
                    # Sincronizar todos os usuários
                    users = User.objects.all()
                    updated_users = 0
                    
                    for user in users:
                        if self.sync_user_permissions(user):
                            updated_users += 1
                    
                    self.stdout.write(self.style.SUCCESS(f"Total de usuários atualizados: {updated_users}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao sincronizar permissões: {e}"))

    def sync_user_permissions(self, user):
        """Sincroniza permissões para um usuário específico."""
        perfil = getattr(user, 'perfil', None)
        if not perfil:
            self.stdout.write(self.style.WARNING(f"Usuário '{user.username}' não tem perfil definido"))
            return False
        
        permissions_to_add = ROLE_PERMISSIONS.get(perfil, [])
        if not permissions_to_add:
            self.stdout.write(self.style.WARNING(f"Perfil '{perfil}' não tem permissões mapeadas"))
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
            self.stdout.write(self.style.SUCCESS(f"Atualizadas permissões para '{user.username}' (Perfil: {perfil})"))
            self.stdout.write(f"  Permissões: {user.permissions}")
            return True
        
        return False
