"""
URLs específicas para catálogo de produtos
"""
from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    # Catálogo de produtos
    path('', views.CatalogoProdutoListCreateView.as_view(), name='catalogo-list'),
    path('<int:pk>/', views.CatalogoProdutoDetailView.as_view(), name='catalogo-detail'),
]
