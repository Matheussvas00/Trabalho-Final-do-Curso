"""
Views do dashboard do Diretor — inclui CRUD de alunos, professores, cursos, disciplinas, portarias e validação
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from atividades.models import (
    Aluno, Professor, Diretor, Atividade, Atestado, AtestadoDisciplina,
    Disciplina, Notificacao, RespostaAtividade, Usuario, Curso
)
from .common import base_context


# ── helpers ────────────────────────────────────────────────────
def _diretor_required(view_func):
    """Decorator: exige que o usuário logado seja diretor."""
    from functools import wraps

    @wraps(view_func)
    @login_required(login_url='authentication:login')
    def wrapper(request, *args, **kwargs):
        if request.user.tipo_usuario != 'diretor':
            messages.error(request, 'Acesso negado.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def _diretor_context(request):
    """Contexto base + dados do diretor."""
    ctx = base_context(request)
    try:
        diretor = Diretor.objects.get(id_diretor=request.user)
        ctx['display_name'] = diretor.nome_completo
        ctx['diretor'] = diretor
    except Diretor.DoesNotExist:
        pass
    return ctx


# ══════════════════════════════════════════════════════════════
#  HOME DIRETOR
# ══════════════════════════════════════════════════════════════
@_diretor_required
def home_diretor(request):
    """Dashboard principal do diretor."""
    ctx = _diretor_context(request)

    ctx['total_alunos']      = Aluno.objects.count()
    ctx['total_professores'] = Professor.objects.count()
    ctx['total_cursos']      = Curso.objects.count()
    ctx['total_atestados']   = Atestado.objects.filter(status='pendente').count()
    ctx['total_portarias']   = Atestado.objects.count()

    # Listas completas para CRUD inline
    ctx['alunos'] = Aluno.objects.select_related('id_aluno').all().order_by('nome_aluno', 'sobrenome_aluno')
    ctx['professores'] = Professor.objects.prefetch_related(
        'disciplinas'
    ).select_related('id_professor').order_by('nome_professor')

    ctx['cursos'] = Curso.objects.prefetch_related('disciplinas').all().order_by('nome_curso')

    ctx['todos_usuarios'] = Usuario.objects.all().order_by('tipo_usuario', 'email')

    # Portarias (atestados)
    ctx['portarias'] = Atestado.objects.select_related(
        'id_alunofk'
    ).prefetch_related(
        'disciplinas_afetadas__codigo_disciplina'
    ).order_by('-data_inicio')

    # Respostas aguardando validação do diretor (aprovadas pelo professor)
    ctx['respostas_para_validar'] = RespostaAtividade.objects.filter(
        status='aprovada'
    ).select_related(
        'id_atividade__codigo_disciplinafk',
        'id_atividade__id_professorfk',
        'id_atividade__id_atestado__id_alunofk',
        'id_alunofk',
    ).order_by('-data_envio')
    ctx['total_validar'] = ctx['respostas_para_validar'].count()

    return render(request, 'dashboard/home_diretor.html', ctx)


# ══════════════════════════════════════════════════════════════
#  REDEFINIR SENHA
# ══════════════════════════════════════════════════════════════
@_diretor_required
@require_POST
def redefinir_senha(request, usuario_id):
    """Permite ao diretor redefinir a senha de qualquer usuário."""
    nova_senha = request.POST.get('nova_senha', '')
    confirmar  = request.POST.get('confirmar_senha', '')

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


# ══════════════════════════════════════════════════════════════
#  CRUD — ALUNOS
# ══════════════════════════════════════════════════════════════
@_diretor_required
def gerenciar_alunos(request):
    """Lista todos os alunos com opções de cadastro, edição e inativação."""
    ctx = _diretor_context(request)
    ctx['alunos'] = Aluno.objects.prefetch_related('cursos').all().order_by('nome_aluno', 'sobrenome_aluno')
    ctx['cursos'] = Curso.objects.all().order_by('nome_curso')
    ctx['active_page'] = 'alunos'
    return render(request, 'dashboard/gerenciar_alunos.html', ctx)


@_diretor_required
@require_POST
def cadastrar_aluno(request):
    """Cadastra um novo aluno e cria o usuário vinculado."""
    nome       = request.POST.get('nome_aluno', '').strip()
    sobrenome  = request.POST.get('sobrenome_aluno', '').strip()
    curso      = request.POST.get('curso_aluno', '').strip()
    periodo    = request.POST.get('periodo', '').strip()
    matricula  = request.POST.get('matricula_aluno', '').strip()
    email      = request.POST.get('email', '').strip()
    senha      = request.POST.get('senha', '').strip()

    if not all([nome, sobrenome, curso, periodo, matricula, email, senha]):
        messages.error(request, 'Todos os campos são obrigatórios.')
        return redirect('dashboard:index')

    if Usuario.objects.filter(email=email).exists():
        messages.error(request, 'Já existe um usuário com esse e-mail.')
        return redirect('dashboard:index')

    if Aluno.objects.filter(matricula_aluno=matricula).exists():
        messages.error(request, 'Já existe um aluno com essa matrícula.')
        return redirect('dashboard:index')

    if len(senha) < 8:
        messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
        return redirect('dashboard:index')

    # Cria usuário
    usuario = Usuario(email=email, tipo_usuario='aluno')
    usuario.set_password(senha)
    usuario.save()

    # Cria aluno vinculado ao usuário
    aluno = Aluno.objects.create(
        id_aluno=usuario,
        nome_aluno=nome,
        sobrenome_aluno=sobrenome,
        curso_aluno=curso,
        periodo=periodo,
        matricula_aluno=matricula,
    )

    messages.success(request, f'Aluno {nome} {sobrenome} cadastrado com sucesso.')

    # Vincula aos cursos selecionados
    cursos_ids = request.POST.getlist('cursos')
    if cursos_ids:
        aluno.cursos.set(Curso.objects.filter(pk__in=cursos_ids))

    return redirect('dashboard:gerenciar_alunos')


@_diretor_required
@require_POST
def editar_aluno(request, aluno_id):
    """Atualiza os dados de um aluno existente."""
    aluno = get_object_or_404(Aluno, pk=aluno_id)

    aluno.nome_aluno      = request.POST.get('nome_aluno', aluno.nome_aluno).strip()
    aluno.sobrenome_aluno = request.POST.get('sobrenome_aluno', aluno.sobrenome_aluno).strip()
    aluno.curso_aluno     = request.POST.get('curso_aluno', aluno.curso_aluno).strip()
    aluno.periodo         = request.POST.get('periodo', aluno.periodo).strip()

    nova_matricula = request.POST.get('matricula_aluno', aluno.matricula_aluno).strip()
    if nova_matricula != aluno.matricula_aluno:
        if Aluno.objects.filter(matricula_aluno=nova_matricula).exclude(pk=aluno_id).exists():
            messages.error(request, 'Já existe outro aluno com essa matrícula.')
            return redirect('dashboard:index')
        aluno.matricula_aluno = nova_matricula

    aluno.save()
    messages.success(request, f'Aluno {aluno.nome_completo} atualizado com sucesso.')

    # Atualiza cursos vinculados
    if 'cursos' in request.POST or request.POST.getlist('cursos'):
        cursos_ids = request.POST.getlist('cursos')
        aluno.cursos.set(Curso.objects.filter(pk__in=cursos_ids))

    return redirect('dashboard:gerenciar_alunos')


@_diretor_required
@require_POST
def excluir_aluno(request, aluno_id):
    """Remove um aluno e seu usuário vinculado (por matrícula)."""
    aluno = get_object_or_404(Aluno, pk=aluno_id)
    nome = aluno.nome_completo
    usuario = aluno.id_aluno  # OneToOneField → objeto Usuario

    aluno.delete()
    usuario.delete()

    messages.success(request, f'Aluno {nome} excluído com sucesso.')
    return redirect('dashboard:gerenciar_alunos')


# ══════════════════════════════════════════════════════════════
#  CRUD — PROFESSORES
# ══════════════════════════════════════════════════════════════
@_diretor_required
def gerenciar_professores(request):
    """Lista todos os professores com opções de cadastro, edição e exclusão."""
    ctx = _diretor_context(request)
    ctx['professores'] = Professor.objects.prefetch_related(
        'disciplinas', 'cursos'
    ).select_related('id_professor').order_by('nome_professor')
    ctx['cursos'] = Curso.objects.all().order_by('nome_curso')
    ctx['active_page'] = 'professores'
    return render(request, 'dashboard/gerenciar_professores.html', ctx)


@_diretor_required
@require_POST
def cadastrar_professor(request):
    """Cadastra um novo professor e cria o usuário vinculado."""
    nome      = request.POST.get('nome_professor', '').strip()
    sobrenome = request.POST.get('sobrenome_professor', '').strip()
    curso     = request.POST.get('curso_professor', '').strip()
    email     = request.POST.get('email', '').strip()
    senha     = request.POST.get('senha', '').strip()

    if not all([nome, sobrenome, curso, email, senha]):
        messages.error(request, 'Todos os campos são obrigatórios.')
        return redirect('dashboard:index')

    if Usuario.objects.filter(email=email).exists():
        messages.error(request, 'Já existe um usuário com esse e-mail.')
        return redirect('dashboard:index')

    if len(senha) < 8:
        messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
        return redirect('dashboard:index')

    # Cria usuário
    usuario = Usuario(email=email, tipo_usuario='professor')
    usuario.set_password(senha)
    usuario.save()

    # Cria professor vinculado
    professor = Professor.objects.create(
        id_professor=usuario,
        nome_professor=nome,
        sobrenome_professor=sobrenome,
        curso_professor=curso,
    )

    messages.success(request, f'Professor {nome} {sobrenome} cadastrado com sucesso.')

    # Vincula aos cursos selecionados
    cursos_ids = request.POST.getlist('cursos')
    if cursos_ids:
        professor.cursos.set(Curso.objects.filter(pk__in=cursos_ids))

    return redirect('dashboard:gerenciar_professores')


@_diretor_required
@require_POST
def editar_professor(request, professor_id):
    """Atualiza os dados de um professor existente."""
    professor = get_object_or_404(Professor, pk=professor_id)

    professor.nome_professor      = request.POST.get('nome_professor', professor.nome_professor).strip()
    professor.sobrenome_professor = request.POST.get('sobrenome_professor', professor.sobrenome_professor).strip()
    professor.curso_professor     = request.POST.get('curso_professor', professor.curso_professor).strip()

    professor.save()
    messages.success(request, f'Professor {professor.nome_completo} atualizado com sucesso.')

    # Atualiza cursos vinculados
    cursos_ids = request.POST.getlist('cursos')
    professor.cursos.set(Curso.objects.filter(pk__in=cursos_ids))

    return redirect('dashboard:gerenciar_professores')


@_diretor_required
@require_POST
def excluir_professor(request, professor_id):
    """Remove um professor e seu usuário vinculado."""
    professor = get_object_or_404(Professor, pk=professor_id)
    nome = professor.nome_completo
    usuario = professor.id_professor  # OneToOneField → é o objeto Usuario

    professor.delete()
    usuario.delete()

    messages.success(request, f'Professor {nome} excluído com sucesso.')
    return redirect('dashboard:gerenciar_professores')


# ══════════════════════════════════════════════════════════════
#  CRUD — CURSOS
# ══════════════════════════════════════════════════════════════
@_diretor_required
@require_POST
def cadastrar_curso(request):
    """Cadastra um novo curso."""
    nome = request.POST.get('nome_curso', '').strip()

    if not nome:
        messages.error(request, 'O nome do curso é obrigatório.')
        return redirect('dashboard:index')

    if Curso.objects.filter(nome_curso=nome).exists():
        messages.error(request, 'Já existe um curso com esse nome.')
        return redirect('dashboard:index')

    Curso.objects.create(nome_curso=nome)
    messages.success(request, f'Curso "{nome}" cadastrado com sucesso.')
    return redirect('dashboard:index')


@_diretor_required
@require_POST
def editar_curso(request, curso_id):
    """Atualiza o nome de um curso existente."""
    curso = get_object_or_404(Curso, pk=curso_id)
    nome = request.POST.get('nome_curso', '').strip()

    if not nome:
        messages.error(request, 'O nome do curso é obrigatório.')
        return redirect('dashboard:index')

    if Curso.objects.filter(nome_curso=nome).exclude(pk=curso_id).exists():
        messages.error(request, 'Já existe outro curso com esse nome.')
        return redirect('dashboard:index')

    curso.nome_curso = nome
    curso.save()
    messages.success(request, f'Curso "{nome}" atualizado com sucesso.')
    return redirect('dashboard:index')


@_diretor_required
@require_POST
def excluir_curso(request, curso_id):
    """Remove um curso."""
    curso = get_object_or_404(Curso, pk=curso_id)
    nome = curso.nome_curso
    curso.delete()
    messages.success(request, f'Curso "{nome}" excluído com sucesso.')
    return redirect('dashboard:index')


# ══════════════════════════════════════════════════════════════
#  CRUD — PORTARIAS (Atestados)
# ══════════════════════════════════════════════════════════════
@_diretor_required
def gerenciar_portarias(request):
    """Página dedicada ao CRUD de portarias."""
    ctx = _diretor_context(request)
    ctx['portarias'] = Atestado.objects.select_related(
        'id_alunofk'
    ).prefetch_related(
        'disciplinas_afetadas__codigo_disciplina'
    ).order_by('-data_inicio')
    ctx['alunos'] = Aluno.objects.all().order_by('nome_aluno', 'sobrenome_aluno')
    ctx['disciplinas'] = Disciplina.objects.select_related('id_professorfk').order_by('nome_disciplina')
    ctx['active_page'] = 'portarias'
    return render(request, 'dashboard/gerenciar_portarias.html', ctx)


@_diretor_required
@require_POST
def cadastrar_portaria(request):
    """Diretor cadastra uma nova portaria (atestado) para um aluno."""
    aluno_id       = request.POST.get('id_alunofk', '').strip()
    data_inicio    = request.POST.get('data_inicio', '').strip()
    data_fim       = request.POST.get('data_fim', '').strip()
    cid            = request.POST.get('CID', '').strip()
    disciplinas_ids = request.POST.getlist('disciplinas')

    if not all([aluno_id, data_inicio, data_fim]):
        messages.error(request, 'Aluno, data início e data fim são obrigatórios.')
        return redirect('dashboard:index')

    aluno = get_object_or_404(Aluno, pk=aluno_id)

    portaria = Atestado.objects.create(
        id_alunofk=aluno,
        data_inicio=data_inicio,
        data_fim=data_fim,
        CID=cid or None,
        status='pendente',
    )

    for disc_id in disciplinas_ids:
        try:
            disciplina = Disciplina.objects.get(pk=disc_id)
            AtestadoDisciplina.objects.create(
                id_atestado=portaria,
                codigo_disciplina=disciplina,
            )
        except Disciplina.DoesNotExist:
            pass

    messages.success(request, f'Portaria #{portaria.id_atestado} criada para {aluno.nome_completo}.')
    return redirect('dashboard:gerenciar_portarias')


@_diretor_required
@require_POST
def editar_portaria(request, portaria_id):
    """Diretor edita uma portaria existente."""
    portaria = get_object_or_404(Atestado, pk=portaria_id)

    portaria.data_inicio = request.POST.get('data_inicio', portaria.data_inicio)
    portaria.data_fim = request.POST.get('data_fim', portaria.data_fim)
    portaria.CID = request.POST.get('CID', '').strip() or None

    novo_status = request.POST.get('status', '').strip()
    if novo_status in ['pendente', 'aprovado', 'rejeitado']:
        portaria.status = novo_status

    portaria.save()

    # Atualiza disciplinas
    disciplinas_ids = request.POST.getlist('disciplinas')
    if disciplinas_ids or 'disciplinas' in request.POST:
        portaria.disciplinas_afetadas.all().delete()
        for disc_id in disciplinas_ids:
            try:
                disciplina = Disciplina.objects.get(pk=disc_id)
                AtestadoDisciplina.objects.create(
                    id_atestado=portaria,
                    codigo_disciplina=disciplina,
                )
            except Disciplina.DoesNotExist:
                pass

    messages.success(request, f'Portaria #{portaria.id_atestado} atualizada.')
    return redirect('dashboard:gerenciar_portarias')


@_diretor_required
@require_POST
def excluir_portaria(request, portaria_id):
    """Diretor exclui uma portaria."""
    portaria = get_object_or_404(Atestado, pk=portaria_id)
    portaria.delete()
    messages.success(request, 'Portaria excluída com sucesso.')
    return redirect('dashboard:gerenciar_portarias')


# ══════════════════════════════════════════════════════════════
#  VALIDAÇÃO FINAL — DIRETOR
# ══════════════════════════════════════════════════════════════
@_diretor_required
def gerenciar_validacoes(request):
    """Página dedicada à validação de respostas aprovadas pelo professor."""
    ctx = _diretor_context(request)
    ctx['respostas_para_validar'] = RespostaAtividade.objects.filter(
        status='aprovada'
    ).select_related(
        'id_atividade__codigo_disciplinafk',
        'id_atividade__id_professorfk',
        'id_atividade__id_atestado__id_alunofk',
        'id_alunofk',
    ).order_by('-data_envio')
    ctx['total_validar'] = ctx['respostas_para_validar'].count()
    ctx['active_page'] = 'validar'
    return render(request, 'dashboard/gerenciar_validacoes.html', ctx)


@_diretor_required
@require_POST
def validar_resposta(request, resposta_id):
    """Diretor valida uma resposta já aprovada pelo professor."""
    resposta = get_object_or_404(RespostaAtividade, pk=resposta_id, status='aprovada')
    resposta.status = 'validada'
    resposta.save()
    messages.success(request, f'Resposta #{resposta.id_resposta} validada com sucesso.')
    return redirect('dashboard:gerenciar_validacoes')


@_diretor_required
@require_POST
def rejeitar_validacao(request, resposta_id):
    """Diretor rejeita uma resposta que foi aprovada pelo professor (devolve)."""
    resposta = get_object_or_404(RespostaAtividade, pk=resposta_id, status='aprovada')
    resposta.status = 'pendente'
    resposta.observacao_professor = request.POST.get('observacao', '') or resposta.observacao_professor
    resposta.save()
    messages.success(request, f'Resposta #{resposta.id_resposta} devolvida para reavaliação.')
    return redirect('dashboard:gerenciar_validacoes')


# ══════════════════════════════════════════════════════════════
#  API JSON — uso interno (JS filtro dinâmico de disciplinas)
# ══════════════════════════════════════════════════════════════
@_diretor_required
def api_aluno_disciplinas(request, aluno_id):
    """Retorna as disciplinas em que o aluno está matriculado (JSON)."""
    aluno = get_object_or_404(Aluno, pk=aluno_id)
    disciplinas = list(
        Disciplina.objects.filter(
            alunos_matriculados__id_alunofk=aluno
        ).values('codigo_disciplina', 'nome_disciplina')
    )
    return JsonResponse({'disciplinas': disciplinas})
