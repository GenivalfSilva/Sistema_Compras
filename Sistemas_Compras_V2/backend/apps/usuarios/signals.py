from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

# Mapeamento de perfis para permissões
ROLE_PERMISSIONS = {
    'Solicitante': ['can_create_solicitation'],
    'Estoque': ['can_manage_stock'],
    'Suprimentos': ['can_manage_procurement'],
    'Diretoria': ['can_approve'],
    'Admin': ['is_admin', 'can_create_solicitation', 'can_manage_stock', 'can_manage_procurement', 'can_approve'],
}

@receiver(post_save, sender=User)
def sync_user_permissions(sender, instance, created, **kwargs):
    """
    Signal para sincronizar permissões automaticamente quando um usuário é criado ou atualizado.
    """
    # Verificar se o usuário tem um perfil
    perfil = getattr(instance, 'perfil', None)
    if not perfil:
        return
    
    # Obter permissões para o perfil
    permissions_to_add = ROLE_PERMISSIONS.get(perfil, [])
    if not permissions_to_add:
        return
    
    # Inicializar permissions se não existir
    if not instance.permissions:
        instance.permissions = {}
    
    # Adicionar permissões com base no perfil
    updated = False
    for permission in permissions_to_add:
        if permission not in instance.permissions or not instance.permissions.get(permission):
            instance.permissions[permission] = True
            updated = True
    
    # Salvar o usuário se as permissões foram atualizadas
    if updated:
        # Usar update para evitar loop infinito com o signal
        User.objects.filter(id=instance.id).update(permissions=instance.permissions)
