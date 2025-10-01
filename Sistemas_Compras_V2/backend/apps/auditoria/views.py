"""
Views para o app de auditoria
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from .models import AuditoriaAdmin, LogSistema, HistoricoLogin
from .serializers import (
    AuditoriaAdminSerializer, LogSistemaSerializer,
    HistoricoLoginSerializer, AuditoriaFilterSerializer
)
from apps.usuarios.permissions import CanViewAuditoria

User = get_user_model()


class AuditoriaAdminListView(generics.ListAPIView):
    """
    View para listar auditoria administrativa (apenas leitura)
    """
    queryset = AuditoriaAdmin.objects.all()
    serializer_class = AuditoriaAdminSerializer
    permission_classes = [CanViewAuditoria]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['acao', 'usuario']
    search_fields = ['detalhes', 'usuario', 'ip_address', 'modulo']
    ordering_fields = ['timestamp', 'acao', 'usuario']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros por data
        data_inicio = self.request.query_params.get('data_inicio')
        data_fim = self.request.query_params.get('data_fim')
        
        if data_inicio:
            queryset = queryset.filter(timestamp__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(timestamp__lte=data_fim)
        
        return queryset


class AuditoriaAdminDetailView(generics.RetrieveAPIView):
    """
    View para detalhar entrada específica de auditoria
    """
    queryset = AuditoriaAdmin.objects.all()
    serializer_class = AuditoriaAdminSerializer
    permission_classes = [CanViewAuditoria]


class LogSistemaListView(generics.ListAPIView):
    """
    View para listar logs do sistema
    """
    queryset = LogSistema.objects.all()
    serializer_class = LogSistemaSerializer
    permission_classes = [CanViewAuditoria]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'logger_name', 'usuario']
    search_fields = ['message', 'module', 'function']
    ordering_fields = ['timestamp', 'level']
    ordering = ['-timestamp']


class HistoricoLoginListView(generics.ListAPIView):
    """
    View para listar histórico de login
    """
    queryset = HistoricoLogin.objects.all()
    serializer_class = HistoricoLoginSerializer
    permission_classes = [CanViewAuditoria]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'usuario']
    search_fields = ['username_tentativa', 'ip_address']
    ordering_fields = ['timestamp', 'status']
    ordering = ['-timestamp']


@api_view(['GET'])
@permission_classes([CanViewAuditoria])
def audit_statistics(request):
    """
    Endpoint para estatísticas de auditoria
    """
    # Período padrão: últimos 30 dias
    data_inicio = timezone.now() - timedelta(days=30)
    
    # Filtros opcionais
    if request.query_params.get('data_inicio'):
        data_inicio = request.query_params.get('data_inicio')
    
    data_fim = timezone.now()
    if request.query_params.get('data_fim'):
        data_fim = request.query_params.get('data_fim')
    
    # Estatísticas de auditoria
    audit_queryset = AuditoriaAdmin.objects.filter(
        timestamp__gte=data_inicio,
        timestamp__lte=data_fim
    )
    
    # Por ação
    acoes_stats = {}
    for choice in AuditoriaAdmin.ACTION_CHOICES:
        acoes_stats[choice[0]] = audit_queryset.filter(acao=choice[0]).count()
    
    # Por usuário (top 10)
    usuarios_stats = list(
        audit_queryset.values('usuario').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
    )
    
    # Por IP (top 10)
    ips_stats = list(
        audit_queryset.exclude(ip_address__isnull=True).values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
    )
    
    # Estatísticas de login
    login_queryset = HistoricoLogin.objects.filter(
        timestamp__gte=data_inicio,
        timestamp__lte=data_fim
    )
    
    login_stats = {
        'total_tentativas': login_queryset.count(),
        'sucessos': login_queryset.filter(status='SUCCESS').count(),
        'falhas': login_queryset.filter(status='FAILED').count(),
        'bloqueios': login_queryset.filter(status='BLOCKED').count(),
    }
    
    # Logs do sistema por nível
    log_queryset = LogSistema.objects.filter(
        timestamp__gte=data_inicio,
        timestamp__lte=data_fim
    )
    
    logs_stats = {}
    for choice in LogSistema.LEVEL_CHOICES:
        logs_stats[choice[0]] = log_queryset.filter(level=choice[0]).count()
    
    return Response({
        'periodo': {
            'data_inicio': data_inicio,
            'data_fim': data_fim
        },
        'auditoria': {
            'total_eventos': audit_queryset.count(),
            'por_acao': acoes_stats,
            'top_usuarios': usuarios_stats,
            'top_ips': ips_stats
        },
        'login': login_stats,
        'logs_sistema': {
            'total_logs': log_queryset.count(),
            'por_nivel': logs_stats
        }
    })


@api_view(['GET'])
@permission_classes([CanViewAuditoria])
def user_activity(request, user_id):
    """
    Endpoint para atividade de usuário específico
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'Usuário não encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Período padrão: últimos 30 dias
    data_inicio = timezone.now() - timedelta(days=30)
    if request.query_params.get('data_inicio'):
        data_inicio = request.query_params.get('data_inicio')
    
    # Auditoria do usuário
    audit_events = AuditoriaAdmin.objects.filter(
        usuario=user,
        timestamp__gte=data_inicio
    ).order_by('-timestamp')[:50]
    
    # Histórico de login
    login_history = HistoricoLogin.objects.filter(
        usuario=user,
        timestamp__gte=data_inicio
    ).order_by('-timestamp')[:20]
    
    # Estatísticas
    stats = {
        'total_acoes': audit_events.count(),
        'ultimo_login': login_history.filter(status='SUCCESS').first(),
        'tentativas_falha': login_history.filter(status='FAILED').count(),
        'ips_utilizados': list(
            login_history.values_list('ip_address', flat=True).distinct()
        )
    }
    
    return Response({
        'usuario': {
            'id': user.id,
            'username': user.username,
            'nome': (lambda: __import__('apps.usuarios.models', fromlist=['Usuario']).Usuario.objects.get(username=user.username).nome if __import__('apps.usuarios.models', fromlist=['Usuario']).Usuario.objects.filter(username=user.username).exists() else user.get_full_name())(),
            'perfil': (lambda: __import__('apps.usuarios.models', fromlist=['Usuario']).Usuario.objects.get(username=user.username).perfil if __import__('apps.usuarios.models', fromlist=['Usuario']).Usuario.objects.filter(username=user.username).exists() else '')(),
        },
        'estatisticas': stats,
        'eventos_auditoria': AuditoriaAdminSerializer(audit_events, many=True).data,
        'historico_login': HistoricoLoginSerializer(login_history, many=True).data
    })


