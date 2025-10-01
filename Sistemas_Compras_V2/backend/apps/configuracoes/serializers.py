"""
Serializers para o app de configurações
"""
from rest_framework import serializers
from .models import Configuracao, ConfiguracaoSLA, LimiteAprovacao


class ConfiguracaoSerializer(serializers.ModelSerializer):
    """
    Serializer para configurações gerais do sistema
    """
    valor_typed = serializers.SerializerMethodField()
    
    class Meta:
        model = Configuracao
        fields = '__all__'
        read_only_fields = ['updated_at']
    
    def get_valor_typed(self, obj):
        """Retorna valor convertido para o tipo correto"""
        return obj.get_valor_typed()


class ConfiguracaoSLASerializer(serializers.ModelSerializer):
    """
    Serializer para configurações de SLA
    """
    class Meta:
        model = ConfiguracaoSLA
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, attrs):
        """Valida se os valores de SLA são lógicos"""
        sla_urgente = attrs.get('sla_urgente', 1)
        sla_alta = attrs.get('sla_alta', 2)
        sla_normal = attrs.get('sla_normal', 3)
        sla_baixa = attrs.get('sla_baixa', 5)
        
        if not (sla_urgente <= sla_alta <= sla_normal <= sla_baixa):
            raise serializers.ValidationError(
                "Os SLAs devem seguir a ordem: Urgente ≤ Alta ≤ Normal ≤ Baixa"
            )
        
        return attrs


class LimiteAprovacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para limites de aprovação
    """
    class Meta:
        model = LimiteAprovacao
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def validate(self, attrs):
        """Valida se valor mínimo é menor que máximo"""
        valor_minimo = attrs.get('valor_minimo', 0)
        valor_maximo = attrs.get('valor_maximo', 0)
        
        if valor_minimo >= valor_maximo:
            raise serializers.ValidationError(
                "Valor mínimo deve ser menor que valor máximo"
            )
        
        return attrs


class ConfiguracaoUpdateSerializer(serializers.Serializer):
    """
    Serializer para atualização em lote de configurações
    """
    configuracoes = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_configuracoes(self, value):
        """Valida formato das configurações"""
        for config in value:
            if 'chave' not in config or 'valor' not in config:
                raise serializers.ValidationError(
                    "Cada configuração deve ter 'chave' e 'valor'"
                )
        return value
