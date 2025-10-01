"""
Custom authentication backend for V1 database compatibility
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from apps.usuarios.models import Usuario
import hashlib


class V1AuthenticationBackend(BaseBackend):
    """
    Custom authentication backend that works with V1 senha_hash
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            # Get V1 user
            v1_user = Usuario.objects.get(username=username)
            
            # Check password against V1 senha_hash
            if self.check_v1_password(password, v1_user.senha_hash):
                # Create or get Django User for session management
                django_user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': v1_user.nome,
                        'is_active': True,
                        'is_staff': v1_user.perfil == 'Admin',
                        'is_superuser': v1_user.perfil == 'Admin',
                    }
                )
                return django_user
                
        except Usuario.DoesNotExist:
            return None
        
        return None
    
    def check_v1_password(self, password, senha_hash):
        """
        Check password against V1 hash format
        Adjust this method based on V1's hashing algorithm
        """
        # V1: SHA256 com salt "sistema_compras_2024"
        salt = "sistema_compras_2024"
        test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return test_hash == (senha_hash or "")
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
