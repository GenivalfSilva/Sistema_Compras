"""
Modelos para auditoria do Sistema de Compras V2
Baseado na estrutura do V1 com melhorias
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

User = get_user_model()


class AuditoriaAdmin(models.Model):
    """
    Modelo para auditoria administrativa - equivalente à tabela auditoria_admin do V1
    """
    ACTION_CHOICES = [
        ('CREATE', 'Criação'),
        ('UPDATE', 'Atualização'),
        ('DELETE', 'Exclusão'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('APPROVE', 'Aprovação'),
        ('REJECT', 'Rejeição'),
        ('MOVE', 'Movimentação'),
        ('CONFIG', 'Configuração'),
        ('EXPORT', 'Exportação'),
        ('IMPORT', 'Importação'),
    ]
    
    # Campos exatos do V1
    usuario = models.CharField('Usuário', max_length=150)  # V1 usa TEXT, não FK
    acao = models.CharField('Ação', max_length=20, choices=ACTION_CHOICES)
    modulo = models.CharField('Módulo', max_length=100)
    detalhes = models.TextField('Detalhes', blank=True)
    solicitacao_id = models.IntegerField('ID da Solicitação', null=True, blank=True)
    ip_address = models.CharField('Endereço IP', max_length=45, blank=True)
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Auditoria Administrativa'
        verbose_name_plural = 'Auditorias Administrativas'
        ordering = ['-timestamp']
        db_table = 'auditoria_admin'  # Use V1 table name
        indexes = [
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['acao', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.usuario} - {self.get_acao_display()} - {self.timestamp}"

    # ===== Utilitário de logging compatível com V1 =====
    @classmethod
    def log_action(
        cls,
        usuario=None,
        acao: str = "INFO",
        descricao: str = "",
        objeto=None,
        request=None,
        **kwargs,
    ):
        """
        Registra uma ação na tabela V1 `auditoria_admin` mapeando os campos disponíveis.
        - `usuario`: User ou string; armazenamos como username.
        - `acao`: uma das ACTION_CHOICES (fallback para 'INFO' se inválida).
        - `descricao`: texto descritivo; salvo em `detalhes`.
        - `objeto`: se for uma Solicitacao, tentamos preencher `solicitacao_id` com seu id.
        - `request`: usado para capturar IP.
        - `kwargs`: ignorados ou serializados dentro de `detalhes`.
        """
        try:
            username = None
            if usuario is None:
                username = "sistema"
            elif hasattr(usuario, "username"):
                username = getattr(usuario, "username") or "sistema"
            else:
                username = str(usuario)

            # Normaliza ação
            valid_actions = {c[0] for c in cls.ACTION_CHOICES}
            action_norm = acao if acao in valid_actions else "INFO"

            # Módulo inferido do objeto
            modulo = objeto.__class__.__name__ if objeto is not None else "Sistema"

            # Captura IP
            ip = None
            if request is not None:
                xff = request.META.get("HTTP_X_FORWARDED_FOR")
                if xff:
                    ip = xff.split(",")[0]
                else:
                    ip = request.META.get("REMOTE_ADDR")

            # Solicitação id, se aplicável
            sol_id = None
            try:
                from apps.solicitacoes.models import Solicitacao  # local import para evitar ciclos
                if isinstance(objeto, Solicitacao):
                    sol_id = objeto.id
            except Exception:
                pass

            # Monta detalhes
            extra = {k: v for k, v in kwargs.items() if k not in ("usuario", "acao", "objeto", "request")}
            detalhes_dict = {"descricao": descricao}
            if extra:
                detalhes_dict["extra"] = extra
            detalhes_text = json.dumps(detalhes_dict, default=str, ensure_ascii=False)

            cls.objects.create(
                usuario=username,
                acao=action_norm,
                modulo=modulo,
                detalhes=detalhes_text,
                solicitacao_id=sol_id,
                ip_address=ip or "",
            )
        except Exception:
            # Fail-safe: nunca quebrar o fluxo por conta da auditoria
            return


class LogSistema(models.Model):
    """
    Logs gerais do sistema (erros, warnings, info)
    """
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Informação'),
        ('WARNING', 'Aviso'),
        ('ERROR', 'Erro'),
        ('CRITICAL', 'Crítico'),
    ]
    
    level = models.CharField('Nível', max_length=10, choices=LEVEL_CHOICES)
    logger_name = models.CharField('Logger', max_length=100)
    message = models.TextField('Mensagem')
    module = models.CharField('Módulo', max_length=100, blank=True)
    function = models.CharField('Função', max_length=100, blank=True)
    line_number = models.IntegerField('Linha', null=True, blank=True)
    
    # Contexto adicional
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    request_path = models.CharField('Caminho da Requisição', max_length=255, blank=True)
    
    # Dados extras em JSON
    extra_data = models.JSONField('Dados Extras', null=True, blank=True)
    
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Log do Sistema'
        verbose_name_plural = 'Logs do Sistema'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['logger_name', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.logger_name} - {self.timestamp}"


class HistoricoLogin(models.Model):
    """
    Histórico de logins e tentativas de acesso
    """
    STATUS_CHOICES = [
        ('SUCCESS', 'Sucesso'),
        ('FAILED', 'Falha'),
        ('BLOCKED', 'Bloqueado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    username_tentativa = models.CharField('Username Tentativa', max_length=150)
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField('Endereço IP')
    user_agent = models.TextField('User Agent', blank=True)
    motivo_falha = models.CharField('Motivo da Falha', max_length=255, blank=True)
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True)
    sessao_id = models.CharField('ID da Sessão', max_length=40, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Histórico de Login'
        verbose_name_plural = 'Históricos de Login'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.username_tentativa} - {self.get_status_display()} - {self.timestamp}"
