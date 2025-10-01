"""
URLs para o app de configurações
"""
from django.urls import path
from . import views

app_name = 'configuracoes'

urlpatterns = [
    # Configurações gerais
    path('', views.ConfiguracaoListCreateView.as_view(), name='configuracao-list-create'),
    path('<int:pk>/', views.ConfiguracaoDetailView.as_view(), name='configuracao-detail'),
    path('bulk-update/', views.BulkUpdateConfigView.as_view(), name='bulk-update'),
    path('value/<str:chave>/', views.get_config_value, name='get-config-value'),
    
    # Configurações de SLA
    path('sla/', views.ConfiguracaoSLAListCreateView.as_view(), name='sla-list-create'),
    path('sla/<int:pk>/', views.ConfiguracaoSLADetailView.as_view(), name='sla-detail'),
    path('sla/department/<str:departamento>/', views.get_sla_for_department, name='get-sla-department'),
    
    # Limites de aprovação
    path('limites/', views.LimiteAprovacaoListCreateView.as_view(), name='limite-list-create'),
    path('limites/<int:pk>/', views.LimiteAprovacaoDetailView.as_view(), name='limite-detail'),
    path('limites/value/<str:valor>/', views.get_approval_limit_for_value, name='get-approval-limit'),
]
