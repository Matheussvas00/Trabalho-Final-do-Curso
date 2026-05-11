"""
Utilitários compartilhados entre as views do dashboard
"""
from django.utils import timezone
from atividades.models import Notificacao


def get_greeting():
    hour = timezone.localtime(timezone.now()).hour
    if hour < 12:
        return "Bom dia"
    elif hour < 18:
        return "Boa tarde"
    return "Boa noite"


def base_context(request):
    """Contexto base compartilhado por todas as dashboards."""
    user = request.user
    display_name = user.email.split('@')[0].replace('.', ' ').title()

    notificacoes_nao_lidas = Notificacao.objects.filter(
        id_usuariodestino=user, lida=False
    ).count()

    return {
        'user': user,
        'greeting': get_greeting(),
        'display_name': display_name,
        'notificacoes_nao_lidas': notificacoes_nao_lidas,
    }
