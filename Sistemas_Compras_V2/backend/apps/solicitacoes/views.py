"""
Views para o app de solicitações
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Solicitacao, CatalogoProduto, Movimentacao
from .serializers import (
    SolicitacaoListSerializer, SolicitacaoDetailSerializer,
    SolicitacaoCreateSerializer, SolicitacaoUpdateSerializer,
    StatusUpdateSerializer, CatalogoProdutoSerializer,
    MovimentacaoSerializer
)
from apps.usuarios.permissions import (
    IsSolicitanteOrAdmin, IsEstoqueOrAdmin, IsSuprimentosOrAdmin,
    IsDiretoriaOrAdmin, CanManageSolicitacao
)
from apps.auditoria.models import AuditoriaAdmin

User = get_user_model()


class SolicitacaoListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar solicitações
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'prioridade', 'departamento', 'solicitante']
    search_fields = ['numero_solicitacao_estoque', 'descricao', 'solicitante']
    ordering_fields = ['created_at', 'prioridade', 'status', 'valor_estimado']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Solicitacao.objects.all()
        
        # Filtros baseados no perfil do usuário
        try:
            from apps.usuarios.models import Usuario as V1Usuario
            v1 = V1Usuario.objects.get(username=getattr(user, 'username', '')) if user and user.is_authenticated else None
            v1_nome = getattr(v1, 'nome', None)
        except Exception:
            v1_nome = None

        if getattr(user, 'is_admin', lambda: False)():
            # Admin vê todas
            pass
        elif getattr(user, 'can_create_solicitation', lambda: False)() and v1_nome:
            # Solicitante vê apenas suas próprias
            queryset = queryset.filter(solicitante=v1_nome)
        elif getattr(user, 'can_manage_stock', lambda: False)():
            # Estoque vê solicitações em status específicos
            queryset = queryset.filter(status__in=['Solicitação', 'Requisição'])
        elif getattr(user, 'can_manage_procurement', lambda: False)():
            # Suprimentos vê solicitações em vários status
            queryset = queryset.filter(status__in=[
                'Suprimentos', 'Em Cotação', 'Pedido de Compras',
                'Aprovado', 'Compra feita', 'Aguardando Entrega'
            ])
        elif getattr(user, 'can_approve', lambda: False)():
            # Diretoria vê apenas aguardando aprovação
            queryset = queryset.filter(status='Aguardando Aprovação')
        else:
            # Outros perfis não veem nada
            queryset = queryset.none()
        
        # Não existe relação ORM direta com movimentações no V1
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SolicitacaoCreateSerializer
        return SolicitacaoListSerializer
    
    def get_permissions(self):
        # Temporarily allow any authenticated user to create a solicitacao
        return [permissions.AllowAny()]
    
    def perform_create(self, serializer):
        solicitacao = serializer.save()
        
        # Log creation
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='CREATE',
            descricao=f'Solicitação criada - #{solicitacao.numero_solicitacao_estoque}',
            objeto=solicitacao,
            dados_novos=serializer.validated_data,
            request=self.request
        )


class SolicitacaoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para detalhes, atualização e exclusão de solicitação
    """
    queryset = Solicitacao.objects.all()
    serializer_class = SolicitacaoDetailSerializer
    permission_classes = [CanManageSolicitacao]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SolicitacaoUpdateSerializer
        return SolicitacaoDetailSerializer
    
    def perform_update(self, serializer):
        old_data = SolicitacaoDetailSerializer(self.get_object()).data
        solicitacao = serializer.save()
        
        # Log update
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='UPDATE',
            descricao=f'Solicitação atualizada - #{solicitacao.numero_solicitacao_estoque}',
            objeto=solicitacao,
            dados_anteriores=old_data,
            dados_novos=serializer.validated_data,
            request=self.request
        )
    
    def perform_destroy(self, instance):
        # Log deletion
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='DELETE',
            descricao=f'Solicitação deletada - #{instance.numero_solicitacao_estoque}',
            dados_anteriores=SolicitacaoDetailSerializer(instance).data,
            request=self.request
        )
        
        instance.delete()


