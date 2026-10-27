"""Variáveis disponíveis em todos os templates."""
from atividades.dashboard.views.common import TAMANHO_MAXIMO_MB


def limites_upload(request):
    return {'arquivo_max_mb': TAMANHO_MAXIMO_MB}
