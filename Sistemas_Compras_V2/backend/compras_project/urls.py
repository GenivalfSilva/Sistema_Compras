"""
URL Configuration for Sistema de Compras V2
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/usuarios/', include('apps.usuarios.urls')),
    path('api/solicitacoes/', include('apps.solicitacoes.urls')),
    path('api/configuracoes/', include('apps.configuracoes.urls')),
    path('api/auditoria/', include('apps.auditoria.urls')),
    
    # Direct catalog endpoint for convenience
    path('api/catalogo/', include('apps.solicitacoes.catalog_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
