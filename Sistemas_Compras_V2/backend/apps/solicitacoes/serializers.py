"""
Serializers para o app de solicitações
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Solicitacao, CatalogoProduto, Movimentacao

User = get_user_model()


class CatalogoProdutoSerializer(serializers.ModelSerializer):
    """
    Serializer para catálogo de produtos
    """
    class Meta:
        model = CatalogoProduto
        fields = '__all__'
        read_only_fields = ['created_at']


class MovimentacaoSerializer(serializers.ModelSerializer):
    """
    Serializer para movimentações (histórico de status)
    """
    
    class Meta:
        model = Movimentacao
        fields = [
            'id', 'numero_solicitacao', 'etapa_origem', 'etapa_destino',
            'usuario', 'observacoes', 'data_movimentacao'
        ]
        read_only_fields = ['id', 'data_movimentacao']


class SolicitacaoListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de solicitações (campos resumidos)
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    departamento_display = serializers.CharField(source='get_departamento_display', read_only=True)
    sla_status = serializers.SerializerMethodField()
    dias_em_andamento = serializers.SerializerMethodField()
    
    class Meta:
        model = Solicitacao
        fields = [
            'id', 'numero_solicitacao_estoque', 'solicitante', 'departamento', 'departamento_display',
            'prioridade', 'prioridade_display', 'status', 'status_display', 'descricao',
            'valor_estimado', 'valor_final', 'created_at', 'sla_status', 'dias_em_andamento'
        ]
    
    def get_sla_status(self, obj):
        """Retorna status do SLA"""
        if obj.is_sla_vencido():
            return 'vencido'
        elif obj.is_sla_proximo_vencimento():
            return 'proximo_vencimento'
        return 'ok'
    
    def get_dias_em_andamento(self, obj):
        """Retorna dias em andamento"""
        return obj.get_dias_em_andamento()


class SolicitacaoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalhes da solicitação
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    prioridade_display = serializers.CharField(source='get_prioridade_display', read_only=True)
    departamento_display = serializers.CharField(source='get_departamento_display', read_only=True)
    sla_info = serializers.SerializerMethodField()
    pode_editar = serializers.SerializerMethodField()
    proxima_acao = serializers.SerializerMethodField()
    
    class Meta:
        model = Solicitacao
        fields = '__all__'
        read_only_fields = [
            'id', 'numero_solicitacao_estoque', 'created_at',
            'status_display', 'prioridade_display',
            'departamento_display', 'sla_info',
            'pode_editar', 'proxima_acao'
        ]
    
    def get_sla_info(self, obj):
        """Retorna informações detalhadas do SLA"""
        return {
            'dias_limite': obj.get_sla_days(),
            'dias_decorridos': obj.get_dias_em_andamento(),
            'vencido': obj.is_sla_vencido(),
            'proximo_vencimento': obj.is_sla_proximo_vencimento(),
            'percentual_usado': obj.get_sla_percentage_used()
        }
    
    def get_pode_editar(self, obj):
        """Verifica se usuário atual pode editar"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin pode editar sempre
        if user.is_admin():
            return True
        
        # Solicitante pode editar apenas se status for "Solicitação"
        try:
            from apps.usuarios.models import Usuario
            v1 = Usuario.objects.get(username=user.username)
            if obj.solicitante == v1.nome:
                return obj.status == 'Solicitação'
        except Exception:
            pass
        
        # Outros perfis baseado no status
        if user.can_manage_stock():
            return obj.status in ['Solicitação', 'Requisição']
        
        if user.can_manage_procurement():
            return obj.status in [
                'Suprimentos', 'Em Cotação', 'Pedido de Compras',
                'Compra feita', 'Aguardando Entrega'
            ]
        
        if user.can_approve():
            return obj.status == 'Aguardando Aprovação'
        
        return False
    
    def get_proxima_acao(self, obj):
        """Retorna próxima ação possível baseada no status"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        user = request.user
        status_actions = {
            'Solicitação': {
                'estoque': 'Criar Requisição',
                'admin': 'Gerenciar'
            },
            'Requisição': {
                'suprimentos': 'Processar Requisição',
                'admin': 'Gerenciar'
            },
            'Suprimentos': {
                'suprimentos': 'Iniciar Cotação',
                'admin': 'Gerenciar'
            },
            'Em Cotação': {
                'suprimentos': 'Criar Pedido de Compras',
                'admin': 'Gerenciar'
            },
            'Pedido de Compras': {
                'suprimentos': 'Enviar para Aprovação',
                'admin': 'Gerenciar'
            },
            'Aguardando Aprovação': {
                'diretoria': 'Aprovar/Reprovar',
                'admin': 'Gerenciar'
            },
            'Aprovado': {
                'suprimentos': 'Registrar Compra',
                'admin': 'Gerenciar'
            },
            'Compra feita': {
                'suprimentos': 'Aguardar Entrega',
                'admin': 'Gerenciar'
            },
            'Aguardando Entrega': {
                'suprimentos': 'Finalizar Pedido',
                'admin': 'Gerenciar'
            }
        }
        
        actions = status_actions.get(obj.status, {})
        
        if user.is_admin():
            return actions.get('admin')
        elif user.can_manage_stock():
            return actions.get('estoque')
        elif user.can_manage_procurement():
            return actions.get('suprimentos')
        elif user.can_approve():
            return actions.get('diretoria')
        
        return None


class SolicitacaoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de solicitações
    """
    class Meta:
        model = Solicitacao
        fields = [
            'departamento', 'prioridade', 'descricao',
            'local_aplicacao', 'observacoes', 'valor_estimado',
            'itens', 'anexos_requisicao'
        ]
    
    def create(self, validated_data):
        from apps.usuarios.models import Usuario
        request = self.context.get('request')
        user = request.user if request else None
        v1_nome = None
        if user and getattr(user, 'username', None):
            try:
                v1 = Usuario.objects.get(username=user.username)
                v1_nome = v1.nome
            except Usuario.DoesNotExist:
                v1_nome = user.get_full_name() or user.username
        else:
            v1_nome = 'Sistema'

        # Campos automáticos
        validated_data['solicitante'] = v1_nome
        validated_data['status'] = 'Solicitação'

        # Gera próximo número de solicitação
        from django.db.models import Max
        last_num = Solicitacao.objects.aggregate(Max('numero_solicitacao_estoque')).get('numero_solicitacao_estoque__max') or 0
        validated_data['numero_solicitacao_estoque'] = int(last_num) + 1

        solicitacao = Solicitacao.objects.create(**validated_data)

        # Cria movimentação inicial
        Movimentacao.objects.create(
            numero_solicitacao=solicitacao.numero_solicitacao_estoque,
            etapa_origem='',
            etapa_destino='Solicitação',
            usuario=getattr(user, 'username', 'sistema'),
            observacoes='Solicitação criada'
        )

        return solicitacao


class SolicitacaoUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de solicitações
    """
    class Meta:
        model = Solicitacao
        fields = [
            'departamento', 'prioridade', 'descricao',
            'local_aplicacao', 'observacoes', 'valor_estimado',
            'numero_requisicao', 'data_requisicao', 'responsavel_suprimentos',
            'numero_pedido_compras', 'fornecedor_recomendado', 'fornecedor_final',
            'data_entrega_prevista', 'data_entrega_real', 'nota_fiscal', 'valor_final',
            'observacoes_requisicao', 'observacoes_pedido_compras',
            'entrega_conforme', 'responsavel_recebimento', 'justificativa', 'tipo_solicitacao',
            'itens', 'cotacoes', 'aprovacoes', 'anexos_requisicao', 'historico_etapas'
        ]
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        
        # Atualiza instância
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class StatusUpdateSerializer(serializers.Serializer):
    """
    Serializer para atualização de status
    """
    novo_status = serializers.ChoiceField(choices=Solicitacao.ETAPA_CHOICES)
    observacoes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_novo_status(self, value):
        """Valida se a transição de status é permitida"""
        solicitacao = self.context.get('solicitacao')
        if not solicitacao:
            raise serializers.ValidationError("Solicitação não encontrada")
        
        # Validação de transições permitidas baseada no status atual
        valid_transitions = {
            'Solicitação': ['Requisição'],
            'Requisição': ['Suprimentos'],
            'Suprimentos': ['Em Cotação'],
            'Em Cotação': ['Pedido de Compras'],
            'Pedido de Compras': ['Aguardando Aprovação'],
            'Aguardando Aprovação': ['Aprovado', 'Reprovado'],
            'Aprovado': ['Compra feita'],
            'Compra feita': ['Aguardando Entrega'],
            'Aguardando Entrega': ['Pedido Finalizado'],
        }
        
        current_status = solicitacao.status
        allowed_statuses = valid_transitions.get(current_status, [])
        
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f"Transição de '{current_status}' para '{value}' não é permitida. "
                f"Status permitidos: {', '.join(allowed_statuses)}"
            )
        
        return value
