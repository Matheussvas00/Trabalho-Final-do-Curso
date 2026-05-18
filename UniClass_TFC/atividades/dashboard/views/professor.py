"""
Views do dashboard do Professor — Criar atividades e fazer pré-validação de respostas
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from atividades.models import (
    Professor, Atividade, Portaria, RespostaAtividade,
    Disciplina, ProfessorDisciplina, Notificacao, Historico
)
from .common import base_context


def _get_professor(request):
    """Retorna o objeto Professor do usuário logado ou None."""
    try:
        return Professor.objects.get(id_professor=request.user)
    except Professor.DoesNotExist:
        return None


def _professor_context(request):
    """Contexto base para todas as views do professor."""
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

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    # Estatísticas básicas
    disciplinas_ids = ProfessorDisciplina.objects.filter(
        id_professorfk=professor
    ).values_list('codigo_disciplinafk', flat=True)

    ctx['total_disciplinas'] = len(disciplinas_ids)
    ctx['total_atividades'] = Atividade.objects.filter(
        id_professorfk=professor
    ).count()
    ctx['respostas_pendentes'] = RespostaAtividade.objects.filter(
        id_atividade__id_professorfk=professor,
        status_professor='pendente'
    ).count()

    # Portarias abertas para disciplinas que o professor leciona
    portarias = Portaria.objects.filter(
        disciplinas_portaria__codigo_disciplinafk__in=disciplinas_ids
    ).select_related('id_alunofk', 'id_diretorfk').distinct()

    ctx['portarias'] = portarias

    # Disciplinas do professor (usadas no modal de criar atividade)
    from atividades.models import Disciplina
    ctx['disciplinas_prof'] = Disciplina.objects.filter(
        codigo_disciplina__in=disciplinas_ids
    ).select_related('curso_fk')

    # Atividades criadas pelo professor (últimas 10 para o dashboard)
    ctx['atividades'] = Atividade.objects.filter(
        id_professorfk=professor
    ).select_related(
        'codigo_disciplinafk',
        'id_portariafk__id_alunofk'
    ).order_by('-data_criacao')[:10]

    # Respostas pendentes de validação
    ctx['respostas'] = RespostaAtividade.objects.filter(
        id_atividade__id_professorfk=professor,
        status_professor='pendente'
    ).select_related(
        'id_atividade__codigo_disciplinafk',
        'id_alunofk'
    ).order_by('data_envio')[:10]

    return render(request, 'dashboard/home_professor.html', ctx)


@login_required(login_url='authentication:login')
def gerenciar_atividades(request):
    """Lista todas as atividades criadas pelo professor."""
    ctx = _professor_context(request)
    professor = ctx.get('professor')

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    atividades = Atividade.objects.filter(
        id_professorfk=professor
    ).select_related('id_portariafk', 'id_portariafk__id_alunofk').order_by('-data_criacao')

    ctx['atividades'] = atividades
    return render(request, 'dashboard/gerenciar_atividades.html', ctx)


@login_required(login_url='authentication:login')
def cadastrar_atividade(request):
    """Criar nova atividade para uma portaria."""
    ctx = _professor_context(request)
    professor = ctx.get('professor')

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    # Buscar portarias em que o professor pode criar atividades
    # (disciplinas que ele leciona e prazo ainda válido)
    hoje = timezone.now().date()
    disciplinas_ids = ProfessorDisciplina.objects.filter(
        id_professorfk=professor
    ).values_list('codigo_disciplinafk', flat=True)

    portarias = Portaria.objects.filter(
        disciplinas_portaria__codigo_disciplinafk__in=disciplinas_ids,
        prazo_professor_criar_atividades__gte=hoje
    ).select_related('id_alunofk', 'id_diretorfk').distinct()

    if request.method == 'POST':
        portaria_id = request.POST.get('id_portaria')
        codigo_disciplina = request.POST.get('codigo_disciplina')
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()

        errors = []
        if not portaria_id:
            errors.append("Selecione a portaria.")
        if not codigo_disciplina:
            errors.append("Selecione a disciplina.")
        if not titulo:
            errors.append("O título é obrigatório.")
        if not descricao:
            errors.append("A descrição é obrigatória.")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            portaria = get_object_or_404(Portaria, pk=portaria_id)
            disciplina = get_object_or_404(Disciplina, pk=codigo_disciplina)

            # data_limite_resposta vem da portaria — não pode ser alterada pelo professor
            data_limite_resposta = portaria.prazo_aluno_responder

            # Verifica que a disciplina pertence à portaria E é lecionada pelo professor
            if not portaria.disciplinas.filter(pk=codigo_disciplina).exists():
                messages.error(request, "A disciplina selecionada não faz parte desta portaria.")
            elif codigo_disciplina not in [str(d) for d in disciplinas_ids]:
                messages.error(request, "Você não está vinculado a esta disciplina.")
            else:
                try:
                    with transaction.atomic():
                        # Salva arquivo anexo, se enviado
                        anexo_path = None
                        arquivo_upload = request.FILES.get('anexo')
                        if arquivo_upload:
                            from django.core.files.storage import default_storage
                            from django.core.files.base import ContentFile
                            anexo_path = default_storage.save(
                                f'atividades/{arquivo_upload.name}',
                                ContentFile(arquivo_upload.read())
                            )
                        atividade = Atividade(
                            id_portariafk=portaria,
                            id_professorfk=professor,
                            codigo_disciplinafk=disciplina,
                            titulo=titulo,
                            descricao=descricao,
                            data_limite_resposta=data_limite_resposta,
                            data_criacao=timezone.now(),
                            anexo=anexo_path,
                        )
                        atividade.save()
                        # Notifica o aluno da portaria
                        Notificacao.objects.create(
                            id_usuariodestino=portaria.id_alunofk.id_aluno,
                            titulo='Nova Atividade Disponível',
                            mensagem=(
                                f'O professor {professor.nome_completo} criou a atividade '
                                f'"{titulo}" para a disciplina {disciplina.nome_disciplina} '
                                f'(Portaria nº {portaria.numero_portaria}). '
                                f'Prazo para resposta: {data_limite_resposta.strftime("%d/%m/%Y")}.'
                            )
                        )
                        # Registra no histórico
                        Historico.objects.create(
                            id_usuario=request.user,
                            acao='atividade_criada',
                            descricao=f'Atividade "{titulo}" criada para a portaria nº {portaria.numero_portaria} — disciplina {disciplina.nome_disciplina}.'
                        )
                    messages.success(request, f"Atividade '{titulo}' criada com sucesso!")
                    return redirect('dashboard:gerenciar_atividades')
                except ValueError as e:
                    messages.error(request, str(e))

    ctx['portarias'] = portarias
    # Serializa portarias com suas disciplinas para o JS
    portarias_data = {}
    for p in portarias:
        # Disciplinas desta portaria que o professor leciona
        discs = p.disciplinas.filter(
            codigo_disciplina__in=disciplinas_ids
        ).values('codigo_disciplina', 'nome_disciplina')
        portarias_data[str(p.pk)] = {
            'prazo': p.prazo_aluno_responder.strftime('%Y-%m-%d'),
            'disciplinas': list(discs),
        }
    ctx['portarias_json'] = portarias_data
    return render(request, 'dashboard/cadastrar_atividade.html', ctx)


@login_required(login_url='authentication:login')
def editar_atividade(request, id_atividade):
    """Editar uma atividade existente."""
    ctx = _professor_context(request)
    professor = ctx.get('professor')

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    atividade = get_object_or_404(Atividade, id_atividade=id_atividade, id_professorfk=professor)

    if request.method == 'POST':
        atividade.titulo = request.POST.get('titulo')
        atividade.descricao = request.POST.get('descricao')
        data_str = request.POST.get('data_limite_resposta')
        if data_str:
            try:
                from datetime import date
                atividade.data_limite_resposta = date.fromisoformat(data_str)
            except ValueError:
                messages.error(request, "Data de prazo inválida. Use o formato AAAA-MM-DD.")
                ctx['atividade'] = atividade
                return render(request, 'dashboard/editar_atividade.html', ctx)

        try:
            atividade.save()
            messages.success(request, "Atividade atualizada com sucesso!")
            return redirect('dashboard:gerenciar_atividades')
        except ValueError as e:
            messages.error(request, str(e))

    ctx['atividade'] = atividade
    return render(request, 'dashboard/editar_atividade.html', ctx)


@login_required(login_url='authentication:login')
@require_POST
def Inativar_atividade(request, id_atividade):
    """Inativar uma atividade."""
    professor = _get_professor(request)

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    atividade = get_object_or_404(Atividade, id_atividade=id_atividade, id_professorfk=professor)
    titulo = atividade.titulo
    atividade.delete()
    messages.success(request, f"Atividade '{titulo}' excluída com sucesso!")
    return redirect('dashboard:gerenciar_atividades')


@login_required(login_url='authentication:login')
def validar_respostas(request):
    """Lista respostas pendentes de pré-validação do professor."""
    ctx = _professor_context(request)
    professor = ctx.get('professor')

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    # Respostas de atividades criadas por este professor
    respostas = RespostaAtividade.objects.filter(
        id_atividade__id_professorfk=professor,
        status_professor='pendente'
    ).select_related(
        'id_atividade',
        'id_atividade__codigo_disciplinafk',
        'id_atividade__id_portariafk__id_alunofk'
    ).order_by('data_envio')

    ctx['respostas'] = respostas
    return render(request, 'dashboard/validar_respostas_professor.html', ctx)


@login_required(login_url='authentication:login')
@require_POST
def validar_resposta_professor(request, id_resposta):
    """Aprovar (pré-validar) uma resposta de aluno antes de ir para o diretor."""
    professor = _get_professor(request)

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    resposta = get_object_or_404(
        RespostaAtividade,
        id_resposta=id_resposta,
        id_atividade__id_professorfk=professor
    )

    feedback = request.POST.get('feedback_professor', '')

    try:
        resposta.validar_professor(aprovada=True, observacao=feedback)
        # Notifica o aluno
        Notificacao.objects.create(
            id_usuariodestino=resposta.id_alunofk.id_aluno,
            titulo='Resposta Pré-aprovada pelo Professor',
            mensagem=(
                f'O professor {professor.nome_completo} pré-aprovou sua resposta para a '
                f'atividade "{resposta.id_atividade.titulo}". '
                f'Aguardando validação final do diretor.'
            )
        )
        # Notifica o diretor da portaria
        diretor_usuario = resposta.id_atividade.id_portariafk.id_diretorfk.id_diretor
        Notificacao.objects.create(
            id_usuariodestino=diretor_usuario,
            titulo='Resposta Aguardando Validação Final',
            mensagem=(
                f'O professor {professor.nome_completo} pré-aprovou a resposta do aluno '
                f'{resposta.id_alunofk.nome_completo} para a atividade '
                f'"{resposta.id_atividade.titulo}" (Portaria nº '
                f'{resposta.id_atividade.id_portariafk.numero_portaria}). '
                f'Aguarda sua validação final.'
            )
        )
        messages.success(request, "Resposta pré-aprovada! Enviada para validação final do diretor.")
        # Registra no histórico
        Historico.objects.create(
            id_usuario=request.user,
            acao='resposta_aprovada_prof',
            descricao=f'Resposta #{resposta.pk} do aluno {resposta.id_alunofk.nome_completo} aprovada para a atividade "{resposta.id_atividade.titulo}".'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('dashboard:validar_respostas')


@login_required(login_url='authentication:login')
@require_POST
def rejeitar_resposta_professor(request, id_resposta):
    """Rejeitar uma resposta de aluno (não segue para o diretor)."""
    professor = _get_professor(request)

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    resposta = get_object_or_404(
        RespostaAtividade,
        id_resposta=id_resposta,
        id_atividade__id_professorfk=professor
    )

    feedback = request.POST.get('feedback_professor', '')

    try:
        resposta.validar_professor(aprovada=False, observacao=feedback)
        # Notifica o aluno
        Notificacao.objects.create(
            id_usuariodestino=resposta.id_alunofk.id_aluno,
            titulo='Resposta Rejeitada pelo Professor',
            mensagem=(
                f'O professor {professor.nome_completo} rejeitou sua resposta para a '
                f'atividade "{resposta.id_atividade.titulo}". '
                f'Motivo: {feedback or "Sem observações."} '
                f'Você pode revisar e reenviar a resposta.'
            )
        )
        messages.success(request, "Resposta rejeitada. O aluno poderá revisar e reenviar.")
        # Registra no histórico
        Historico.objects.create(
            id_usuario=request.user,
            acao='resposta_rejeitada_prof',
            descricao=f'Resposta #{resposta.pk} do aluno {resposta.id_alunofk.nome_completo} rejeitada para a atividade "{resposta.id_atividade.titulo}".'
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('dashboard:validar_respostas')


@login_required(login_url='authentication:login')
def criar_atividade(request):
    """Alias para cadastrar_atividade (compatibilidade com __init__.py)."""
    return cadastrar_atividade(request)


@login_required(login_url='authentication:login')
def avaliar_resposta(request):
    """Alias para validar_respostas (compatibilidade com __init__.py)."""
    return validar_respostas(request)


@login_required(login_url='authentication:login')
def portarias_professor(request):
    """Lista todas as portarias cujas disciplinas o professor leciona."""
    ctx = _professor_context(request)
    professor = ctx.get('professor')

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    disciplinas_ids = ProfessorDisciplina.objects.filter(
        id_professorfk=professor
    ).values_list('codigo_disciplinafk', flat=True)

    portarias = Portaria.objects.filter(
        disciplinas_portaria__codigo_disciplinafk__in=disciplinas_ids
    ).select_related('id_alunofk', 'id_diretorfk').distinct().order_by('-data_criacao')

    ctx['portarias'] = portarias
    ctx['disciplinas_ids'] = list(disciplinas_ids)
    ctx['active_page'] = 'portarias'
    return render(request, 'dashboard/portarias_professor.html', ctx)


@login_required(login_url='authentication:login')
def disciplinas_professor(request):
    """Lista as disciplinas lecionadas pelo professor."""
    ctx = _professor_context(request)
    professor = ctx.get('professor')

    if not professor:
        messages.error(request, "Você não está registrado como professor.")
        return redirect('dashboard:index')

    from atividades.models import Disciplina
    disciplinas_ids = ProfessorDisciplina.objects.filter(
        id_professorfk=professor
    ).values_list('codigo_disciplinafk', flat=True)

    disciplinas = Disciplina.objects.filter(
        codigo_disciplina__in=disciplinas_ids
    ).select_related('curso_fk').order_by('nome_disciplina')

    ctx['disciplinas'] = disciplinas
    ctx['active_page'] = 'disciplinas'
    return render(request, 'dashboard/disciplinas_professor.html', ctx)


from django.http import JsonResponse

@login_required(login_url='authentication:login')
def api_disciplinas_portaria_professor(request, portaria_id):
    """Retorna as disciplinas de uma portaria que o professor leciona (JSON)."""
    professor = _get_professor(request)
    if not professor:
        return JsonResponse({'error': 'Não autorizado'}, status=403)

    disciplinas_ids = ProfessorDisciplina.objects.filter(
        id_professorfk=professor
    ).values_list('codigo_disciplinafk', flat=True)

    portaria = get_object_or_404(Portaria, pk=portaria_id)

    disciplinas = portaria.disciplinas.filter(
        codigo_disciplina__in=disciplinas_ids
    ).values('codigo_disciplina', 'nome_disciplina')

    return JsonResponse({
        'disciplinas': list(disciplinas),
        'prazo': portaria.prazo_aluno_responder.strftime('%Y-%m-%d'),
    })
