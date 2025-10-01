"""
URLs para o app de solicitações
"""
from django.urls import path
from . import views

app_name = 'solicitacoes'

urlpatterns = [
    # Solicitações CRUD
    path('', views.SolicitacaoListCreateView.as_view(), name='solicitacao-list-create'),
    path('<int:pk>/', views.SolicitacaoDetailView.as_view(), name='solicitacao-detail'),
    
    # Ações específicas
    path('<int:pk>/update-status/', views.UpdateStatusView.as_view(), name='update-status'),
    path('<int:pk>/approval/', views.ApprovalView.as_view(), name='approval'),
    
    # Catálogo de produtos
    path('catalogo/', views.CatalogoProdutoListCreateView.as_view(), name='catalogo-list-create'),
    path('catalogo/<int:pk>/', views.CatalogoProdutoDetailView.as_view(), name='catalogo-detail'),
    
    # Dashboard
    path('dashboard/', views.dashboard_data, name='dashboard-data'),
]
