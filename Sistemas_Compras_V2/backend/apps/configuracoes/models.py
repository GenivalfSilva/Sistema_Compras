"""
Modelos para configurações do Sistema de Compras V2
Baseado na estrutura do V1 com melhorias
"""
from django.db import models
from django.core.exceptions import ValidationError


class Configuracao(models.Model):
    """
    Modelo para armazenar configurações do sistema - equivalente à tabela configuracoes do V1
    """
    chave = models.CharField('Chave', max_length=100, unique=True)
    valor = models.TextField('Valor')
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)  # V1 tem updated_at, não created_at
    
    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'
        ordering = ['chave']
        db_table = 'configuracoes'  # Use V1 table name
    
    def __str__(self):
        return f"{self.chave}: {self.valor}"
    
    def get_valor_typed(self):
        """Retorna o valor convertido para o tipo correto"""
        # V1 não possui campo 'tipo'. Tentamos inferir de forma segura.
        val = self.valor
        if val is None:
            return None
        s = str(val).strip()
        # boolean
        low = s.lower()
        if low in ('true', 'false'):
            return low == 'true'
        # integer
        try:
            if s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
                return int(s)
        except Exception:
            pass
        # float
        try:
            return float(s)
        except Exception:
            pass
        # json
        try:
            import json
            return json.loads(s)
        except Exception:
            pass
        # fallback: string
        return s
    
    @classmethod
    def get_config(cls, chave, default=None):
        """Método utilitário para buscar configuração"""
        try:
            config = cls.objects.get(chave=chave)
            return config.get_valor_typed()
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_config(cls, chave, valor, tipo='string', descricao=''):
        """Método utilitário para definir configuração"""
        # V1 só tem chave/valor/updated_at; não passar campos inexistentes em defaults
        config, created = cls.objects.get_or_create(
            chave=chave,
            defaults={'valor': str(valor)}
        )
        if not created:
            config.valor = str(valor)
            config.save()
        return config


class ConfiguracaoSLA(models.Model):
    """
    Configurações específicas de SLA por departamento
    """
    departamento = models.CharField('Departamento', max_length=50, unique=True)
    sla_urgente = models.IntegerField('SLA Urgente (dias)', default=1)
    sla_alta = models.IntegerField('SLA Alta (dias)', default=2)
    sla_normal = models.IntegerField('SLA Normal (dias)', default=3)
    sla_baixa = models.IntegerField('SLA Baixa (dias)', default=5)
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração de SLA'
        verbose_name_plural = 'Configurações de SLA'
        ordering = ['departamento']
    
    def __str__(self):
        return f"SLA {self.departamento}"
    
    def get_sla_for_priority(self, prioridade):
        """Retorna SLA para uma prioridade específica"""
        sla_map = {
            'Urgente': self.sla_urgente,
            'Alta': self.sla_alta,
            'Normal': self.sla_normal,
            'Baixa': self.sla_baixa,
        }
        return sla_map.get(prioridade, self.sla_normal)


class LimiteAprovacao(models.Model):
    """
    Limites de aprovação por valor
    """
    nome = models.CharField('Nome do Limite', max_length=100)
    valor_minimo = models.DecimalField('Valor Mínimo', max_digits=12, decimal_places=2, default=0)
    valor_maximo = models.DecimalField('Valor Máximo', max_digits=12, decimal_places=2)
    aprovador_necessario = models.CharField('Aprovador Necessário', max_length=50, choices=[
        ('Gerência', 'Gerência'),
        ('Diretoria', 'Diretoria'),
        ('Especial', 'Aprovação Especial'),
    ])
    ativo = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Limite de Aprovação'
        verbose_name_plural = 'Limites de Aprovação'
        ordering = ['valor_minimo']
    
    def __str__(self):
        return f"{self.nome}: R$ {self.valor_minimo} - R$ {self.valor_maximo}"
    
    @classmethod
    def get_aprovador_for_value(cls, valor):
        """Retorna o aprovador necessário para um valor"""
        limite = cls.objects.filter(
            valor_minimo__lte=valor,
            valor_maximo__gte=valor,
            ativo=True
        ).first()
        return limite.aprovador_necessario if limite else 'Gerência'