@api_view(['POST'])
@permission_classes([CanViewAuditoria])
def export_audit_report(request):
    """
    Endpoint para exportar relatório de auditoria
    """
    serializer = AuditoriaFilterSerializer(data=request.data)
    
    if serializer.is_valid():
        filters = serializer.validated_data
        
        # Aplica filtros
        queryset = AuditoriaAdmin.objects.all()
        
        if filters.get('data_inicio'):
            queryset = queryset.filter(timestamp__gte=filters['data_inicio'])
        if filters.get('data_fim'):
            queryset = queryset.filter(timestamp__lte=filters['data_fim'])
        if filters.get('usuario'):
            queryset = queryset.filter(usuario_id=filters['usuario'])
        if filters.get('acao'):
            queryset = queryset.filter(acao=filters['acao'])
        if filters.get('ip_address'):
            queryset = queryset.filter(ip_address=filters['ip_address'])
        
        # Limita a 10000 registros para performance
        queryset = queryset.order_by('-timestamp')[:10000]
        
        # Serializa dados
        data = AuditoriaAdminSerializer(queryset, many=True).data
        
        return Response({
            'total_registros': len(data),
            'filtros_aplicados': filters,
            'dados': data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([CanViewAuditoria])
def security_alerts(request):
    """
    Endpoint para alertas de segurança
    """
    # Últimas 24 horas
    last_24h = timezone.now() - timedelta(hours=24)
    
    # Múltiplas tentativas de login falhadas
    failed_logins = HistoricoLogin.objects.filter(
        status='FAILED',
        timestamp__gte=last_24h
    ).values('ip_address').annotate(
        count=Count('id')
    ).filter(count__gte=5).order_by('-count')
    
    # Logins de IPs suspeitos (novos IPs)
    known_ips = set(
        HistoricoLogin.objects.filter(
            status='SUCCESS',
            timestamp__lt=last_24h
        ).values_list('ip_address', flat=True).distinct()
    )
    
    new_ip_logins = HistoricoLogin.objects.filter(
        status='SUCCESS',
        timestamp__gte=last_24h
    ).exclude(ip_address__in=known_ips)
    
    # Ações administrativas fora do horário comercial
    admin_actions_off_hours = AuditoriaAdmin.objects.filter(
        timestamp__gte=last_24h,
        acao__in=['DELETE', 'CONFIG'],
        timestamp__hour__lt=8  # Antes das 8h
    ).union(
        AuditoriaAdmin.objects.filter(
            timestamp__gte=last_24h,
            acao__in=['DELETE', 'CONFIG'],
            timestamp__hour__gt=18  # Depois das 18h
        )
    )
    
    return Response({
        'periodo_analise': '24 horas',
        'alertas': {
            'tentativas_login_falhadas': list(failed_logins),
            'logins_ips_novos': HistoricoLoginSerializer(new_ip_logins, many=True).data,
            'acoes_admin_fora_horario': AuditoriaAdminSerializer(admin_actions_off_hours, many=True).data
        },
        'total_alertas': len(failed_logins) + new_ip_logins.count() + admin_actions_off_hours.count()
    })
