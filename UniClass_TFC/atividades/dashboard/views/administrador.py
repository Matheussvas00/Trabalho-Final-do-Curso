"""Views do painel do Administrador.

Escopo: CRUD de Diretores e Cursos.
"""
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction

from atividades.models import (
    Admin, Diretor, Curso, Usuario, Professor, Aluno, Disciplina
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
    # Cada curso tem um único diretor ativo: o formulário mostra quem já ocupa cada curso
    diretores_ativos = {d.curso_fk_id: d for d in Diretor.objects.filter(ativo=True).order_by('nome_diretor')}
    cursos = list(Curso.objects.all().order_by('nome_curso'))
    for curso in cursos:
        curso.diretor_ativo = diretores_ativos.get(curso.pk)
    ctx['cursos'] = cursos
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

    if not curso_obj.ativo:
        messages.error(
            request,
            f'O curso {curso_obj.nome_curso} está inativo. Reative o curso antes de cadastrar um diretor.'
        )
        return redirect('dashboard:gerenciar_diretores')

    atual = Diretor.diretor_ativo_do_curso(curso_obj)
    if atual:
        messages.error(
            request,
            f'O curso {curso_obj.nome_curso} já tem um diretor ativo ({atual.nome_completo}). '
            f'Cada curso pode ter apenas um diretor: inative o diretor atual antes de cadastrar outro.'
        )
        return redirect('dashboard:gerenciar_diretores')

    with transaction.atomic():
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
        if not curso_obj.ativo and curso_obj.pk != diretor.curso_fk_id:
            messages.error(request, f'O curso {curso_obj.nome_curso} está inativo.')
            return redirect('dashboard:gerenciar_diretores')
        diretor.curso_fk = curso_obj
        diretor.curso_diretor = curso_obj.nome_curso  # Sincroniza o campo de texto com o curso vinculado
    except Curso.DoesNotExist:
        messages.error(request, 'Curso não encontrado.')
        return redirect('dashboard:gerenciar_diretores')

    if diretor.ativo:
        outro = Diretor.diretor_ativo_do_curso(curso_obj, excluir_pk=diretor.pk)
        if outro:
            messages.error(
                request,
                f'O curso {curso_obj.nome_curso} já tem um diretor ativo ({outro.nome_completo}). '
                f'Cada curso pode ter apenas um diretor.'
            )
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
def Inativar_diretor(request, diretor_id):
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

    outro = Diretor.diretor_ativo_do_curso(diretor.curso_fk, excluir_pk=diretor.pk)
    if outro:
        messages.error(
            request,
            f'Não é possível reativar {nome}: o curso {diretor.curso_fk.nome_curso} já tem um diretor ativo '
            f'({outro.nome_completo}). Inative o diretor atual ou mude o curso de {nome} antes.'
        )
        return redirect('dashboard:gerenciar_diretores')

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
    nome = ' '.join(request.POST.get('nome_curso', '').split())

    if not nome:
        messages.error(request, 'O nome do curso é obrigatório.')
        return redirect('dashboard:gerenciar_cursos')

    with transaction.atomic():
        # Trava a tabela de cursos durante a checagem: dois envios ao mesmo tempo
        # (clique duplo) não conseguem criar o mesmo curso duas vezes.
        list(Curso.objects.select_for_update().values_list('pk', flat=True))
        existente = Curso.objects.filter(nome_curso__iexact=nome).first()
        if existente:
            if existente.ativo:
                messages.error(request, 'Já existe um curso com esse nome.')
            else:
                messages.error(
                    request,
                    f'O curso "{existente.nome_curso}" já existe e está inativo. '
                    f'Use "Ver Inativos" e clique em Reativar.'
                )
            return redirect('dashboard:gerenciar_cursos')
        Curso.objects.create(nome_curso=nome)

    messages.success(request, f'Curso "{nome}" cadastrado com sucesso.')
    return redirect('dashboard:gerenciar_cursos')


@_admin_required
@require_POST
def editar_curso_admin(request, curso_id):
    """Atualiza o nome de um curso."""
    curso = get_object_or_404(Curso, pk=curso_id)
    nome = ' '.join(request.POST.get('nome_curso', '').split())

    if not nome:
        messages.error(request, 'O nome do curso é obrigatório.')
        return redirect('dashboard:gerenciar_cursos')

    if Curso.objects.filter(nome_curso__iexact=nome).exclude(pk=curso_id).exists():
        messages.error(request, 'Já existe outro curso com esse nome.')
        return redirect('dashboard:gerenciar_cursos')

    curso.nome_curso = nome
    curso.save()
    messages.success(request, f'Curso "{nome}" atualizado com sucesso.')
    return redirect('dashboard:gerenciar_cursos')


@_admin_required
@require_POST
def Inativar_curso_admin(request, curso_id):
    """Inativa um curso. Nada é apagado: diretor, disciplinas, alunos e portarias continuam no banco."""
    curso = get_object_or_404(Curso, pk=curso_id)
    curso.ativo = False
    curso.save(update_fields=['ativo'])
    messages.success(
        request,
        f'Curso "{curso.nome_curso}" inativado. Ele não aparece mais nos cadastros, '
        f'mas todos os dados foram mantidos.'
    )
    return redirect('dashboard:gerenciar_cursos')


@_admin_required
@require_POST
def reativar_curso_admin(request, curso_id):
    """Reativa um curso inativado."""
    curso = get_object_or_404(Curso, pk=curso_id)
    curso.ativo = True
    curso.save(update_fields=['ativo'])
    messages.success(request, f'Curso "{curso.nome_curso}" reativado com sucesso.')
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
    if not curso.ativo:
        messages.error(
            request,
            f'O curso {curso.nome_curso} está inativo. Reative o curso antes de cadastrar disciplinas.'
        )
        return redirect('dashboard:gerenciar_disciplinas')

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
        novo_curso = get_object_or_404(Curso, pk=curso_id)
        if not novo_curso.ativo and novo_curso.pk != disciplina.curso_fk_id:
            messages.error(request, f'O curso {novo_curso.nome_curso} está inativo.')
            return redirect('dashboard:gerenciar_disciplinas')
        disciplina.curso_fk = novo_curso

    disciplina.save()

    messages.success(request, f'Disciplina "{disciplina.nome_disciplina}" atualizada com sucesso.')
    return redirect('dashboard:gerenciar_disciplinas')


@_admin_required
@require_POST
def Inativar_disciplina(request, disciplina_codigo):
    """Remove uma disciplina (e todos os vínculos com professores através do CASCADE)."""
    disciplina = get_object_or_404(Disciplina, pk=disciplina_codigo)
    nome = disciplina.nome_disciplina
    disciplina.delete()  # CASCADE vai remover os vínculos em ProfessorDisciplina automaticamente
    messages.success(request, f'Disciplina "{nome}" excluída com sucesso.')
    return redirect('dashboard:gerenciar_disciplinas')
