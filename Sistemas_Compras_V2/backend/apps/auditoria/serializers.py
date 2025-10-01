"""
Serializers para o app de auditoria
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AuditoriaAdmin, LogSistema, HistoricoLogin

User = get_user_model()


class AuditoriaAdminSerializer(serializers.ModelSerializer):
    """
    Serializer para auditoria administrativa
    """
    acao_display = serializers.CharField(source='get_acao_display', read_only=True)
    
    class Meta:
        model = AuditoriaAdmin
        fields = [
            'id', 'usuario', 'acao', 'acao_display',
            'modulo', 'detalhes', 'solicitacao_id', 'ip_address', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class LogSistemaSerializer(serializers.ModelSerializer):
    """
    Serializer para logs do sistema
    """
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = LogSistema
        fields = [
            'id', 'level', 'level_display', 'logger_name', 'message',
            'module', 'function', 'line_number', 'usuario', 'usuario_nome',
            'ip_address', 'request_path', 'extra_data', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class HistoricoLoginSerializer(serializers.ModelSerializer):
    """
    Serializer para histórico de login
    """
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = HistoricoLogin
        fields = [
            'id', 'usuario', 'usuario_nome', 'username_tentativa',
            'status', 'status_display', 'ip_address', 'user_agent',
            'motivo_falha', 'timestamp', 'sessao_id'
        ]
        read_only_fields = ['id', 'timestamp']


class AuditoriaFilterSerializer(serializers.Serializer):
    """
    Serializer para filtros de auditoria
    """
    data_inicio = serializers.DateTimeField(required=False)
    data_fim = serializers.DateTimeField(required=False)
    usuario = serializers.IntegerField(required=False)
    acao = serializers.ChoiceField(choices=AuditoriaAdmin.ACTION_CHOICES, required=False)
    ip_address = serializers.IPAddressField(required=False)
    
    def validate(self, attrs):
        """Valida se data início é anterior à data fim"""
        data_inicio = attrs.get('data_inicio')
        data_fim = attrs.get('data_fim')
        
        if data_inicio and data_fim and data_inicio > data_fim:
            raise serializers.ValidationError(
                "Data de início deve ser anterior à data de fim"
            )
        
        return attrs
