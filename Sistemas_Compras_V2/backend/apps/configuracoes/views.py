"""
Views para o app de configurações
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .models import Configuracao, ConfiguracaoSLA, LimiteAprovacao
from .serializers import (
    ConfiguracaoSerializer, ConfiguracaoSLASerializer,
    LimiteAprovacaoSerializer, ConfiguracaoUpdateSerializer
)
from apps.usuarios.permissions import CanManageConfiguracoes
from apps.auditoria.models import AuditoriaAdmin

User = get_user_model()


class ConfiguracaoListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar configurações (apenas admin)
    """
    queryset = Configuracao.objects.all()
    serializer_class = ConfiguracaoSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    ordering = ['chave']
    
    def perform_create(self, serializer):
        config = serializer.save()
        
        # Log creation
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='CONFIG',
            descricao=f'Configuração criada - {config.chave}',
            objeto=config,
            dados_novos=serializer.validated_data,
            request=self.request
        )


class ConfiguracaoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para detalhar, atualizar e deletar configuração específica
    """
    queryset = Configuracao.objects.all()
    serializer_class = ConfiguracaoSerializer
    permission_classes = [CanManageConfiguracoes]
    
    def perform_update(self, serializer):
        old_data = ConfiguracaoSerializer(self.get_object()).data
        config = serializer.save()
        
        # Log update
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='CONFIG',
            descricao=f'Configuração atualizada - {config.chave}',
            objeto=config,
            dados_anteriores=old_data,
            dados_novos=serializer.validated_data,
            request=self.request
        )


class ConfiguracaoSLAListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar configurações de SLA
    """
    queryset = ConfiguracaoSLA.objects.all()
    serializer_class = ConfiguracaoSLASerializer
    permission_classes = [CanManageConfiguracoes]
    ordering = ['departamento']
    
    def perform_create(self, serializer):
        config = serializer.save()
        
        # Log creation
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='CONFIG',
            descricao=f'Configuração SLA criada - {config.departamento}',
            objeto=config,
            dados_novos=serializer.validated_data,
            request=self.request
        )


class ConfiguracaoSLADetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para detalhar, atualizar e deletar configuração de SLA
    """
    queryset = ConfiguracaoSLA.objects.all()
    serializer_class = ConfiguracaoSLASerializer
    permission_classes = [CanManageConfiguracoes]


class LimiteAprovacaoListCreateView(generics.ListCreateAPIView):
    """
    View para listar e criar limites de aprovação
    """
    queryset = LimiteAprovacao.objects.filter(ativo=True)
    serializer_class = LimiteAprovacaoSerializer
    permission_classes = [CanManageConfiguracoes]
    ordering = ['valor_minimo']
    
    def perform_create(self, serializer):
        limite = serializer.save()
        
        # Log creation
        AuditoriaAdmin.log_action(
            usuario=self.request.user,
            acao='CONFIG',
            descricao=f'Limite de aprovação criado - {limite.nome}',
            objeto=limite,
            dados_novos=serializer.validated_data,
            request=self.request
        )


class LimiteAprovacaoDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para detalhar, atualizar e deletar limite de aprovação
    """
    queryset = LimiteAprovacao.objects.all()
    serializer_class = LimiteAprovacaoSerializer
    permission_classes = [CanManageConfiguracoes]


class BulkUpdateConfigView(APIView):
    """
    View para atualização em lote de configurações
    """
    permission_classes = [CanManageConfiguracoes]
    
    def post(self, request):
        serializer = ConfiguracaoUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            configuracoes_data = serializer.validated_data['configuracoes']
            updated_configs = []
            
            for config_data in configuracoes_data:
                chave = config_data['chave']
                valor = config_data['valor']
                tipo = config_data.get('tipo', 'string')
                descricao = config_data.get('descricao', '')
                
                config = Configuracao.set_config(chave, valor, tipo, descricao)
                updated_configs.append(config)
                
                # Log each update
                AuditoriaAdmin.log_action(
                    usuario=request.user,
                    acao='CONFIG',
                    descricao=f'Configuração atualizada em lote - {chave}',
                    objeto=config,
                    request=request
                )
            
            return Response({
                'message': f'{len(updated_configs)} configurações atualizadas',
                'configuracoes': ConfiguracaoSerializer(updated_configs, many=True).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_config_value(request, chave):
    """
    Endpoint para buscar valor de configuração específica
    """
    valor = Configuracao.get_config(chave)
    
    if valor is None:
        return Response(
            {'error': 'Configuração não encontrada'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response({
        'chave': chave,
        'valor': valor
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_sla_for_department(request, departamento):
    """
    Endpoint para buscar SLA de um departamento
    """
    try:
        config_sla = ConfiguracaoSLA.objects.get(departamento=departamento, ativo=True)
        serializer = ConfiguracaoSLASerializer(config_sla)
        return Response(serializer.data)
    except ConfiguracaoSLA.DoesNotExist:
        # Retorna SLA padrão se não encontrar configuração específica
        return Response({
            'departamento': departamento,
            'sla_urgente': 1,
            'sla_alta': 2,
            'sla_normal': 3,
            'sla_baixa': 5,
            'ativo': True
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_approval_limit_for_value(request, valor):
    """
    Endpoint para buscar limite de aprovação para um valor
    """
    try:
        valor_decimal = float(valor)
        aprovador = LimiteAprovacao.get_aprovador_for_value(valor_decimal)
        
        return Response({
            'valor': valor_decimal,
            'aprovador_necessario': aprovador
        })
    except ValueError:
        return Response(
            {'error': 'Valor inválido'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
