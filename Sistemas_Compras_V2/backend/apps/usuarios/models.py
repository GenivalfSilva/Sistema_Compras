"""
Modelos para gestão de usuários do Sistema de Compras V2
Baseado na estrutura do V1 com melhorias para Django
"""
from django.db import models


class Usuario(models.Model):
    """
    Modelo customizado de usuário baseado no sistema V1
    Perfis: Solicitante, Estoque, Suprimentos, Gerência&Diretoria, Admin
    """
    PERFIL_CHOICES = [
        ('Solicitante', 'Solicitante'),
        ('Estoque', 'Estoque'),
        ('Suprimentos', 'Suprimentos'),
        ('Gerência&Diretoria', 'Gerência & Diretoria'),
        ('Admin', 'Administrador'),
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
    
    # Campos exatos do V1
    username = models.CharField('Username', max_length=150, unique=True)
    nome = models.CharField('Nome Completo', max_length=150)
    perfil = models.CharField('Perfil', max_length=50, choices=PERFIL_CHOICES)
    departamento = models.CharField('Departamento', max_length=50, choices=DEPARTAMENTO_CHOICES)
    senha_hash = models.CharField('Senha Hash', max_length=255)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome']
        db_table = 'usuarios'  # Use V1 table name
    
    def __str__(self):
        return f"{self.nome} ({self.perfil})"
    
    @property
    def display_name(self):
        """Retorna nome para exibição"""
        return self.nome
    
    def has_perfil(self, perfil):
        """Verifica se usuário tem um perfil específico"""
        return self.perfil == perfil
    
    def can_create_solicitacao(self):
        """Verifica se pode criar solicitações"""
        return self.perfil in ['Solicitante', 'Admin']
    
    def can_manage_requisicoes(self):
        """Verifica se pode gerenciar requisições"""
        return self.perfil in ['Estoque', 'Admin']
    
    def can_process_suprimentos(self):
        """Verifica se pode processar suprimentos"""
        return self.perfil in ['Suprimentos', 'Admin']
    
    def can_approve(self):
        """Verifica se pode aprovar pedidos"""
        return self.perfil in ['Gerência&Diretoria', 'Admin']
    
    def is_admin_user(self):
        """Verifica se é administrador"""
        return self.perfil == 'Admin'


class Sessao(models.Model):
    """
    Modelo para gerenciar sessões persistentes (equivalente ao V1)
    """
    id = models.CharField('ID da Sessão', max_length=255, primary_key=True)
    username = models.CharField('Username', max_length=150)  # V1 usa username, não FK
    expires_at = models.DateTimeField('Expira em')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Sessão'
        verbose_name_plural = 'Sessões'
        ordering = ['-created_at']
        db_table = 'sessoes'  # Use V1 table name
    
    def __str__(self):
        return f"Sessão de {self.username}"
    
    @property
    def is_expired(self):
        """Verifica se a sessão está expirada"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
