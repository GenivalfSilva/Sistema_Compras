"""
Modelos para gestão de solicitações do Sistema de Compras V2
Baseado na estrutura completa do V1 SQLite com todos os 44 campos
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Solicitacao(models.Model):
    """
    Modelo principal de solicitações - equivalente à tabela solicitacoes do V1
    Contém todos os 44 campos da estrutura original
    """
    
    # Choices baseados no V1
    PRIORIDADE_CHOICES = [
        ('Urgente', 'Urgente'),
        ('Alta', 'Alta'),
        ('Normal', 'Normal'),
        ('Baixa', 'Baixa'),
    ]
    
    ETAPA_CHOICES = [
        ('Solicitação', 'Solicitação'),
        ('Requisição', 'Requisição'),
        ('Suprimentos', 'Suprimentos'),
        ('Em Cotação', 'Em Cotação'),
        ('Pedido de Compras', 'Pedido de Compras'),
        ('Aguardando Aprovação', 'Aguardando Aprovação'),
        ('Aprovado', 'Aprovado'),
        ('Reprovado', 'Reprovado'),
        ('Compra feita', 'Compra feita'),
        ('Aguardando Entrega', 'Aguardando Entrega'),
        ('Pedido Finalizado', 'Pedido Finalizado'),
    ]
    
    DEPARTAMENTO_CHOICES = [
        ('Manutenção', 'Manutenção'),
        ('TI', 'TI'),
        ('RH', 'RH'),
        ('Financeiro', 'Financeiro'),
        ('Marketing', 'Marketing'),
        ('Operações', 'Operações'),
        ('Outro', 'Outro'),
    ]
    
    # Campos principais (equivalentes ao V1)
    numero_solicitacao_estoque = models.IntegerField('Número da Solicitação', unique=True)
    numero_requisicao = models.IntegerField('Número da Requisição', null=True, blank=True)
    numero_pedido_compras = models.IntegerField('Número do Pedido de Compras', null=True, blank=True)
    
    # Dados do solicitante
    solicitante = models.CharField('Solicitante', max_length=100)
    departamento = models.CharField('Departamento', max_length=50, choices=DEPARTAMENTO_CHOICES)
    descricao = models.TextField('Descrição')
    prioridade = models.CharField('Prioridade', max_length=20, choices=PRIORIDADE_CHOICES, default='Normal')
    local_aplicacao = models.CharField('Local de Aplicação', max_length=200)
    
    # Status e etapas
    status = models.CharField('Status', max_length=50, choices=ETAPA_CHOICES, default='Solicitação')
    etapa_atual = models.CharField('Etapa Atual', max_length=50, choices=ETAPA_CHOICES, default='Solicitação')
    
    # Datas
    carimbo_data_hora = models.DateTimeField('Data/Hora Criação', default=timezone.now)
    data_requisicao = models.DateTimeField('Data da Requisição', null=True, blank=True)
    responsavel_estoque = models.CharField('Responsável Estoque', max_length=100, blank=True)
    data_numero_pedido = models.DateTimeField('Data do Pedido', null=True, blank=True)
    data_cotacao = models.DateTimeField('Data da Cotação', null=True, blank=True)
    data_entrega = models.DateTimeField('Data de Entrega', null=True, blank=True)
    
    # SLA
    sla_dias = models.IntegerField('SLA em Dias', default=3)
    dias_atendimento = models.IntegerField('Dias de Atendimento', null=True, blank=True)
    sla_cumprido = models.CharField('SLA Cumprido', max_length=10, blank=True)
    
    # Observações
    observacoes = models.TextField('Observações', blank=True)
    
    # Campos de requisição
    numero_requisicao_interno = models.CharField('Número Requisição Interno', max_length=50, blank=True)
    data_requisicao_interna = models.DateTimeField('Data Requisição Interna', null=True, blank=True)
    responsavel_suprimentos = models.CharField('Responsável Suprimentos', max_length=100, blank=True)
    
    # Valores
    valor_estimado = models.DecimalField('Valor Estimado', max_digits=12, decimal_places=2, null=True, blank=True)
    valor_final = models.DecimalField('Valor Final', max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Fornecedores
    fornecedor_recomendado = models.CharField('Fornecedor Recomendado', max_length=200, blank=True)
    fornecedor_final = models.CharField('Fornecedor Final', max_length=200, blank=True)
    
    # Campos JSON (equivalentes ao V1)
    anexos_requisicao = models.JSONField('Anexos da Requisição', default=list, blank=True)
    cotacoes = models.JSONField('Cotações', default=list, blank=True)
    aprovacoes = models.JSONField('Aprovações', default=list, blank=True)
    historico_etapas = models.JSONField('Histórico de Etapas', default=list, blank=True)
    itens = models.JSONField('Itens da Solicitação', default=list, blank=True)
    
    # Campos de entrega
    data_entrega_prevista = models.DateTimeField('Data Entrega Prevista', null=True, blank=True)
    data_entrega_real = models.DateTimeField('Data Entrega Real', null=True, blank=True)
    entrega_conforme = models.CharField('Entrega Conforme', max_length=10, blank=True)
    nota_fiscal = models.CharField('Número da Nota Fiscal', max_length=50, blank=True)
    responsavel_recebimento = models.CharField('Responsável Recebimento', max_length=100, blank=True)
    observacoes_entrega = models.TextField('Observações da Entrega', blank=True)
    observacoes_finalizacao = models.TextField('Observações da Finalização', blank=True)
    data_finalizacao = models.DateTimeField('Data de Finalização', null=True, blank=True)
    
    # Campos adicionais
    tipo_solicitacao = models.CharField('Tipo de Solicitação', max_length=50, blank=True)
    justificativa = models.TextField('Justificativa', blank=True)
    observacoes_requisicao = models.TextField('Observações da Requisição', blank=True)
    observacoes_pedido_compras = models.TextField('Observações do Pedido de Compras', blank=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    # Remove updated_at - não existe no V1
    
    class Meta:
        verbose_name = 'Solicitação'
        verbose_name_plural = 'Solicitações'
        ordering = ['-numero_solicitacao_estoque']
        db_table = 'solicitacoes'  # Use V1 table name
        indexes = [
            models.Index(fields=['numero_solicitacao_estoque']),
            models.Index(fields=['status']),
            models.Index(fields=['solicitante']),
            models.Index(fields=['departamento']),
            models.Index(fields=['prioridade']),
        ]
    
    def __str__(self):
        return f"Sol. #{self.numero_solicitacao_estoque} - {self.solicitante}"
    
    def save(self, *args, **kwargs):
        # Sincroniza status e etapa_atual
        if self.status != self.etapa_atual:
            self.etapa_atual = self.status
        
        # Calcula SLA baseado na prioridade
        if not self.sla_dias:
            sla_map = settings.COMPRAS_SETTINGS['SLA_PADRAO']
            self.sla_dias = sla_map.get(self.prioridade, 3)
        
        super().save(*args, **kwargs)
    
    @property
    def is_finalizada(self):
        """Verifica se a solicitação está finalizada"""
        return self.status in ['Pedido Finalizado', 'Reprovado']
    
    @property
    def pode_mover_para_proxima_etapa(self):
        """Verifica se pode mover para próxima etapa"""
        return not self.is_finalizada
    
    def calcular_dias_atendimento(self):
        """Calcula dias de atendimento até agora"""
        if self.is_finalizada and self.data_finalizacao:
            data_fim = self.data_finalizacao
        else:
            data_fim = timezone.now()
        
        delta = data_fim - self.carimbo_data_hora
        return delta.days
    
    def verificar_sla_cumprido(self):
        """Verifica se o SLA foi cumprido"""
        dias_atendimento = self.calcular_dias_atendimento()
        return "Sim" if dias_atendimento <= self.sla_dias else "Não"
    
    # ===== Métodos auxiliares usados pelos serializers/views =====
    def get_sla_days(self):
        """Retorna o total de dias de SLA para a solicitação"""
        return int(self.sla_dias or 0)
    
    def get_dias_em_andamento(self):
        """Retorna os dias decorridos desde a criação (ou até finalização)"""
        return int(self.calcular_dias_atendimento())
    
    def is_sla_vencido(self):
        """True se o SLA foi excedido"""
        try:
            return self.get_dias_em_andamento() > self.get_sla_days()
        except Exception:
            return False
    
    def is_sla_proximo_vencimento(self):
        """True se está a 1 dia do vencimento (e ainda não vencido)"""
        try:
            dias = self.get_dias_em_andamento()
            sla = self.get_sla_days()
            return (dias >= max(sla - 1, 0)) and not self.is_sla_vencido()
        except Exception:
            return False
    
    def get_sla_percentage_used(self):
        """Percentual de SLA consumido (0-100+)"""
        sla = self.get_sla_days()
        if sla <= 0:
            return 0
        return min(100, int((self.get_dias_em_andamento() / sla) * 100))
    
    def get_proximo_aprovador(self):
        """Retorna o tipo de aprovador necessário baseado no valor"""
        if not self.valor_final:
            return "Gerência"
        
        limite_gerencia = settings.COMPRAS_SETTINGS['LIMITE_GERENCIA']
        limite_diretoria = settings.COMPRAS_SETTINGS['LIMITE_DIRETORIA']
        
        if self.valor_final <= limite_gerencia:
            return "Gerência"
        elif self.valor_final <= limite_diretoria:
            return "Diretoria"
        else:
            return "Aprovação Especial"


class CatalogoProduto(models.Model):
    """
    Catálogo de produtos - equivalente à tabela catalogo_produtos do V1
    """
    codigo = models.CharField('Código', max_length=50, unique=True)
    nome = models.CharField('Nome', max_length=200)
    categoria = models.CharField('Categoria', max_length=100, blank=True)
    unidade = models.CharField('Unidade', max_length=10, default='UN')
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Produto do Catálogo'
        verbose_name_plural = 'Produtos do Catálogo'
        ordering = ['codigo']
        db_table = 'catalogo_produtos'  # Use V1 table name
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Movimentacao(models.Model):
    """
    Histórico de movimentações - equivalente à tabela movimentacoes do V1
    """
    numero_solicitacao = models.IntegerField('Número da Solicitação')
    etapa_origem = models.CharField('Etapa Origem', max_length=50)
    etapa_destino = models.CharField('Etapa Destino', max_length=50)
    usuario = models.CharField('Usuário', max_length=100)
    data_movimentacao = models.DateTimeField('Data da Movimentação', auto_now_add=True)
    observacoes = models.TextField('Observações', blank=True)
    
    class Meta:
        verbose_name = 'Movimentação'
        verbose_name_plural = 'Movimentações'
        ordering = ['-data_movimentacao']
        db_table = 'movimentacoes'
    
    def __str__(self):
        return f"Sol. #{self.numero_solicitacao}: {self.etapa_origem} → {self.etapa_destino}"
