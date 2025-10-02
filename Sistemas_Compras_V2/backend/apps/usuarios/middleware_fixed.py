"""
Middleware para adaptar request.user com métodos de perfil do V1
- Adiciona métodos utilitários esperados pelas views/permissions:
  is_admin(), can_create_solicitation(), can_manage_stock(), can_manage_procurement(), can_approve(), get_profile_permissions()
- Funciona também para AnonymousUser (retorna permissões falsas)
"""
from typing import Dict
from django.utils.deprecation import MiddlewareMixin

try:
    from django.contrib.auth.models import AnonymousUser
except Exception:  # pragma: no cover
    AnonymousUser = object  # type: ignore

from .models import Usuario as V1Usuario


def _get_v1_usuario(username: str):
    if not username:
        return None
    try:
        return V1Usuario.objects.get(username=username)
    except V1Usuario.DoesNotExist:
        return None


def _permissions_from_perfil(perfil: str) -> Dict[str, bool]:
    perfil = perfil or ""
    return {
        "is_admin": perfil == "Admin",
        "can_create_solicitation": perfil in ("Solicitante", "Admin"),
        "can_create_solicitacao": perfil in ("Solicitante", "Admin"),  # Alias for compatibility
        "can_manage_stock": perfil in ("Estoque", "Admin"),
        "can_manage_procurement": perfil in ("Suprimentos", "Admin"),
        "can_approve": perfil in ("Gerência&Diretoria", "Diretoria", "Admin"),
    }


class UserProfileMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = getattr(request, "user", None)

        def is_admin():
            if not user or isinstance(user, AnonymousUser):
                return False
            # Direct check of V1 user's perfil
            v1 = _get_v1_usuario(getattr(user, "username", ""))
            if v1 and v1.perfil == "Admin":
                print(f"User {getattr(user, 'username', '')} has Admin permissions")
                return True
            return False

        def can_create_solicitation():
            if not user or isinstance(user, AnonymousUser):
                return False
            # Direct check of V1 user's perfil
            v1 = _get_v1_usuario(getattr(user, "username", ""))
            if v1 and v1.perfil in ["Solicitante", "Admin"]:
                print(f"User {getattr(user, 'username', '')} has Solicitante permissions")
                return True
            return False

        def can_manage_stock():
            if not user or isinstance(user, AnonymousUser):
                return False
            v1 = _get_v1_usuario(getattr(user, "username", ""))
            perms = _permissions_from_perfil(getattr(v1, "perfil", ""))
            return perms["can_manage_stock"]

        def can_manage_procurement():
            if not user or isinstance(user, AnonymousUser):
                return False
            v1 = _get_v1_usuario(getattr(user, "username", ""))
            perms = _permissions_from_perfil(getattr(v1, "perfil", ""))
            return perms["can_manage_procurement"]

        def can_approve():
            if not user or isinstance(user, AnonymousUser):
                return False
            v1 = _get_v1_usuario(getattr(user, "username", ""))
            perms = _permissions_from_perfil(getattr(v1, "perfil", ""))
            return perms["can_approve"]

        def get_profile_permissions():
            if not user or isinstance(user, AnonymousUser):
                return {
                    "is_admin": False,
                    "can_create_solicitation": False,
                    "can_create_solicitacao": False,  # Alias for compatibility
                    "can_manage_stock": False,
                    "can_manage_procurement": False,
                    "can_approve": False,
                }
            v1 = _get_v1_usuario(getattr(user, "username", ""))
            return _permissions_from_perfil(getattr(v1, "perfil", ""))

        # Anexa métodos ao user dinamicamente (somente se ainda não existem)
        if user is not None:
            for name, func in (
                ("is_admin", is_admin),
                ("can_create_solicitation", can_create_solicitation),
                ("can_create_solicitacao", can_create_solicitation),  # Alias for compatibility
                ("can_manage_stock", can_manage_stock),
                ("can_manage_procurement", can_manage_procurement),
                ("can_approve", can_approve),
                ("get_profile_permissions", get_profile_permissions),
            ):
                if not hasattr(user, name):
                    setattr(user, name, func)

        return None
