"""Views do painel do Administrador.

Escopo: CRUD de Diretores e Cursos.
"""
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from atividades.models import (
    Admin, Diretor, Curso, Usuario, Professor, Aluno, Disciplina, ProfessorDisciplina
)
from .common import base_context


# ── helpers ────────────────────────────────────────────────────
def _admin_required(view_func):
    """Decorator: exige que o usuário logado seja administrador."""
    @wraps(view_func)
    @login_required(login_url='authentication:login')
    def wrapper(request, *args, **kwargs):
        if request.user.tipo_usuario != 'admin':
            messages.error(request, 'Acesso negado.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def _admin_context(request):
    """Contexto base + dados do administrador."""
    ctx = base_context(request)
    try:
        admin_obj = Admin.objects.get(id_admin=request.user)
        ctx['display_name'] = admin_obj.nome_completo
        ctx['admin_obj'] = admin_obj
    except Admin.DoesNotExist:
        ctx['display_name'] = request.user.email
    return ctx


# ══════════════════════════════════════════════════════════════
#  HOME ADMIN
# ══════════════════════════════════════════════════════════════
@_admin_required
def home_admin(request):
    """Dashboard principal do administrador."""
    ctx = _admin_context(request)
    ctx['total_diretores']   = Diretor.objects.count()
    ctx['total_cursos']      = Curso.objects.count()
    ctx['total_professores'] = Professor.objects.count()
    ctx['total_alunos']      = Aluno.objects.count()
    ctx['diretores'] = Diretor.objects.select_related(
        'id_diretor', 'curso_fk'
    ).order_by('nome_diretor')
    ctx['cursos'] = Curso.objects.prefetch_related('disciplinas').order_by('nome_curso')
    ctx['active_page'] = 'inicio'
    return render(request, 'dashboard/home_admin.html', ctx)


# ══════════════════════════════════════════════════════════════
#  CRUD — DIRETORES
# ══════════════════════════════════════════════════════════════
@_admin_required
def gerenciar_diretores(request):
    """Lista todos os diretores com opções de cadastro, edição e exclusão."""
    ctx = _admin_context(request)
    ctx['diretores'] = Diretor.objects.select_related(
        'id_diretor', 'curso_fk'
    ).order_by('nome_diretor')
    ctx['cursos'] = Curso.objects.all().order_by('nome_curso')
    ctx['active_page'] = 'diretores'
    return render(request, 'dashboard/gerenciar_diretores.html', ctx)


@_admin_required
@require_POST
def cadastrar_diretor(request):
    """Cria um novo diretor + usuário vinculado."""
    nome      = request.POST.get('nome_diretor', '').strip()
    sobrenome = request.POST.get('sobrenome_diretor', '').strip()
    email     = request.POST.get('email', '').strip()
    senha     = request.POST.get('senha', '').strip()
    curso_id  = request.POST.get('curso_fk', '').strip()

    if not all([nome, sobrenome, email, senha, curso_id]):
        messages.error(request, 'Todos os campos são obrigatórios (incluindo curso).')
        return redirect('dashboard:gerenciar_diretores')

    if Usuario.objects.filter(email=email).exists():
        messages.error(request, 'Já existe um usuário com esse e-mail.')
        return redirect('dashboard:gerenciar_diretores')

    if len(senha) < 8:
        messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
        return redirect('dashboard:gerenciar_diretores')

    try:
        curso_obj = Curso.objects.get(pk=curso_id)
    except Curso.DoesNotExist:
        messages.error(request, 'Curso não encontrado.')
        return redirect('dashboard:gerenciar_diretores')

    usuario = Usuario(email=email, tipo_usuario='diretor')
    usuario.set_password(senha)
    usuario.save()

    Diretor.objects.create(
        id_diretor=usuario,
        nome_diretor=nome,
        sobrenome_diretor=sobrenome,
        curso_diretor=curso_obj.nome_curso,
        curso_fk=curso_obj,
    )

    messages.success(request, f'Diretor {nome} {sobrenome} cadastrado com sucesso no curso {curso_obj.nome_curso}.')
    return redirect('dashboard:gerenciar_diretores')


@_admin_required
@require_POST
def editar_diretor(request, diretor_id):
    """Atualiza dados de um diretor existente."""
    diretor = get_object_or_404(Diretor, pk=diretor_id)

    diretor.nome_diretor      = request.POST.get('nome_diretor', diretor.nome_diretor).strip()
    diretor.sobrenome_diretor = request.POST.get('sobrenome_diretor', diretor.sobrenome_diretor).strip()

    curso_id = request.POST.get('curso_fk', '').strip()
    if not curso_id:
        messages.error(request, 'Curso é obrigatório para o diretor.')
        return redirect('dashboard:gerenciar_diretores')

    try:
        curso_obj = Curso.objects.get(pk=curso_id)
        diretor.curso_fk = curso_obj
        diretor.curso_diretor = curso_obj.nome_curso  # Sincroniza o campo de texto com o curso vinculado
    except Curso.DoesNotExist:
        messages.error(request, 'Curso não encontrado.')
        return redirect('dashboard:gerenciar_diretores')

    # Alterar senha se fornecida
    nova_senha = request.POST.get('nova_senha', '').strip()
    confirmar_senha = request.POST.get('confirmar_senha', '').strip()

    if nova_senha or confirmar_senha:
        if nova_senha != confirmar_senha:
            messages.error(request, 'As senhas não coincidem.')
            return redirect('dashboard:gerenciar_diretores')

        if len(nova_senha) < 8:
            messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
            return redirect('dashboard:gerenciar_diretores')

        diretor.id_diretor.set_password(nova_senha)
        diretor.id_diretor.save()
        messages.info(request, 'Senha do diretor alterada com sucesso.')

    try:
        diretor.save()
        messages.success(request, f'Diretor {diretor.nome_completo} atualizado com sucesso.')
    except ValueError as e:
        messages.error(request, f'Erro ao atualizar diretor: {str(e)}')

    return redirect('dashboard:gerenciar_diretores')


@_admin_required
@require_POST
def excluir_diretor(request, diretor_id):
    """Inativa um diretor (LGPD — dados preservados, acesso bloqueado)."""
    diretor = get_object_or_404(Diretor, pk=diretor_id)
    nome    = diretor.nome_completo

    diretor.ativo = False
    diretor.save(update_fields=['ativo'])

    # Bloqueia login: marca is_active=False no Usuario via campo is_active simulado
    usuario = diretor.id_diretor
    usuario.email = f'_inativo_{diretor_id}_{usuario.email}'
    usuario.save(update_fields=['email'])

    messages.success(request, f'Diretor {nome} inativado com sucesso (dados preservados conforme LGPD).')
    return redirect('dashboard:gerenciar_diretores')


@_admin_required
@require_POST
def reativar_diretor(request, diretor_id):
    """Reativa um diretor previamente inativado, restaurando o acesso ao sistema."""
    diretor = get_object_or_404(Diretor, pk=diretor_id)
    nome = diretor.nome_completo

    diretor.ativo = True
    diretor.save(update_fields=['ativo'])

    usuario = diretor.id_diretor
    prefix = f'_inativo_{diretor_id}_'
    if usuario.email.startswith(prefix):
        usuario.email = usuario.email[len(prefix):]
        usuario.save(update_fields=['email'])

    messages.success(request, f'Diretor {nome} reativado com sucesso.')
    return redirect('dashboard:gerenciar_diretores')


# ══════════════════════════════════════════════════════════════
#  CRUD — CURSOS (admin)
# ══════════════════════════════════════════════════════════════
@_admin_required
def gerenciar_cursos(request):
    """Lista todos os cursos com opções de cadastro, edição e exclusão."""
    ctx = _admin_context(request)
    ctx['cursos'] = Curso.objects.prefetch_related('disciplinas').order_by('nome_curso')
    ctx['active_page'] = 'cursos'
    return render(request, 'dashboard/gerenciar_cursos.html', ctx)


@_admin_required
@require_POST
def cadastrar_curso_admin(request):
    """Cadastra um novo curso."""
    nome = request.POST.get('nome_curso', '').strip()

    if not nome:
        messages.error(request, 'O nome do curso é obrigatório.')
        return redirect('dashboard:gerenciar_cursos')

    if Curso.objects.filter(nome_curso=nome).exists():
        messages.error(request, 'Já existe um curso com esse nome.')
        return redirect('dashboard:gerenciar_cursos')

    Curso.objects.create(nome_curso=nome)
    messages.success(request, f'Curso "{nome}" cadastrado com sucesso.')
    return redirect('dashboard:gerenciar_cursos')


@_admin_required
@require_POST
def editar_curso_admin(request, curso_id):
    """Atualiza o nome de um curso."""
    curso = get_object_or_404(Curso, pk=curso_id)
    nome  = request.POST.get('nome_curso', '').strip()

    if not nome:
        messages.error(request, 'O nome do curso é obrigatório.')
        return redirect('dashboard:gerenciar_cursos')

    if Curso.objects.filter(nome_curso=nome).exclude(pk=curso_id).exists():
        messages.error(request, 'Já existe outro curso com esse nome.')
        return redirect('dashboard:gerenciar_cursos')

    curso.nome_curso = nome
    curso.save()
    messages.success(request, f'Curso "{nome}" atualizado com sucesso.')
    return redirect('dashboard:gerenciar_cursos')


@_admin_required
@require_POST
def excluir_curso_admin(request, curso_id):
    """Remove um curso."""
    curso = get_object_or_404(Curso, pk=curso_id)
    nome  = curso.nome_curso
    curso.delete()
    messages.success(request, f'Curso "{nome}" excluído com sucesso.')
    return redirect('dashboard:gerenciar_cursos')


# ══════════════════════════════════════════════════════════════
#  CRUD — DISCIPLINAS (admin)
# ══════════════════════════════════════════════════════════════
@_admin_required
def gerenciar_disciplinas(request):
    """Lista todas as disciplinas com opções de cadastro, edição e exclusão."""
    ctx = _admin_context(request)
    ctx['disciplinas'] = Disciplina.objects.select_related(
        'curso_fk'
    ).prefetch_related(
        'professores_disciplina__id_professorfk'
    ).order_by('nome_disciplina')
    ctx['professores'] = Professor.objects.order_by('nome_professor')
    ctx['cursos'] = Curso.objects.order_by('nome_curso')
    ctx['active_page'] = 'disciplinas'
    return render(request, 'dashboard/gerenciar_disciplinas.html', ctx)


@_admin_required
@require_POST
def cadastrar_disciplina(request):
    """Cadastra uma nova disciplina (sem vincular professores)."""
    codigo   = request.POST.get('codigo_disciplina', '').strip()
    nome     = request.POST.get('nome_disciplina', '').strip()
    curso_id = request.POST.get('curso_fk', '').strip()

    if not all([codigo, nome, curso_id]):
        messages.error(request, 'Código, nome e curso são obrigatórios.')
        return redirect('dashboard:gerenciar_disciplinas')

    if Disciplina.objects.filter(codigo_disciplina=codigo).exists():
        messages.error(request, 'Já existe uma disciplina com esse código.')
        return redirect('dashboard:gerenciar_disciplinas')

    curso = get_object_or_404(Curso, pk=curso_id)

    # Cria a disciplina (sem vincular professores - isso é feito ao cadastrar/editar professor)
    disciplina = Disciplina.objects.create(
        codigo_disciplina=codigo,
        nome_disciplina=nome,
        curso_fk=curso,
    )

    messages.success(request, f'Disciplina "{nome}" cadastrada com sucesso.')
    return redirect('dashboard:gerenciar_disciplinas')


@_admin_required
@require_POST
def editar_disciplina(request, disciplina_codigo):
    """Atualiza uma disciplina existente (nome e curso apenas)."""
    disciplina = get_object_or_404(Disciplina, pk=disciplina_codigo)

    disciplina.nome_disciplina = request.POST.get('nome_disciplina', disciplina.nome_disciplina).strip()

    curso_id = request.POST.get('curso_fk', '').strip()
    if curso_id:
        disciplina.curso_fk = get_object_or_404(Curso, pk=curso_id)

    disciplina.save()

    messages.success(request, f'Disciplina "{disciplina.nome_disciplina}" atualizada com sucesso.')
    return redirect('dashboard:gerenciar_disciplinas')


@_admin_required
@require_POST
def excluir_disciplina(request, disciplina_codigo):
    """Remove uma disciplina (e todos os vínculos com professores através do CASCADE)."""
    disciplina = get_object_or_404(Disciplina, pk=disciplina_codigo)
    nome = disciplina.nome_disciplina
    disciplina.delete()  # CASCADE vai remover os vínculos em ProfessorDisciplina automaticamente
    messages.success(request, f'Disciplina "{nome}" excluída com sucesso.')
    return redirect('dashboard:gerenciar_disciplinas')
