"""
Views do dashboard do Professor — ver portarias, criar atividades, avaliar respostas
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from atividades.models import (
    Aluno, Professor, Atividade, Atestado, AtestadoDisciplina,
    RespostaAtividade, Disciplina
)
from .common import base_context


def _get_professor(request):
    try:
        return Professor.objects.get(id_professor=request.user)
    except Professor.DoesNotExist:
        return None


def _professor_context(request):
    ctx = base_context(request)
    professor = _get_professor(request)
    if professor:
        ctx['display_name'] = professor.nome_completo
        ctx['professor'] = professor
    return ctx


@login_required(login_url='authentication:login')
def home_professor(request):
    """Dashboard principal do professor."""
    ctx = _professor_context(request)
    professor = ctx.get('professor')

    if professor:
        ctx['total_disciplinas'] = professor.disciplinas.count()
        ctx['total_alunos'] = Aluno.objects.filter(
            matriculas__codigo_disciplinafk__id_professorfk=professor
        ).distinct().count()
        ctx['total_atividades'] = Atividade.objects.filter(
            id_professorfk=professor
        ).count()
        ctx['respostas_pendentes'] = RespostaAtividade.objects.filter(
            id_atividade__id_professorfk=professor,
            status='pendente'
        ).count()

        # Portarias que afetam disciplinas deste professor
        # Filtro: somente atestados de alunos que compartilham curso com o professor
        disciplinas_prof = professor.disciplinas.all()
        portaria_ids = AtestadoDisciplina.objects.filter(
            codigo_disciplina__in=disciplinas_prof
        ).values_list('id_atestado_id', flat=True).distinct()

        # Se o professor tem cursos vinculados, filtra apenas alunos desses cursos
        professor_cursos = professor.cursos.all()
        portarias_qs = Atestado.objects.filter(pk__in=portaria_ids, status='aprovado')
        if professor_cursos.exists():
            portarias_qs = portarias_qs.filter(
                id_alunofk__cursos__in=professor_cursos
            ).distinct()

        ctx['portarias'] = portarias_qs.select_related('id_alunofk').prefetch_related(
            'disciplinas_afetadas__codigo_disciplina'
        ).order_by('-data_inicio')

        # Atividades criadas por este professor
        ctx['atividades'] = Atividade.objects.filter(
            id_professorfk=professor
        ).select_related(
            'codigo_disciplinafk', 'id_atestado__id_alunofk'
        ).order_by('-data_criacao')

        # Respostas pendentes para avaliar
        ctx['respostas'] = RespostaAtividade.objects.filter(
            id_atividade__id_professorfk=professor,
            status='pendente'
        ).select_related(
            'id_atividade__codigo_disciplinafk', 'id_alunofk'
        ).order_by('-data_envio')

        # Disciplinas do professor + portarias aprovadas (para o form criar atividade)
        ctx['disciplinas_prof'] = disciplinas_prof.order_by('nome_disciplina')
        ctx['portarias_ativas'] = Atestado.objects.filter(
            pk__in=portaria_ids, status='aprovado'
        ).select_related('id_alunofk')

    return render(request, 'dashboard/home_professor.html', ctx)


# ══════════════════════════════════════════════════════════════
#  CRIAR ATIVIDADE PARA ALUNO AFASTADO
# ══════════════════════════════════════════════════════════════
@login_required(login_url='authentication:login')
@require_POST
def criar_atividade(request):
    """Professor cria uma atividade vinculada a uma portaria."""
    professor = _get_professor(request)
    if not professor:
        messages.error(request, 'Perfil de professor não encontrado.')
        return redirect('dashboard:index')

    portaria_id   = request.POST.get('id_atestado', '').strip()
    disciplina_id = request.POST.get('codigo_disciplinafk', '').strip()
    titulo        = request.POST.get('titulo', '').strip()
    descricao     = request.POST.get('descricao', '').strip()
    data_limite   = request.POST.get('data_limite', '').strip()

    if not all([portaria_id, disciplina_id, titulo]):
        messages.error(request, 'Portaria, disciplina e título são obrigatórios.')
        return redirect('dashboard:index')

    portaria = get_object_or_404(Atestado, pk=portaria_id, status='aprovado')
    disciplina = get_object_or_404(Disciplina, pk=disciplina_id, id_professorfk=professor)

    # Valida que o aluno da portaria está num curso do professor
    professor_cursos = professor.cursos.all()
    if professor_cursos.exists() and not portaria.id_alunofk.cursos.filter(pk__in=professor_cursos).exists():
        messages.error(request, 'O aluno desta portaria não pertence aos seus cursos.')
        return redirect('dashboard:index')

    Atividade.objects.create(
        id_atestado=portaria,
        codigo_disciplinafk=disciplina,
        id_professorfk=professor,
        titulo=titulo,
        descricao=descricao or None,
        data_limite=data_limite or None,
    )

    messages.success(request, f'Atividade "{titulo}" criada para {portaria.id_alunofk.nome_completo}.')
    return redirect('dashboard:index')


# ══════════════════════════════════════════════════════════════
#  AVALIAR RESPOSTA
# ══════════════════════════════════════════════════════════════
@login_required(login_url='authentication:login')
@require_POST
def avaliar_resposta(request, resposta_id):
    """Professor aprova ou reprova uma resposta de atividade."""
    professor = _get_professor(request)
    if not professor:
        messages.error(request, 'Perfil de professor não encontrado.')
        return redirect('dashboard:index')

    resposta = get_object_or_404(
        RespostaAtividade, pk=resposta_id,
        id_atividade__id_professorfk=professor,
        status='pendente'
    )

    acao = request.POST.get('acao', '').strip()
    observacao = request.POST.get('observacao', '').strip()

    if acao == 'aprovar':
        resposta.status = 'aprovada'
        resposta.observacao_professor = observacao or None
        resposta.save()
        messages.success(request, f'Resposta de {resposta.id_alunofk.nome_completo} aprovada. Enviada ao diretor para validação.')
    elif acao == 'reprovar':
        resposta.status = 'rejeitada'
        resposta.observacao_professor = observacao or 'Reprovada pelo professor.'
        resposta.save()
        messages.success(request, f'Resposta de {resposta.id_alunofk.nome_completo} reprovada. O aluno poderá reenviar.')
    else:
        messages.error(request, 'Ação inválida.')

    return redirect('dashboard:index')
