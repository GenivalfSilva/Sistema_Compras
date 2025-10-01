"""
Modelos para dashboard e métricas do Sistema de Compras V2
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

User = get_user_model()


class MetricaDashboard(models.Model):
    """
    Armazena métricas calculadas do dashboard para cache/performance
    """
    METRIC_TYPES = [
        ('total_solicitacoes', 'Total de Solicitações'),
        ('solicitacoes_pendentes', 'Solicitações Pendentes'),
        ('solicitacoes_aprovadas', 'Solicitações Aprovadas'),
        ('solicitacoes_reprovadas', 'Solicitações Reprovadas'),
        ('valor_total_mes', 'Valor Total do Mês'),
        ('tempo_medio_aprovacao', 'Tempo Médio de Aprovação'),
        ('sla_cumprido', 'SLA Cumprido (%)'),
        ('solicitacoes_por_departamento', 'Solicitações por Departamento'),
        ('solicitacoes_por_status', 'Solicitações por Status'),
        ('top_solicitantes', 'Top Solicitantes'),
    ]
    
    tipo_metrica = models.CharField('Tipo da Métrica', max_length=50, choices=METRIC_TYPES)
    periodo = models.CharField('Período', max_length=20, choices=[
        ('hoje', 'Hoje'),
        ('semana', 'Esta Semana'),
        ('mes', 'Este Mês'),
        ('trimestre', 'Este Trimestre'),
        ('ano', 'Este Ano'),
        ('total', 'Total'),
    ])
    valor = models.JSONField('Valor da Métrica')
    data_calculo = models.DateTimeField('Data do Cálculo', auto_now=True)
    
    class Meta:
        verbose_name = 'Métrica do Dashboard'
        verbose_name_plural = 'Métricas do Dashboard'
        unique_together = ['tipo_metrica', 'periodo']
        ordering = ['-data_calculo']
    
    def __str__(self):
        return f"{self.get_tipo_metrica_display()} - {self.get_periodo_display()}"
    
    @classmethod
    def get_or_calculate_metric(cls, tipo_metrica, periodo, force_recalculate=False):
        """
        Busca métrica do cache ou calcula se necessário
        """
        if not force_recalculate:
            try:
                metric = cls.objects.get(tipo_metrica=tipo_metrica, periodo=periodo)
                # Verifica se métrica não está muito desatualizada (1 hora)
                if timezone.now() - metric.data_calculo < timedelta(hours=1):
                    return metric.valor
            except cls.DoesNotExist:
                pass
        
        # Calcula nova métrica
        valor = cls._calculate_metric(tipo_metrica, periodo)
        
        # Salva no cache
        metric, created = cls.objects.get_or_create(
            tipo_metrica=tipo_metrica,
            periodo=periodo,
            defaults={'valor': valor}
        )
        if not created:
            metric.valor = valor
            metric.save()
        
        return valor
    
    @classmethod
    def _calculate_metric(cls, tipo_metrica, periodo):
        """
        Calcula métrica específica para o período
        """
        from apps.solicitacoes.models import Solicitacao
        
        # Define filtro de data baseado no período
        now = timezone.now()
        date_filter = {}
        
        if periodo == 'hoje':
            date_filter['created_at__date'] = now.date()
        elif periodo == 'semana':
            start_week = now - timedelta(days=now.weekday())
            date_filter['created_at__gte'] = start_week.replace(hour=0, minute=0, second=0)
        elif periodo == 'mes':
            date_filter['created_at__year'] = now.year
            date_filter['created_at__month'] = now.month
        elif periodo == 'trimestre':
            quarter_start = datetime(now.year, ((now.month - 1) // 3) * 3 + 1, 1)
            date_filter['created_at__gte'] = quarter_start
        elif periodo == 'ano':
            date_filter['created_at__year'] = now.year
        
        queryset = Solicitacao.objects.filter(**date_filter)
        
        if tipo_metrica == 'total_solicitacoes':
            return queryset.count()
        
        elif tipo_metrica == 'solicitacoes_pendentes':
            return queryset.exclude(status__in=['Aprovado', 'Reprovado', 'Pedido Finalizado']).count()
        
        elif tipo_metrica == 'solicitacoes_aprovadas':
            return queryset.filter(status='Aprovado').count()
        
        elif tipo_metrica == 'solicitacoes_reprovadas':
            return queryset.filter(status='Reprovado').count()
        
        elif tipo_metrica == 'valor_total_mes':
            total = queryset.filter(
                status__in=['Aprovado', 'Pedido Finalizado']
            ).aggregate(
                total=Sum('valor_final')
            )['total']
            return float(total or 0)
        
        elif tipo_metrica == 'tempo_medio_aprovacao':
            aprovadas = queryset.filter(
                status__in=['Aprovado', 'Reprovado'],
                data_aprovacao__isnull=False
            )
            if aprovadas.exists():
                tempos = []
                for sol in aprovadas:
                    tempo = (sol.data_aprovacao - sol.created_at).days
                    tempos.append(tempo)
                return sum(tempos) / len(tempos) if tempos else 0
            return 0
        
        elif tipo_metrica == 'sla_cumprido':
            total = queryset.count()
            if total == 0:
                return 100
            
            cumpridas = 0
            for sol in queryset:
                if sol.is_sla_cumprido():
                    cumpridas += 1
            
            return round((cumpridas / total) * 100, 2)
        
        elif tipo_metrica == 'solicitacoes_por_departamento':
            return dict(
                queryset.values('departamento').annotate(
                    count=Count('id')
                ).values_list('departamento', 'count')
            )
        
        elif tipo_metrica == 'solicitacoes_por_status':
            return dict(
                queryset.values('status').annotate(
                    count=Count('id')
                ).values_list('status', 'count')
            )
        
        elif tipo_metrica == 'top_solicitantes':
            return list(
                queryset.values('solicitante_nome').annotate(
                    count=Count('id')
                ).order_by('-count')[:10].values_list('solicitante_nome', 'count')
            )
        
        return {}


class RelatorioAgendado(models.Model):
    """
    Relatórios agendados para geração automática
    """
    FREQUENCY_CHOICES = [
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
        ('quarterly', 'Trimestral'),
    ]
    
    REPORT_TYPES = [
        ('sla_performance', 'Performance de SLA'),
        ('solicitacoes_departamento', 'Solicitações por Departamento'),
        ('aprovacoes_valores', 'Aprovações por Valores'),
        ('tempo_processamento', 'Tempo de Processamento'),
        ('auditoria_completa', 'Auditoria Completa'),
    ]
    
    nome = models.CharField('Nome do Relatório', max_length=100)
    tipo_relatorio = models.CharField('Tipo', max_length=30, choices=REPORT_TYPES)
    frequencia = models.CharField('Frequência', max_length=20, choices=FREQUENCY_CHOICES)
    destinatarios = models.JSONField('Destinatários (emails)', default=list)
    ativo = models.BooleanField('Ativo', default=True)
    
    # Filtros do relatório
    filtros = models.JSONField('Filtros', default=dict)
    
    # Controle de execução
    ultima_execucao = models.DateTimeField('Última Execução', null=True, blank=True)
    proxima_execucao = models.DateTimeField('Próxima Execução')
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Criado por')
    
    class Meta:
        verbose_name = 'Relatório Agendado'
        verbose_name_plural = 'Relatórios Agendados'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.get_frequencia_display()})"


class AlertaSLA(models.Model):
    """
    Alertas de SLA próximos do vencimento ou vencidos
    """
    ALERT_TYPES = [
        ('warning', 'Aviso (80% do SLA)'),
        ('danger', 'Perigo (100% do SLA)'),
        ('overdue', 'Vencido'),
    ]
    
    solicitacao = models.ForeignKey(
        'solicitacoes.Solicitacao',
        on_delete=models.CASCADE,
        verbose_name='Solicitação'
    )
    tipo_alerta = models.CharField('Tipo do Alerta', max_length=20, choices=ALERT_TYPES)
    mensagem = models.TextField('Mensagem')
    
    # Controle de notificação
    notificado = models.BooleanField('Notificado', default=False)
    data_notificacao = models.DateTimeField('Data da Notificação', null=True, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Alerta de SLA'
        verbose_name_plural = 'Alertas de SLA'
        ordering = ['-created_at']
        unique_together = ['solicitacao', 'tipo_alerta']
    
    def __str__(self):
        return f"Alerta {self.get_tipo_alerta_display()} - Sol. #{self.solicitacao.id}"
