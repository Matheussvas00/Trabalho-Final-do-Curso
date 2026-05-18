"""
Views de Notificações — leitura e confirmação de leitura
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from atividades.models import Notificacao
from .common import base_context


@login_required(login_url='authentication:login')
def notificacoes(request):
    """Lista todas as notificações do usuário logado."""
    user = request.user
    todas = Notificacao.objects.filter(id_usuariodestino=user).order_by('-data_hora')

    ctx = base_context(request)
    ctx.update({
        'notificacoes': todas,
        'total_nao_lidas': todas.filter(lida=False).count(),
        'active_page': 'notificacoes',
    })
    return render(request, 'dashboard/notificacoes.html', ctx)


@login_required(login_url='authentication:login')
@require_POST
def marcar_lida(request, notificacao_id):
    """Marca uma notificação específica como lida (chamada via fetch/AJAX)."""
    notif = get_object_or_404(Notificacao, id_notificacao=notificacao_id, id_usuariodestino=request.user)
    notif.lida = True
    notif.save(update_fields=['lida'])
    return JsonResponse({'ok': True, 'nao_lidas': Notificacao.objects.filter(
        id_usuariodestino=request.user, lida=False).count()})


@login_required(login_url='authentication:login')
@require_POST
def marcar_todas_lidas(request):
    """Marca todas as notificações do usuário como lidas."""
    count = Notificacao.objects.filter(id_usuariodestino=request.user, lida=False).update(lida=True)
    return JsonResponse({'ok': True, 'marcadas': count, 'nao_lidas': 0})
