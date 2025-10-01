"""
URLs para o app de usuários
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Autenticação
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('auth/permissions/', views.check_permissions, name='check-permissions'),
    
    # Gerenciamento de usuários
    path('', views.UsuarioListCreateView.as_view(), name='usuario-list-create'),
    path('<int:pk>/', views.UsuarioDetailView.as_view(), name='usuario-detail'),
    path('v1/', views.UsuarioV1ListView.as_view(), name='usuario-v1-list'),
    
    # Test endpoint
    path('test/', views.test_endpoint, name='test'),
]
