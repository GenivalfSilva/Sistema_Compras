"""
Views para autenticação e gerenciamento de usuários
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from .authentication import LoginSerializer, TokenSerializer, get_tokens_for_user
from .serializers import UsuarioSerializer, UsuarioCreateSerializer, UsuarioV1Serializer
from apps.auditoria.models import AuditoriaAdmin, HistoricoLogin
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin

User = get_user_model()


class LoginView(APIView):
    """
    View para login com JWT
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user, request)
            
            response_serializer = TokenSerializer(tokens)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    View para logout (blacklist do refresh token)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log logout
            AuditoriaAdmin.log_action(
                usuario=request.user,
                acao='LOGOUT',
                descricao=f'Logout realizado - {request.user.username}',
                request=request
            )
            
            return Response({'message': 'Logout realizado com sucesso'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': 'Token inválido'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    View para obter perfil do usuário logado
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            # Log update
            AuditoriaAdmin.log_action(
                usuario=request.user,
                acao='UPDATE',
                descricao=f'Perfil atualizado - {request.user.username}',
                objeto=request.user,
                dados_novos=serializer.validated_data,
                request=request
            )
            
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar usuários (apenas admin)
    """
    queryset = User.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UsuarioCreateSerializer
        return UsuarioSerializer
    
    def perform_create(self, serializer):
        user = serializer.save()
        
        # Log creation
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='CREATE',
            descricao=f'Usuário criado - {user.username}',
            objeto=user,
            dados_novos=serializer.validated_data,
            request=self.request
        )


class UsuarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para detalhar, atualizar e deletar usuário específico
    """
    queryset = User.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsOwnerOrAdmin]
    
    def perform_update(self, serializer):
        old_data = UsuarioSerializer(self.get_object()).data
        user = serializer.save()
        
        # Log update
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='UPDATE',
            descricao=f'Usuário atualizado - {user.username}',
            objeto=user,
            dados_anteriores=old_data,
            dados_novos=serializer.validated_data,
            request=self.request
        )
    
    def perform_destroy(self, instance):
        # Log deletion
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='DELETE',
            descricao=f'Usuário deletado - {instance.username}',
            dados_anteriores=UsuarioSerializer(instance).data,
            request=self.request
        )
        
        instance.delete()


class UsuarioV1ListView(generics.ListAPIView):
    """
    Lista somente-leitura dos usuários do V1 (`apps.usuarios.models.Usuario`).
    Útil para o frontend operar com perfis reais enquanto o CRUD do Django User não for necessário.
    """
    from .models import Usuario as V1Usuario
    queryset = V1Usuario.objects.all().order_by('nome')
    serializer_class = UsuarioV1Serializer
    permission_classes = [IsAdminOrReadOnly]


class ChangePasswordView(APIView):
    """
    View para alterar senha do usuário
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': 'Senha atual e nova senha são obrigatórias'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.check_password(old_password):
            return Response(
                {'error': 'Senha atual incorreta'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        # Log password change
        AuditoriaAdmin.log_action(
            usuario=user,
            acao='UPDATE',
            descricao=f'Senha alterada - {user.username}',
            request=request
        )
        
        return Response({'message': 'Senha alterada com sucesso'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_permissions(request):
    """
    Endpoint para verificar permissões do usuário
    """
    user = request.user
    # Obtém perfil do V1
    try:
        from apps.usuarios.models import Usuario as V1Usuario
        v1 = V1Usuario.objects.get(username=getattr(user, 'username', ''))
        perfil = v1.perfil
    except Exception:
        perfil = ''

    # Permissions dict via middleware (ou fallback)
    perms = None
    if hasattr(user, 'get_profile_permissions'):
        try:
            perms = user.get_profile_permissions()
        except Exception:
            perms = None
    if not perms:
        perms = {
            'is_admin': perfil == 'Admin',
            'can_create_solicitation': perfil in ('Solicitante', 'Admin'),
            'can_manage_stock': perfil in ('Estoque', 'Admin'),
            'can_manage_procurement': perfil in ('Suprimentos', 'Admin'),
            'can_approve': perfil in ('Gerência&Diretoria', 'Diretoria', 'Admin'),
        }

    permissions_data = {
        'user_id': user.id,
        'username': user.username,
        'perfil': perfil,
        'is_admin': bool(perms.get('is_admin')),
        'permissions': perms,
        'can_create_solicitation': bool(perms.get('can_create_solicitation')),
        'can_manage_stock': bool(perms.get('can_manage_stock')),
        'can_manage_procurement': bool(perms.get('can_manage_procurement')),
        'can_approve': bool(perms.get('can_approve')),
        'can_admin': bool(perms.get('is_admin')),
    }
    
    return Response(permissions_data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test_endpoint(request):
    """
    Test endpoint to verify API is working
    """
    from apps.usuarios.models import Usuario
    from apps.solicitacoes.models import CatalogoProduto, Solicitacao
    from apps.configuracoes.models import Configuracao
    
    data = {
        'message': 'API is working!',
        'usuarios_count': Usuario.objects.count(),
        'solicitacoes_count': Solicitacao.objects.count(),
        'produtos_count': CatalogoProduto.objects.count(),
        'configuracoes_count': Configuracao.objects.count(),
    }
    return Response(data)
