from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.usuarios'
    verbose_name = 'Usuários'
    
    def ready(self):
        # Importar sinais
        import apps.usuarios.signals
