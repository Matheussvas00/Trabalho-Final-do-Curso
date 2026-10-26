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


# ── Validação de arquivos enviados (RNF010) ─────────────────────
TAMANHO_MAXIMO_ARQUIVO = 10 * 1024 * 1024  # 10 MB
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
        return 'Arquivo muito grande. Limite máximo: 10 MB.'
    return None
