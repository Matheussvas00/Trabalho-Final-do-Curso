"""
Utilitários compartilhados entre as views do dashboard
"""
import os

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


# ── Validação de arquivos enviados (RNF010) ─────────────────────
# Na Vercel o corpo da requisição tem limite de 4,5 MB, por isso lá o padrão é 4 MB.
# O valor pode ser ajustado pela variável de ambiente ARQUIVO_TAMANHO_MAXIMO_MB.
TAMANHO_MAXIMO_MB = int(os.getenv('ARQUIVO_TAMANHO_MAXIMO_MB', '4' if os.getenv('VERCEL') else '10'))
TAMANHO_MAXIMO_ARQUIVO = TAMANHO_MAXIMO_MB * 1024 * 1024
EXTENSOES_RESPOSTA = ('.pdf', '.docx', '.jpg', '.jpeg', '.png')
EXTENSOES_ATESTADO = ('.pdf', '.jpg', '.jpeg', '.png')


def validar_arquivo(arquivo, extensoes=EXTENSOES_RESPOSTA):
    """Valida formato e tamanho do arquivo. Retorna a mensagem de erro ou None."""
    nome = (arquivo.name or '').lower()
    if not nome.endswith(extensoes):
        if extensoes == EXTENSOES_ATESTADO:
            return 'Formato não suportado. Use PDF, JPG ou PNG.'
        return 'Formato não suportado. Use PDF, DOCX, JPG ou PNG.'
    if arquivo.size > TAMANHO_MAXIMO_ARQUIVO:
        return f'Arquivo muito grande. Limite máximo: {TAMANHO_MAXIMO_MB} MB.'
    return None
