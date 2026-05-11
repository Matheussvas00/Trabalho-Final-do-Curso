"""
Views do dashboard do Aluno — visualiza portarias (read-only), atividades e envia respostas
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from atividades.models import (
    Aluno, Atividade, Atestado, RespostaAtividade
)
from .common import base_context


def _get_aluno(request):
    """Retorna o Aluno vinculado ao usuário logado ou None."""
    try:
        return Aluno.objects.get(id_aluno=request.user)
    except Aluno.DoesNotExist:
        return None


def _aluno_context(request):
    """Contexto base + dados do aluno."""
    ctx = base_context(request)
    aluno = _get_aluno(request)
    if aluno:
        ctx['display_name'] = aluno.nome_completo
        ctx['aluno'] = aluno
    return ctx


@login_required(login_url='authentication:login')
def home_aluno(request):
    """Dashboard principal do aluno."""
    ctx = _aluno_context(request)
    aluno = ctx.get('aluno')

    if aluno:
        # Atividades pendentes (criadas pelos professores para este aluno)
        atividades_pendentes = Atividade.objects.filter(
            id_atestado__id_alunofk=aluno, status='pendente'
        ).select_related('codigo_disciplinafk', 'id_professorfk', 'id_atestado')
        ctx['total_atividades'] = atividades_pendentes.count()
        ctx['atividades_pendentes'] = atividades_pendentes.order_by('-data_criacao')

        # Portarias (read-only)
        ctx['portarias'] = Atestado.objects.filter(
            id_alunofk=aluno
        ).prefetch_related('disciplinas_afetadas__codigo_disciplina').order_by('-data_inicio')
        ctx['total_portarias'] = ctx['portarias'].count()

        ctx['total_disciplinas'] = aluno.matriculas.count()

        # Respostas já enviadas pelo aluno (para saber quais atividades já respondeu)
        ctx['respostas'] = RespostaAtividade.objects.filter(
            id_alunofk=aluno
        ).select_related('id_atividade__codigo_disciplinafk').order_by('-data_envio')
        ctx['atividades_respondidas_ids'] = set(
            ctx['respostas'].values_list('id_atividade_id', flat=True)
        )

    return render(request, 'dashboard/home_aluno.html', ctx)


# ══════════════════════════════════════════════════════════════
#  ENVIAR RESPOSTA DE ATIVIDADE
# ══════════════════════════════════════════════════════════════
@login_required(login_url='authentication:login')
@require_POST
def enviar_resposta(request, atividade_id):
    """Aluno envia uma resposta para uma atividade."""
    aluno = _get_aluno(request)
    if not aluno:
        messages.error(request, 'Perfil de aluno não encontrado.')
        return redirect('dashboard:index')

    atividade = get_object_or_404(Atividade, pk=atividade_id)

    # Verifica se a atividade pertence a uma portaria deste aluno
    if atividade.id_atestado.id_alunofk != aluno:
        messages.error(request, 'Você não tem permissão para responder esta atividade.')
        return redirect('dashboard:index')

    # Verifica se já respondeu e se a resposta anterior foi rejeitada
    resposta_existente = RespostaAtividade.objects.filter(
        id_atividade=atividade, id_alunofk=aluno
    ).first()

    descricao = request.POST.get('descricao', '').strip()
    arquivo = request.POST.get('arquivo', '').strip()

    if resposta_existente:
        if resposta_existente.status == 'rejeitada':
            # Re-envio permitido
            resposta_existente.arquivo = arquivo or None
            resposta_existente.status = 'pendente'
            resposta_existente.observacao_professor = None
            from django.utils import timezone
            resposta_existente.data_envio = timezone.now()
            resposta_existente.save()
            messages.success(request, f'Resposta reenviada para "{atividade.titulo}".')
        else:
            messages.error(request, 'Você já enviou uma resposta para esta atividade.')
    else:
        RespostaAtividade.objects.create(
            id_atividade=atividade,
            id_alunofk=aluno,
            arquivo=arquivo or None,
        )
        messages.success(request, f'Resposta enviada para "{atividade.titulo}".')

    return redirect('dashboard:index')