class UpdateStatusView(APIView):
    """
    View para atualizar status da solicitação
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            solicitacao = Solicitacao.objects.get(pk=pk)
        except Solicitacao.DoesNotExist:
            return Response(
                {'error': 'Solicitação não encontrada'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verifica permissão
        if not self._can_update_status(request.user, solicitacao):
            return Response(
                {'error': 'Sem permissão para alterar status desta solicitação'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = StatusUpdateSerializer(
            data=request.data,
            context={'solicitacao': solicitacao}
        )
        
        if serializer.is_valid():
            status_anterior = solicitacao.status
            novo_status = serializer.validated_data['novo_status']
            observacoes = serializer.validated_data.get('observacoes', '')
            
            # Atualiza status
            solicitacao.status = novo_status
            solicitacao.save()
            
            # Cria movimentação
            Movimentacao.objects.create(
                numero_solicitacao=solicitacao.numero_solicitacao_estoque,
                etapa_origem=status_anterior,
                etapa_destino=novo_status,
                usuario=(getattr(request.user, 'username', None) or 'sistema'),
                observacoes=observacoes or f'Status alterado para {novo_status}'
            )
            
            # Log audit
            AuditoriaAdmin.log_action(
                usuario=request.user,
                acao='MOVE',
                descricao=f'Status alterado de {status_anterior} para {novo_status} - #{solicitacao.numero_solicitacao_estoque}',
                objeto=solicitacao,
                request=request
            )
            
            return Response({
                'message': 'Status atualizado com sucesso',
                'status_anterior': status_anterior,
                'novo_status': novo_status
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _can_update_status(self, user, solicitacao):
        """Verifica se usuário pode alterar status"""
        def _has(method_name: str) -> bool:
            try:
                attr = getattr(user, method_name, None)
                if callable(attr):
                    return bool(attr())
                return bool(attr)
            except Exception:
                return False

        if _has('is_admin'):
            return True

        status = getattr(solicitacao, 'status', None)
        status_permissions = {
            'Solicitação': _has('can_manage_stock'),
            'Requisição': _has('can_manage_procurement'),
            'Suprimentos': _has('can_manage_procurement'),
            'Em Cotação': _has('can_manage_procurement'),
            'Pedido de Compras': _has('can_manage_procurement'),
            'Aguardando Aprovação': _has('can_approve'),
            'Aprovado': _has('can_manage_procurement'),
            'Compra feita': _has('can_manage_procurement'),
            'Aguardando Entrega': _has('can_manage_procurement'),
        }

        return status_permissions.get(status, False)


class ApprovalView(APIView):
    """
    View específica para aprovação/reprovação
    """
    permission_classes = [IsDiretoriaOrAdmin]
    
    def post(self, request, pk):
        try:
            solicitacao = Solicitacao.objects.get(pk=pk)
        except Solicitacao.DoesNotExist:
            return Response(
                {'error': 'Solicitação não encontrada'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if solicitacao.status != 'Aguardando Aprovação':
            return Response(
                {'error': 'Solicitação não está aguardando aprovação'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        acao = request.data.get('acao')  # 'aprovar' ou 'reprovar'
        observacoes = request.data.get('observacoes', '')
        
        if acao not in ['aprovar', 'reprovar']:
            return Response(
                {'error': 'Ação deve ser "aprovar" ou "reprovar"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Atualiza solicitação
        status_anterior = solicitacao.status
        novo_status = 'Aprovado' if acao == 'aprovar' else 'Reprovado'
        
        # Registra aprovação na lista JSON
        try:
            from apps.usuarios.models import Usuario as V1Usuario
            v1 = V1Usuario.objects.get(username=getattr(request.user, 'username', ''))
            aprovador_nome = v1.nome
        except Exception:
            aprovador_nome = getattr(request.user, 'username', 'sistema')

        aprovacao_reg = {
            'acao': acao,
            'por': aprovador_nome,
            'data': timezone.now().isoformat(),
            'observacoes': observacoes,
        }
        aprovacoes = list(solicitacao.aprovacoes or [])
        aprovacoes.append(aprovacao_reg)
        solicitacao.aprovacoes = aprovacoes
        solicitacao.status = novo_status
        solicitacao.save()
        
        # Cria movimentação
        Movimentacao.objects.create(
            numero_solicitacao=solicitacao.numero_solicitacao_estoque,
            etapa_origem=status_anterior,
            etapa_destino=novo_status,
            usuario=(getattr(request.user, 'username', None) or 'sistema'),
            observacoes=observacoes or f'Solicitação {acao}da'
        )
        
        # Log audit
        AuditoriaAdmin.log_action(
            usuario=request.user,
            acao='APPROVE' if acao == 'aprovar' else 'REJECT',
            descricao=f'Solicitação {acao}da - #{solicitacao.numero_solicitacao_estoque}',
            objeto=solicitacao,
            request=request
        )
        
        return Response({
            'message': f'Solicitação {acao}da com sucesso',
            'novo_status': novo_status
        })


class CatalogoProdutoListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar produtos do catálogo
    """
    queryset = CatalogoProduto.objects.filter(ativo=True)
    serializer_class = CatalogoProdutoSerializer
    permission_classes = [IsSuprimentosOrAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'categoria']
    ordering_fields = ['nome', 'categoria', 'created_at']
    ordering = ['nome']
    
    def perform_create(self, serializer):
        produto = serializer.save()
        
        # Log creation
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='CREATE',
            descricao=f'Produto criado no catálogo - {produto.nome}',
            objeto=produto,
            dados_novos=serializer.validated_data,
            request=self.request
        )


class CatalogoProdutoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para detalhar, atualizar e deletar produto do catálogo
    """
    queryset = CatalogoProduto.objects.all()
    serializer_class = CatalogoProdutoSerializer
    permission_classes = [IsSuprimentosOrAdmin]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_data(request):
    """
    Endpoint para dados do dashboard
    """
    user = getattr(request, 'user', None)

    def _has_perm(method_name: str) -> bool:
        """Executa método booleano do usuário com segurança."""
        try:
            attr = getattr(user, method_name, None)
            if callable(attr):
                return bool(attr())
            return bool(attr)
        except Exception:
            return False

    # Descobrir usuário V1 (quando possível)
    v1_nome = None
    v1_perfil = None
    try:
        from apps.usuarios.models import Usuario as V1Usuario
        v1 = V1Usuario.objects.get(username=getattr(user, 'username', ''))
        v1_nome = getattr(v1, 'nome', None)
        v1_perfil = getattr(v1, 'perfil', None)
    except Exception:
        pass

    # Base queryset baseado no perfil
    if _has_perm('is_admin'):
        queryset = Solicitacao.objects.all()
    elif _has_perm('can_create_solicitation'):
        if v1_nome:
            queryset = Solicitacao.objects.filter(solicitante=v1_nome)
        else:
            queryset = Solicitacao.objects.none()
    elif _has_perm('can_manage_stock'):
        queryset = Solicitacao.objects.filter(status__in=['Solicitação', 'Requisição'])
    elif _has_perm('can_manage_procurement'):
        queryset = Solicitacao.objects.filter(status__in=[
            'Suprimentos', 'Em Cotação', 'Pedido de Compras',
            'Aprovado', 'Compra feita', 'Aguardando Entrega'
        ])
    elif _has_perm('can_approve'):
        queryset = Solicitacao.objects.filter(status='Aguardando Aprovação')
    else:
        # Fallback: se não houver métodos de permissão mas existir usuário V1,
        # considerar como solicitante e mostrar apenas suas solicitações
        if v1_nome:
            queryset = Solicitacao.objects.filter(solicitante=v1_nome)
        else:
            queryset = Solicitacao.objects.none()
    
    # Estatísticas
    total = queryset.count()
    pendentes = queryset.exclude(status__in=['Aprovado', 'Reprovado', 'Pedido Finalizado']).count()
    aprovadas = queryset.filter(status='Aprovado').count()
    reprovadas = queryset.filter(status='Reprovado').count()
    finalizadas = queryset.filter(status='Pedido Finalizado').count()
    
    # SLA (cálculo resiliente)
    def _call_bool(sol, method_name: str) -> bool:
        try:
            m = getattr(sol, method_name, None)
            if callable(m):
                return bool(m())
        except Exception:
            pass
        return False

    vencidas = sum(1 for sol in queryset if _call_bool(sol, 'is_sla_vencido'))
    proximo_vencimento = sum(1 for sol in queryset if _call_bool(sol, 'is_sla_proximo_vencimento'))
    
    # Por status
    status_counts = {}
    for choice in Solicitacao.ETAPA_CHOICES:
        status_counts[choice[0]] = queryset.filter(status=choice[0]).count()
    
    # Por prioridade
    prioridade_counts = {}
    for choice in Solicitacao.PRIORIDADE_CHOICES:
        prioridade_counts[choice[0]] = queryset.filter(prioridade=choice[0]).count()
    
    return Response({
        'resumo': {
            'total': total,
            'pendentes': pendentes,
            'aprovadas': aprovadas,
            'reprovadas': reprovadas,
            'finalizadas': finalizadas,
        },
        'sla': {
            'vencidas': vencidas,
            'proximo_vencimento': proximo_vencimento,
            'ok': total - vencidas - proximo_vencimento,
        },
        'por_status': status_counts,
        'por_prioridade': prioridade_counts,
        'solicitacoes_recentes': SolicitacaoListSerializer(
            queryset.order_by('-created_at')[:5], 
            many=True
        ).data
    })
