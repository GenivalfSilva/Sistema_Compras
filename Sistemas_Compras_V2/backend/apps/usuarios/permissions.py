"""
Permissões customizadas para o Sistema de Compras V2
"""
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permissão que permite apenas admins criarem/editarem/deletarem
    Outros usuários podem apenas ler
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        return request.user.is_authenticated and getattr(request.user, 'is_admin', lambda: False)()


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão que permite ao dono do objeto ou admin acessar
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin tem acesso total
        if getattr(request.user, 'is_admin', lambda: False)():
            return True
        
        # Usuário pode acessar apenas seus próprios dados
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Se o objeto é um usuário, verifica se é o próprio usuário
        if hasattr(obj, 'username'):
            return obj == request.user
        
        return False


class IsSolicitanteOrAdmin(permissions.BasePermission):
    """
    Permissão para solicitantes e admins
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            getattr(request.user, 'can_create_solicitation', lambda: False)() or 
            getattr(request.user, 'is_admin', lambda: False)()
        )


class IsEstoqueOrAdmin(permissions.BasePermission):
    """
    Permissão para estoque e admins
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            getattr(request.user, 'can_manage_stock', lambda: False)() or 
            getattr(request.user, 'is_admin', lambda: False)()
        )


class IsSuprimentosOrAdmin(permissions.BasePermission):
    """
    Permissão para suprimentos e admins
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            getattr(request.user, 'can_manage_procurement', lambda: False)() or 
            getattr(request.user, 'is_admin', lambda: False)()
        )


class IsDiretoriaOrAdmin(permissions.BasePermission):
    """
    Permissão para diretoria e admins
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        return (
            getattr(request.user, 'can_approve', lambda: False)() or 
            getattr(request.user, 'is_admin', lambda: False)()
        )


class CanManageSolicitacao(permissions.BasePermission):
    """
    Permissão baseada no status da solicitação e perfil do usuário
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin tem acesso total
        if getattr(user, 'is_admin', lambda: False)():
            return True
        
        # Solicitante pode ver suas próprias solicitações
        user_username = getattr(user, 'username', None)
        solicitante_username = getattr(obj, 'solicitante_username', None)
        if solicitante_username and user_username and solicitante_username == user_username:
            if request.method in permissions.SAFE_METHODS:
                return True
            return getattr(obj, 'status', None) == 'Solicitação'
        else:
            # Fallback: usar mapeamento do usuário V1 para comparar com o campo de exibição 'solicitante'
            try:
                from apps.usuarios.models import Usuario as V1Usuario
                v1 = V1Usuario.objects.get(username=user_username)
                v1_nome = getattr(v1, 'nome', None)
            except Exception:
                v1_nome = None
            if v1_nome and getattr(obj, 'solicitante', None) == v1_nome:
                if request.method in permissions.SAFE_METHODS:
                    return True
                return getattr(obj, 'status', None) == 'Solicitação'
        
        # Estoque pode gerenciar solicitações em status específicos
        if getattr(user, 'can_manage_stock', lambda: False)():
            return getattr(obj, 'status', None) in ['Solicitação', 'Requisição']
        
        # Suprimentos pode gerenciar em vários status
        if getattr(user, 'can_manage_procurement', lambda: False)():
            return getattr(obj, 'status', None) in [
                'Suprimentos', 'Em Cotação', 'Pedido de Compras',
                'Compra feita', 'Aguardando Entrega'
            ]
        
        # Diretoria pode aprovar/reprovar
        if getattr(user, 'can_approve', lambda: False)():
            return getattr(obj, 'status', None) == 'Aguardando Aprovação'
        
        return False


class CanViewAuditoria(permissions.BasePermission):
    """
    Permissão para visualizar auditoria (apenas admin)
    """
    
    def has_permission(self, request, view):
        return (
            getattr(request.user, 'is_authenticated', False) and 
            getattr(request.user, 'is_admin', lambda: False)()
        )


class CanManageConfiguracoes(permissions.BasePermission):
    """
    Permissão para gerenciar configurações (apenas admin)
    """
    
    def has_permission(self, request, view):
        return (
            getattr(request.user, 'is_authenticated', False) and 
            getattr(request.user, 'is_admin', lambda: False)()
        )
