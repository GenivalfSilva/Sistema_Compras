"""
WSGI config for Sistema de Compras V2 project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')

application = get_wsgi_application()
