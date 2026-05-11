"""
Views do dashboard do UniClass
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from atividades.models import (
    Aluno, Professor, Diretor, Atividade, Atestado,
    Disciplina, Notificacao, RespostaAtividade, Usuario
)


def _get_greeting():
    hour = timezone.localtime(timezone.now()).hour
    if hour < 12:
        return "Bom dia"
    elif hour < 18:
        return "Boa tarde"
    return "Boa noite"


@login_required(login_url='authentication:login')
def dashboard_view(request):
    """Dashboard principal — roteia para o template correto por tipo de usuário."""
    user = request.user
    display_name = user.email.split('@')[0].replace('.', ' ').title()

    notificacoes_nao_lidas = Notificacao.objects.filter(
        id_usuariodestino=user, lida=False
    ).count()

    base_ctx = {
        'user': user,
        'greeting': _get_greeting(),
        'display_name': display_name,
        'notificacoes_nao_lidas': notificacoes_nao_lidas,
    }

    # ── ALUNO ──────────────────────────────────────────────────
    if user.tipo_usuario == 'aluno':
        aluno = Aluno.objects.filter(
            matricula_aluno=user.email.split('@')[0]
        ).first()

        ctx = {**base_ctx}

        if aluno:
            ctx['display_name'] = aluno.nome_completo
            ctx['aluno'] = aluno
            ctx['total_atividades'] = Atividade.objects.filter(
                id_atestado__id_alunofk=aluno, status='pendente'
            ).count()
            ctx['total_atestados'] = Atestado.objects.filter(
                id_alunofk=aluno
            ).count()
            ctx['total_disciplinas'] = aluno.matriculas.count()
            ctx['atividades_recentes'] = Atividade.objects.filter(
                id_atestado__id_alunofk=aluno, status='pendente'
            ).select_related('codigo_disciplinafk').order_by('-data_criacao')[:5]
            ctx['atestados_recentes'] = Atestado.objects.filter(
                id_alunofk=aluno
            ).order_by('-data_inicio')[:5]

        return render(request, 'dashboard/home_aluno.html', ctx)

    # ── PROFESSOR ──────────────────────────────────────────────
    elif user.tipo_usuario == 'professor':
        ctx = {**base_ctx}

        try:
            professor = Professor.objects.get(id_professor=user)
            ctx['display_name'] = professor.nome_completo
            ctx['professor'] = professor

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
            ctx['atividades_recentes'] = Atividade.objects.filter(
                id_professorfk=professor
            ).select_related('codigo_disciplinafk').order_by('-data_criacao')[:5]
            ctx['respostas_recentes'] = RespostaAtividade.objects.filter(
                id_atividade__id_professorfk=professor,
                status='pendente'
            ).select_related('id_atividade', 'id_alunofk').order_by('-data_envio')[:5]

        except Professor.DoesNotExist:
            pass

        return render(request, 'dashboard/home_professor.html', ctx)

    # ── DIRETOR ────────────────────────────────────────────────
    elif user.tipo_usuario == 'diretor':
        ctx = {**base_ctx}

        try:
            diretor = Diretor.objects.get(id_diretor=user)
            ctx['display_name'] = diretor.nome_completo
            ctx['diretor'] = diretor
        except Diretor.DoesNotExist:
            pass

        ctx['total_alunos']      = Aluno.objects.count()
        ctx['total_professores'] = Professor.objects.count()
        ctx['total_disciplinas'] = Disciplina.objects.count()
        ctx['total_atestados']   = Atestado.objects.filter(status='pendente').count()
        ctx['atividades_validar'] = RespostaAtividade.objects.filter(
            status='aprovada'
        ).count()

        ctx['atestados_recentes'] = Atestado.objects.filter(
            status='pendente'
        ).select_related('id_alunofk').order_by('-data_inicio')[:5]

        ctx['atividades_para_validar'] = RespostaAtividade.objects.filter(
            status='aprovada'
        ).select_related(
            'id_atividade__codigo_disciplinafk', 'id_alunofk'
        ).order_by('-data_envio')[:5]

        ctx['professores_recentes'] = Professor.objects.prefetch_related(
            'disciplinas'
        ).order_by('nome_professor')[:6]

        ctx['disciplinas_recentes'] = Disciplina.objects.select_related(
            'id_professorfk'
        ).order_by('nome_disciplina')[:6]

        ctx['todos_usuarios'] = Usuario.objects.all().order_by('tipo_usuario', 'email')

        return render(request, 'dashboard/home_diretor.html', ctx)

    # fallback
    return render(request, 'dashboard/index.html', base_ctx)


@login_required(login_url='authentication:login')
@require_POST
def redefinir_senha_diretor_view(request, usuario_id):
    """Permite ao diretor redefinir a senha de qualquer usuário."""
    if request.user.tipo_usuario != 'diretor':
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard:index')

    nova_senha  = request.POST.get('nova_senha', '')
    confirmar   = request.POST.get('confirmar_senha', '')

    if len(nova_senha) < 8:
        messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
        return redirect('dashboard:index')

    if nova_senha != confirmar:
        messages.error(request, 'As senhas não coincidem.')
        return redirect('dashboard:index')

    try:
        usuario = Usuario.objects.get(pk=usuario_id)
        usuario.set_password(nova_senha)
        usuario.save(update_fields=['senha'])
        messages.success(request, f'Senha de {usuario.email} redefinida com sucesso.')
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')

    return redirect('dashboard:index')

    """
    Dashboard principal com sidebar — redireciona baseado no tipo de usuário
    """
    user = request.user
    display_name = user.email.split('@')[0].replace('.', ' ').title()

    notificacoes_nao_lidas = Notificacao.objects.filter(
        id_usuariodestino=user, lida=False
    ).count()

    context = {
        'user': user,
        'title': 'Início - UniClass',
        'page_title': 'Início',
        'greeting': _get_greeting(),
        'display_name': display_name,
        'notificacoes_nao_lidas': notificacoes_nao_lidas,
    }

    if user.tipo_usuario == 'aluno':
        aluno = Aluno.objects.filter(
            matricula_aluno=user.email.split('@')[0]
        ).first()
        if aluno:
            display_name = aluno.nome_completo
            context['display_name'] = display_name
            context['aluno'] = aluno
            context['total_atividades'] = Atividade.objects.filter(
                id_atestado__id_alunofk=aluno, status='pendente'
            ).count()
            context['total_atestados'] = Atestado.objects.filter(
                id_alunofk=aluno
            ).count()
            context['total_disciplinas'] = aluno.matriculas.count()

    elif user.tipo_usuario == 'professor':
        try:
            professor = Professor.objects.get(id_professor=user)
            display_name = professor.nome_completo
            context['display_name'] = display_name
            context['professor'] = professor
            context['total_atividades'] = Atividade.objects.filter(
                id_professorfk=professor
            ).count()
            context['total_atestados'] = Atestado.objects.filter(
                id_alunofk__matriculas__codigo_disciplinafk__id_professorfk=professor
            ).distinct().count()
            context['total_alunos'] = Aluno.objects.filter(
                matriculas__codigo_disciplinafk__id_professorfk=professor
            ).distinct().count()
        except Professor.DoesNotExist:
            pass

    elif user.tipo_usuario == 'diretor':
        try:
            diretor = Diretor.objects.get(id_diretor=user)
            display_name = diretor.nome_completo
            context['display_name'] = display_name
            context['diretor'] = diretor
        except Diretor.DoesNotExist:
            pass
        context['total_alunos'] = Aluno.objects.count()
        context['total_professores'] = Professor.objects.count()
        context['total_disciplinas'] = Disciplina.objects.count()
        context['total_atestados'] = Atestado.objects.filter(status='pendente').count()

    return render(request, 'dashboard/home.html', context)
