"""
URLs para o app de auditoria
"""
from django.urls import path
from . import views

app_name = 'auditoria'

urlpatterns = [
    # Raiz aponta para lista de auditoria administrativa
    path('', views.AuditoriaAdminListView.as_view(), name='root'),
    # Auditoria administrativa
    path('admin/', views.AuditoriaAdminListView.as_view(), name='admin-list'),
    path('admin/<int:pk>/', views.AuditoriaAdminDetailView.as_view(), name='admin-detail'),
    
    # Logs do sistema
    path('logs/', views.LogSistemaListView.as_view(), name='logs-list'),
    
    # Histórico de login
    path('login/', views.HistoricoLoginListView.as_view(), name='login-list'),
    
    # Estatísticas e relatórios
    path('statistics/', views.audit_statistics, name='statistics'),
    path('user-activity/<int:user_id>/', views.user_activity, name='user-activity'),
    path('export/', views.export_audit_report, name='export-report'),
    path('security-alerts/', views.security_alerts, name='security-alerts'),
]
