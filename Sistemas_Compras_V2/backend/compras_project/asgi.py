"""
ASGI config for Sistema de Compras V2 project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')

application = get_asgi_application()
