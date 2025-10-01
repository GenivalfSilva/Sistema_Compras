"""
Serializers para o app de usuários
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Usuario as V1Usuario

User = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para usuário (leitura e atualização)
    """
    full_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    nome = serializers.SerializerMethodField()
    perfil = serializers.SerializerMethodField()
    departamento = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'nome', 'perfil', 'departamento',
            'is_active', 'date_joined', 'last_login', 'full_name', 'permissions'
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'full_name', 'permissions']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_permissions(self, obj):
        # Tenta usar método anexado via middleware
        if hasattr(obj, 'get_profile_permissions'):
            try:
                return obj.get_profile_permissions()
            except Exception:
                pass
        # Computa a partir do perfil do V1
        perfil = self.get_perfil(obj)
        return {
            'is_admin': perfil == 'Admin',
            'can_create_solicitation': perfil in ('Solicitante', 'Admin'),
            'can_manage_stock': perfil in ('Estoque', 'Admin'),
            'can_manage_procurement': perfil in ('Suprimentos', 'Admin'),
            'can_approve': perfil in ('Gerência&Diretoria', 'Diretoria', 'Admin'),
        }

    def _get_v1_usuario(self, obj):
        try:
            from apps.usuarios.models import Usuario
            return Usuario.objects.get(username=getattr(obj, 'username', ''))
        except Exception:
            return None

    def get_nome(self, obj):
        v1 = self._get_v1_usuario(obj)
        if v1 and getattr(v1, 'nome', None):
            return v1.nome
        # fallback
        return obj.get_full_name() or obj.username

    def get_perfil(self, obj):
        v1 = self._get_v1_usuario(obj)
        return getattr(v1, 'perfil', None) or ''

    def get_departamento(self, obj):
        v1 = self._get_v1_usuario(obj)
        return getattr(v1, 'departamento', None) or ''


class UsuarioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de usuário
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'nome', 'perfil', 'departamento',
            'password', 'password_confirm', 'is_active'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("As senhas não coincidem.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UsuarioUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de usuário (sem senha)
    """
    class Meta:
        model = User
        fields = ['email', 'nome', 'perfil', 'departamento', 'is_active']
    
    def validate_perfil(self, value):
        """Valida se o perfil é válido"""
        valid_profiles = ['Solicitante', 'Estoque', 'Suprimentos', 'Diretoria', 'Admin']
        if value not in valid_profiles:
            raise serializers.ValidationError(f"Perfil deve ser um dos: {', '.join(valid_profiles)}")
        return value


class UsuarioV1Serializer(serializers.ModelSerializer):
    """
    Serializer simples para o modelo V1 `usuarios` (somente leitura)
    """
    class Meta:
        model = V1Usuario
        fields = ['id', 'username', 'nome', 'perfil', 'departamento', 'created_at']
        read_only_fields = fields


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer para alteração de senha
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("As novas senhas não coincidem.")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta.")
        return value
