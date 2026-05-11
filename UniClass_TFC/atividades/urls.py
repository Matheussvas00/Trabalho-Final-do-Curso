"""
URLs principais do app atividades
"""
from django.urls import path, include

urlpatterns = [
    # Autenticação
    path('', include('atividades.authentication.urls')),

    # Dashboard
    path('dashboard/', include('atividades.dashboard.urls')),
]
