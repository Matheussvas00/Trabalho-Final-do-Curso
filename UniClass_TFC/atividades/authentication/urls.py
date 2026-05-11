"""
URLs do módulo de autenticação
"""
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('', views.login_view, name='login_root'),  # Rota raiz redireciona para login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
]
