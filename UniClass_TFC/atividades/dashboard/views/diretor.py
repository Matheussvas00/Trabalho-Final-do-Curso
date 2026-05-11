"""
Views do dashboard do Diretor — CRUD de professores, alunos, portarias e validação de atividades
Atualizado para trabalhar com o modelo Portaria
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError
from django.http import JsonResponse
from datetime import date
from atividades.models import (
    Aluno, Professor, Diretor, Atividade, Portaria, PortariaDisciplina,
    Disciplina, ProfessorDisciplina, AlunoDisciplina, RespostaAtividade, Usuario, Curso,
    Notificacao
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
        diretor = Diretor.objects.select_related('curso_fk').get(id_diretor=request.user)
        ctx['display_name'] = diretor.nome_completo
        ctx['diretor'] = diretor
        ctx['curso_diretor'] = diretor.curso_fk
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

    diretor = ctx.get('diretor')
    curso_diretor = diretor.curso_fk if diretor else None

    # Professores do curso do diretor
    if curso_diretor:
        ctx['professores'] = Professor.objects.filter(
            cursos=curso_diretor
        ).select_related('id_professor').order_by('nome_professor')

        ctx['alunos'] = Aluno.objects.filter(
            cursos=curso_diretor
        ).select_related('id_aluno').order_by('nome_aluno', 'sobrenome_aluno')

        ctx['disciplinas'] = Disciplina.objects.filter(
            curso_fk=curso_diretor
        ).order_by('nome_disciplina')
    else:
        ctx['professores'] = Professor.objects.none()
        ctx['alunos'] = Aluno.objects.none()
        ctx['disciplinas'] = Disciplina.objects.none()

    # Portarias do diretor
    ctx['portarias'] = Portaria.objects.filter(
        id_diretorfk=diretor
    ).select_related('id_alunofk', 'id_alunofk__id_aluno').order_by('-data_criacao')[:10] if diretor else []

    # Estatísticas do curso do diretor
    if curso_diretor:
        ctx['total_alunos'] = Aluno.objects.filter(cursos=curso_diretor).count()
        ctx['total_professores'] = Professor.objects.filter(cursos=curso_diretor).count()
        ctx['total_portarias'] = Portaria.objects.filter(id_diretorfk=diretor).count()
        ctx['portarias_ativas'] = Portaria.objects.filter(
            id_diretorfk=diretor
        ).exclude(status='concluida').count()
    else:
        ctx['total_alunos'] = 0
        ctx['total_professores'] = 0
        ctx['total_portarias'] = 0
        ctx['portarias_ativas'] = 0

    # Respostas aguardando validação do diretor (pré-aprovadas pelo professor)
    ctx['respostas_para_validar'] = RespostaAtividade.objects.filter(
        status_professor='aprovada',
        status_diretor='pendente'
    ).select_related(
        'id_atividade__codigo_disciplinafk',
        'id_atividade__id_professorfk',
        'id_atividade__id_portariafk',
        'id_alunofk',
    ).order_by('-data_envio')[:10]

    ctx['total_validar'] = RespostaAtividade.objects.filter(
        status_professor='aprovada',
        status_diretor='pendente'
    ).count()

    ctx['active_page'] = 'inicio'
    ctx['curso_diretor'] = curso_diretor
    return render(request, 'dashboard/home_diretor.html', ctx)


# ══════════════════════════════════════════════════════════════
#  CRUD — PROFESSORES
# ══════════════════════════════════════════════════════════════
@_diretor_required
def gerenciar_professores(request):
    """Lista todos os professores do curso do diretor com opções de CRUD."""
    ctx = _diretor_context(request)
    diretor = ctx.get('diretor')
    curso_diretor = diretor.curso_fk if diretor else None

    if curso_diretor:
        ctx['professores'] = Professor.objects.filter(
            cursos=curso_diretor
        ).prefetch_related(
            'cursos',
            'disciplinas_professor__codigo_disciplinafk'
        ).select_related('id_professor').order_by('nome_professor')
    else:
        ctx['professores'] = Professor.objects.none()

    ctx['cursos'] = Curso.objects.all().order_by('nome_curso')
    ctx['disciplinas'] = Disciplina.objects.filter(curso_fk=curso_diretor).order_by('nome_disciplina') if curso_diretor else []
    ctx['active_page'] = 'professores'
    return render(request, 'dashboard/gerenciar_professores.html', ctx)


@_diretor_required
@require_POST
def cadastrar_professor(request):
    """Cadastra um novo professor e o vincula ao curso do diretor."""
    nome      = request.POST.get('nome_professor', '').strip()
    sobrenome = request.POST.get('sobrenome_professor', '').strip()
    email     = request.POST.get('email', '').strip().lower()
    senha     = request.POST.get('senha', '').strip()
    disciplinas_ids = request.POST.getlist('disciplinas')

    if not all([nome, sobrenome, email, senha]):
        messages.error(request, 'Nome, sobrenome, e-mail e senha são obrigatórios.')
        return redirect('dashboard:gerenciar_professores')

    if not disciplinas_ids:
        messages.error(request, 'É obrigatório vincular pelo menos uma disciplina ao professor.')
        return redirect('dashboard:gerenciar_professores')

    if Usuario.objects.filter(email=email).exists():
        messages.error(request, 'Já existe um usuário com esse e-mail.')
        return redirect('dashboard:gerenciar_professores')

    if len(senha) < 8:
        messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
        return redirect('dashboard:gerenciar_professores')

    diretor = Diretor.objects.get(id_diretor=request.user)

    try:
        with transaction.atomic():
            # Cria usuário
            usuario = Usuario(email=email, tipo_usuario='professor')
            usuario.set_password(senha)
            usuario.save()

            # Cria professor vinculado
            professor = Professor.objects.create(
                id_professor=usuario,
                nome_professor=nome,
                sobrenome_professor=sobrenome,
                curso_professor=diretor.curso_fk.nome_curso,
            )

            # Vincula ao curso do diretor obrigatoriamente
            professor.cursos.add(diretor.curso_fk)

            # Vincula disciplinas selecionadas (devem ser do curso do diretor)
            if disciplinas_ids:
                disciplinas = Disciplina.objects.filter(
                    codigo_disciplina__in=disciplinas_ids,
                    curso_fk=diretor.curso_fk
                )
                for disciplina in disciplinas:
                    ProfessorDisciplina.objects.create(
                        id_professorfk=professor,
                        codigo_disciplinafk=disciplina
                    )
    except IntegrityError:
        messages.error(request, 'Já existe um usuário com esse e-mail.')
        return redirect('dashboard:gerenciar_professores')

    messages.success(request, f'Professor {nome} {sobrenome} cadastrado com sucesso.')
    return redirect('dashboard:gerenciar_professores')


@_diretor_required
@require_POST
def editar_professor(request, professor_id):
    """Atualiza os dados de um professor existente."""
    professor = get_object_or_404(Professor, pk=professor_id)
    diretor = Diretor.objects.get(id_diretor=request.user)

    professor.nome_professor      = request.POST.get('nome_professor', professor.nome_professor).strip()
    professor.sobrenome_professor = request.POST.get('sobrenome_professor', professor.sobrenome_professor).strip()

    usuario = professor.id_professor
    novo_email = request.POST.get('email', '').strip().lower()
    nova_senha = request.POST.get('nova_senha', '').strip()

    # Verifica se o novo e-mail já está em uso por outro usuário
    if novo_email and novo_email != usuario.email:
        if Usuario.objects.filter(email=novo_email).exclude(pk=usuario.pk).exists():
            messages.error(request, 'Esse e-mail já está em uso por outro usuário.')
            return redirect('dashboard:gerenciar_professores')
        usuario.email = novo_email

    if nova_senha:
        if len(nova_senha) < 8:
            messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
            return redirect('dashboard:gerenciar_professores')
        usuario.set_password(nova_senha)

    try:
        with transaction.atomic():
            usuario.save()
            professor.save()

            # Atualiza disciplinas vinculadas (apenas do curso do diretor)
            disciplinas_ids = request.POST.getlist('disciplinas')

            # Remove vínculos antigos do curso do diretor
            ProfessorDisciplina.objects.filter(
                id_professorfk=professor,
                codigo_disciplinafk__curso_fk=diretor.curso_fk
            ).delete()

            # Cria novos vínculos
            if disciplinas_ids:
                disciplinas = Disciplina.objects.filter(
                    codigo_disciplina__in=disciplinas_ids,
                    curso_fk=diretor.curso_fk
                )
                for disciplina in disciplinas:
                    ProfessorDisciplina.objects.get_or_create(
                        id_professorfk=professor,
                        codigo_disciplinafk=disciplina
                    )
    except IntegrityError:
        messages.error(request, 'Erro ao salvar: e-mail já em uso.')
        return redirect('dashboard:gerenciar_professores')

    messages.success(request, f'Professor {professor.nome_completo} atualizado com sucesso.')
    return redirect('dashboard:gerenciar_professores')


@_diretor_required
@require_POST
def excluir_professor(request, professor_id):
    """Remove um professor e seu usuário vinculado."""
    professor = get_object_or_404(Professor, pk=professor_id)
    nome = professor.nome_completo
    usuario = professor.id_professor

    with transaction.atomic():
        professor.delete()
        usuario.delete()

    messages.success(request, f'Professor {nome} excluído com sucesso.')
    return redirect('dashboard:gerenciar_professores')


# ══════════════════════════════════════════════════════════════
#  CRUD — ALUNOS
# ══════════════════════════════════════════════════════════════
@_diretor_required
def gerenciar_alunos(request):
    """Lista todos os alunos do curso do diretor com opções de CRUD."""
    ctx = _diretor_context(request)
    diretor = ctx.get('diretor')
    curso_diretor = diretor.curso_fk if diretor else None

    if curso_diretor:
        ctx['alunos'] = Aluno.objects.filter(
            cursos=curso_diretor
        ).prefetch_related(
            'cursos',
            'matriculas__codigo_disciplinafk'
        ).order_by('nome_aluno', 'sobrenome_aluno')
    else:
        ctx['alunos'] = Aluno.objects.none()

    ctx['disciplinas'] = Disciplina.objects.filter(curso_fk=curso_diretor).order_by('nome_disciplina') if curso_diretor else []
    ctx['active_page'] = 'alunos'
    return render(request, 'dashboard/gerenciar_alunos.html', ctx)


@_diretor_required
@require_POST
def cadastrar_aluno(request):
    """Cadastra um novo aluno e o vincula ao curso do diretor."""
    nome       = request.POST.get('nome_aluno', '').strip()
    sobrenome  = request.POST.get('sobrenome_aluno', '').strip()
    periodo    = request.POST.get('periodo', '').strip()
    matricula  = request.POST.get('matricula_aluno', '').strip()
    email      = request.POST.get('email', '').strip().lower()
    senha      = request.POST.get('senha', '').strip()
    disciplinas_ids = request.POST.getlist('disciplinas')

    if not all([nome, sobrenome, periodo, matricula, email, senha]):
        messages.error(request, 'Todos os campos são obrigatórios.')
        return redirect('dashboard:gerenciar_alunos')

    if not disciplinas_ids:
        messages.error(request, 'Selecione pelo menos uma disciplina para o aluno.')
        return redirect('dashboard:gerenciar_alunos')

    if Usuario.objects.filter(email=email).exists():
        messages.error(request, 'Já existe um usuário com esse e-mail.')
        return redirect('dashboard:gerenciar_alunos')

    if Aluno.objects.filter(matricula_aluno=matricula).exists():
        messages.error(request, 'Já existe um aluno com essa matrícula.')
        return redirect('dashboard:gerenciar_alunos')

    if len(senha) < 8:
        messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
        return redirect('dashboard:gerenciar_alunos')

    diretor = Diretor.objects.get(id_diretor=request.user)

    try:
        with transaction.atomic():
            # Cria usuário
            usuario = Usuario(email=email, tipo_usuario='aluno')
            usuario.set_password(senha)
            usuario.save()

            # Cria aluno vinculado ao usuário
            aluno = Aluno.objects.create(
                id_aluno=usuario,
                nome_aluno=nome,
                sobrenome_aluno=sobrenome,
                curso_aluno=diretor.curso_fk.nome_curso,
                periodo=periodo,
                matricula_aluno=matricula,
            )

            # Vincula ao curso do diretor obrigatoriamente
            aluno.cursos.add(diretor.curso_fk)

            # Vincula disciplinas selecionadas (devem ser do curso do diretor)
            if disciplinas_ids:
                disciplinas = Disciplina.objects.filter(
                    codigo_disciplina__in=disciplinas_ids,
                    curso_fk=diretor.curso_fk
                )
                for disciplina in disciplinas:
                    AlunoDisciplina.objects.create(
                        id_alunofk=aluno,
                        codigo_disciplinafk=disciplina
                    )
    except IntegrityError:
        messages.error(request, 'Já existe um usuário com esse e-mail ou matrícula.')
        return redirect('dashboard:gerenciar_alunos')

    messages.success(request, f'Aluno {nome} {sobrenome} cadastrado com sucesso.')
    return redirect('dashboard:gerenciar_alunos')


@_diretor_required
@require_POST
def editar_aluno(request, aluno_id):
    """Atualiza os dados de um aluno existente."""
    aluno = get_object_or_404(Aluno, pk=aluno_id)
    diretor = Diretor.objects.get(id_diretor=request.user)

    aluno.nome_aluno      = request.POST.get('nome_aluno', aluno.nome_aluno).strip()
    aluno.sobrenome_aluno = request.POST.get('sobrenome_aluno', aluno.sobrenome_aluno).strip()
    aluno.periodo         = request.POST.get('periodo', aluno.periodo).strip()

    nova_matricula = request.POST.get('matricula_aluno', aluno.matricula_aluno).strip()
    if nova_matricula != aluno.matricula_aluno:
        if Aluno.objects.filter(matricula_aluno=nova_matricula).exclude(pk=aluno_id).exists():
            messages.error(request, 'Já existe outro aluno com essa matrícula.')
            return redirect('dashboard:gerenciar_alunos')
        aluno.matricula_aluno = nova_matricula

    usuario = aluno.id_aluno
    novo_email = request.POST.get('email', '').strip().lower()
    nova_senha = request.POST.get('nova_senha', '').strip()

    if novo_email and novo_email != usuario.email:
        if Usuario.objects.filter(email=novo_email).exclude(pk=usuario.pk).exists():
            messages.error(request, 'Esse e-mail já está em uso por outro usuário.')
            return redirect('dashboard:gerenciar_alunos')
        usuario.email = novo_email

    if nova_senha:
        if len(nova_senha) < 8:
            messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
            return redirect('dashboard:gerenciar_alunos')
        usuario.set_password(nova_senha)

    try:
        with transaction.atomic():
            usuario.save()
            aluno.save()

            # Atualiza disciplinas vinculadas (apenas do curso do diretor)
            disciplinas_ids = request.POST.getlist('disciplinas')

            # Remove vínculos antigos do curso do diretor
            AlunoDisciplina.objects.filter(
                id_alunofk=aluno,
                codigo_disciplinafk__curso_fk=diretor.curso_fk
            ).delete()

            # Cria novos vínculos
            if disciplinas_ids:
                disciplinas = Disciplina.objects.filter(
                    codigo_disciplina__in=disciplinas_ids,
                    curso_fk=diretor.curso_fk
                )
                for disciplina in disciplinas:
                    AlunoDisciplina.objects.get_or_create(
                        id_alunofk=aluno,
                        codigo_disciplinafk=disciplina
                    )
    except IntegrityError:
        messages.error(request, 'Erro ao salvar: e-mail já em uso.')
        return redirect('dashboard:gerenciar_alunos')

    messages.success(request, f'Aluno {aluno.nome_completo} atualizado com sucesso.')
    return redirect('dashboard:gerenciar_alunos')


@_diretor_required
@require_POST
def excluir_aluno(request, aluno_id):
    """Remove um aluno e seu usuário vinculado."""
    aluno = get_object_or_404(Aluno, pk=aluno_id)
    nome = aluno.nome_completo
    usuario = aluno.id_aluno

    with transaction.atomic():
        aluno.delete()
        usuario.delete()

    messages.success(request, f'Aluno {nome} excluído com sucesso.')
    return redirect('dashboard:gerenciar_alunos')


# ══════════════════════════════════════════════════════════════
#  CRUD — PORTARIAS
# ══════════════════════════════════════════════════════════════
@_diretor_required
def gerenciar_portarias(request):
    """Lista todas as portarias criadas pelo diretor com opções de CRUD."""
    ctx = _diretor_context(request)
    diretor = ctx.get('diretor')

    if diretor:
        ctx['portarias'] = Portaria.objects.filter(
            id_diretorfk=diretor
        ).select_related(
            'id_alunofk__id_aluno'
        ).prefetch_related(
            'disciplinas_portaria__codigo_disciplinafk'
        ).order_by('-data_criacao')

        # Alunos matriculados no curso do diretor
        ctx['alunos'] = Aluno.objects.filter(
            cursos=diretor.curso_fk
        ).order_by('nome_aluno', 'sobrenome_aluno')

        # Disciplinas do curso do diretor
        ctx['disciplinas'] = Disciplina.objects.filter(
            curso_fk=diretor.curso_fk
        ).order_by('nome_disciplina')
    else:
        ctx['portarias'] = Portaria.objects.none()
        ctx['alunos'] = Aluno.objects.none()
        ctx['disciplinas'] = Disciplina.objects.none()

    ctx['active_page'] = 'portarias'
    return render(request, 'dashboard/gerenciar_portarias.html', ctx)


@_diretor_required
@require_POST
def cadastrar_portaria(request):
    """Diretor cadastra uma nova portaria para um aluno do seu curso."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def _erro(msg):
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg})
        messages.error(request, msg)
        return redirect('dashboard:gerenciar_portarias')

    aluno_id    = request.POST.get('id_alunofk', '').strip()
    numero      = request.POST.get('numero_portaria', '').strip()
    motivo      = request.POST.get('motivo_portaria', '').strip()
    prazo_criar = request.POST.get('prazo_professor_criar_atividades', '').strip()
    prazo_resp  = request.POST.get('prazo_aluno_responder', '').strip()
    prazo_valid = request.POST.get('prazo_validacao_final', '').strip()
    disciplinas_ids = request.POST.getlist('disciplinas')

    if not all([aluno_id, numero, motivo, prazo_criar, prazo_resp, prazo_valid]):
        return _erro('Todos os campos são obrigatórios.')

    if not disciplinas_ids:
        return _erro('Selecione pelo menos uma disciplina para a portaria.')

    if Portaria.objects.filter(numero_portaria=numero).exists():
        return _erro('Já existe uma portaria com esse número.')

    diretor = Diretor.objects.get(id_diretor=request.user)
    aluno = get_object_or_404(Aluno, pk=aluno_id)

    if not aluno.cursos.filter(id_curso=diretor.curso_fk.id_curso).exists():
        return _erro(f'Aluno não está matriculado no curso {diretor.curso_fk.nome_curso}.')

    # Valida ordenação das datas
    from datetime import datetime
    try:
        d_criar = datetime.strptime(prazo_criar, '%Y-%m-%d').date()
        d_resp  = datetime.strptime(prazo_resp,  '%Y-%m-%d').date()
        d_valid = datetime.strptime(prazo_valid, '%Y-%m-%d').date()
    except ValueError:
        return _erro('Datas inválidas. Use o formato correto.')

    if not (d_criar <= d_resp <= d_valid):
        return _erro(
            'As datas devem estar em ordem: '
            'Prazo Criar Atividades ≤ Prazo Respostas ≤ Prazo Validação Final.'
        )

    disciplinas = Disciplina.objects.filter(
        codigo_disciplina__in=disciplinas_ids,
        curso_fk=diretor.curso_fk
    )

    try:
        with transaction.atomic():
            portaria = Portaria(
                id_diretorfk=diretor,
                id_alunofk=aluno,
                numero_portaria=numero,
                motivo_portaria=motivo,
                prazo_professor_criar_atividades=d_criar,
                prazo_aluno_responder=d_resp,
                prazo_validacao_final=d_valid,
            )
            atestado = request.FILES.get('atestado')
            if atestado:
                portaria.atestado = atestado
            portaria.save()

            valido, erro = portaria.validar_disciplinas(disciplinas)
            if not valido:
                raise ValueError(erro)

            for disciplina in disciplinas:
                PortariaDisciplina.objects.create(
                    id_portariafk=portaria,
                    codigo_disciplinafk=disciplina
                )
    except ValueError as e:
        return _erro(f'Erro ao criar portaria: {str(e)}')

    # Notifica os professores das disciplinas vinculadas à portaria
    prof_relacoes = ProfessorDisciplina.objects.filter(
        codigo_disciplinafk__in=disciplinas
    ).select_related('id_professorfk__id_professor')
    professores_notificados = set()
    for pd in prof_relacoes:
        prof_usuario = pd.id_professorfk.id_professor  # Usuario do professor
        if prof_usuario.pk not in professores_notificados:
            professores_notificados.add(prof_usuario.pk)
            Notificacao.objects.create(
                id_usuariodestino=prof_usuario,
                titulo='Nova Portaria — Criar Atividades',
                mensagem=(
                    f'O diretor criou a portaria nº {portaria.numero_portaria} para o aluno '
                    f'{aluno.nome_completo} (matrícula {aluno.matricula_aluno}). '
                    f'Você precisa criar as atividades até {d_criar.strftime("%d/%m/%Y")}.'
                )
            )

    sucesso_msg = f'Portaria {numero} criada com sucesso para {aluno.nome_completo}.'
    if is_ajax:
        return JsonResponse({'success': True, 'message': sucesso_msg})
    messages.success(request, sucesso_msg)
    return redirect('dashboard:gerenciar_portarias')


@_diretor_required
@require_POST
def editar_portaria(request, portaria_id):
    """Diretor edita uma portaria existente."""
    portaria = get_object_or_404(Portaria, pk=portaria_id)
    diretor = Diretor.objects.get(id_diretor=request.user)

    # Apenas o diretor que criou pode editar
    if portaria.id_diretorfk != diretor:
        messages.error(request, 'Você não tem permissão para editar esta portaria.')
        return redirect('dashboard:gerenciar_portarias')

    portaria.motivo_portaria = request.POST.get('motivo_portaria', portaria.motivo_portaria).strip()
    portaria.prazo_professor_criar_atividades = request.POST.get(
        'prazo_professor_criar_atividades',
        portaria.prazo_professor_criar_atividades
    )
    portaria.prazo_aluno_responder = request.POST.get(
        'prazo_aluno_responder',
        portaria.prazo_aluno_responder
    )
    portaria.prazo_validacao_final = request.POST.get(
        'prazo_validacao_final',
        portaria.prazo_validacao_final
    )
    portaria.observacoes = request.POST.get('observacoes', portaria.observacoes or '').strip() or None

    status = request.POST.get('status', '').strip()
    if status and status in dict(Portaria.STATUS_CHOICES):
        portaria.status = status

    # Atestado (arquivo) — opcional na edição
    atestado = request.FILES.get('atestado')
    if atestado:
        portaria.atestado = atestado

    with transaction.atomic():
        try:
            portaria.save()

            # Atualiza disciplinas se fornecidas
            disciplinas_ids = request.POST.getlist('disciplinas')
            if disciplinas_ids:
                disciplinas = Disciplina.objects.filter(
                    codigo_disciplina__in=disciplinas_ids,
                    curso_fk=diretor.curso_fk
                )

                # Valida disciplinas
                valido, erro = portaria.validar_disciplinas(disciplinas)
                if not valido:
                    raise ValueError(erro)

                # Remove vínculos antigos
                PortariaDisciplina.objects.filter(id_portariafk=portaria).delete()

                # Cria novos vínculos
                for disciplina in disciplinas:
                    PortariaDisciplina.objects.create(
                        id_portariafk=portaria,
                        codigo_disciplinafk=disciplina
                    )

            messages.success(request, f'Portaria {portaria.numero_portaria} atualizada com sucesso.')

        except ValueError as e:
            messages.error(request, f'Erro ao atualizar portaria: {str(e)}')

    return redirect('dashboard:gerenciar_portarias')


@_diretor_required
@require_POST
def excluir_portaria(request, portaria_id):
    """Diretor exclui uma portaria."""
    portaria = get_object_or_404(Portaria, pk=portaria_id)
    diretor = Diretor.objects.get(id_diretor=request.user)

    # Apenas o diretor que criou pode excluir
    if portaria.id_diretorfk != diretor:
        messages.error(request, 'Você não tem permissão para excluir esta portaria.')
        return redirect('dashboard:gerenciar_portarias')

    numero = portaria.numero_portaria
    portaria.delete()  # CASCADE vai deletar PortariaDisciplina e Atividades associadas
    messages.success(request, f'Portaria {numero} excluída com sucesso.')
    return redirect('dashboard:gerenciar_portarias')


@_diretor_required
def api_disciplinas_aluno(request, aluno_id):
    """Retorna as disciplinas de um aluno em JSON (para seleção dinâmica em modal)."""
    from django.http import JsonResponse
    diretor = Diretor.objects.select_related('curso_fk').get(id_diretor=request.user)
    aluno = get_object_or_404(Aluno, pk=aluno_id)

    # Disciplinas matriculadas do aluno que pertencem ao curso do diretor
    matriculas = AlunoDisciplina.objects.filter(
        id_alunofk=aluno,
        codigo_disciplinafk__curso_fk=diretor.curso_fk
    ).select_related('codigo_disciplinafk')

    disciplinas = [
        {
            'codigo_disciplina': m.codigo_disciplinafk.codigo_disciplina,
            'nome_disciplina': m.codigo_disciplinafk.nome_disciplina,
        }
        for m in matriculas
    ]
    return JsonResponse({'disciplinas': disciplinas})


# ══════════════════════════════════════════════════════════════
#  VALIDAÇÃO FINAL — DIRETOR
# ══════════════════════════════════════════════════════════════
@_diretor_required
def gerenciar_validacoes(request):
    """Página dedicada à validação de respostas pré-aprovadas pelo professor."""
    ctx = _diretor_context(request)
    diretor = ctx.get('diretor')

    # Respostas de atividades das portarias criadas por este diretor
    if diretor:
        ctx['respostas_para_validar'] = RespostaAtividade.objects.filter(
            status_professor='aprovada',
            status_diretor='pendente',
            id_atividade__id_portariafk__id_diretorfk=diretor
        ).select_related(
            'id_atividade__codigo_disciplinafk',
            'id_atividade__id_professorfk__id_professor',
            'id_atividade__id_portariafk',
            'id_alunofk__id_aluno',
        ).order_by('-data_envio')
    else:
        ctx['respostas_para_validar'] = RespostaAtividade.objects.none()

    ctx['total_validar'] = ctx['respostas_para_validar'].count()
    ctx['active_page'] = 'validacoes'
    return render(request, 'dashboard/gerenciar_validacoes.html', ctx)


@_diretor_required
@require_POST
def validar_resposta_diretor(request, resposta_id):
    """Diretor valida uma resposta já pré-aprovada pelo professor."""
    resposta = get_object_or_404(
        RespostaAtividade,
        pk=resposta_id,
        status_professor='aprovada',
        status_diretor='pendente'
    )

    diretor = Diretor.objects.get(id_diretor=request.user)

    # Verifica se a portaria pertence a este diretor
    if resposta.id_atividade.id_portariafk.id_diretorfk != diretor:
        messages.error(request, 'Você não tem permissão para validar esta resposta.')
        return redirect('dashboard:gerenciar_validacoes')

    acao = request.POST.get('acao', '').strip()
    observacao = request.POST.get('observacao_diretor', '').strip()

    if acao not in ['aprovar', 'rejeitar']:
        messages.error(request, 'Ação inválida.')
        return redirect('dashboard:gerenciar_validacoes')

    try:
        if acao == 'aprovar':
            resposta.validar_diretor(aprovada=True, observacao=observacao)
            messages.success(request, 'Resposta validada com sucesso pelo diretor.')
        else:
            resposta.validar_diretor(aprovada=False, observacao=observacao)
            messages.warning(request, 'Resposta rejeitada pelo diretor.')
    except ValueError as e:
        messages.error(request, f'Erro ao validar: {str(e)}')

    return redirect('dashboard:gerenciar_validacoes')


# ══════════════════════════════════════════════════════════════
#  PÁGINAS DEDICADAS DE CRUD — ALUNOS E PROFESSORES
# ══════════════════════════════════════════════════════════════
@_diretor_required
def gerenciar_alunos_diretor(request):
    """Página dedicada ao gerenciamento de alunos do curso do diretor."""
    ctx = _diretor_context(request)
    diretor = ctx.get('diretor')
    curso_diretor = diretor.curso_fk if diretor else None

    if curso_diretor:
        ctx['alunos'] = Aluno.objects.filter(
            cursos=curso_diretor
        ).select_related('id_aluno').order_by('nome_aluno', 'sobrenome_aluno')
        ctx['total_alunos'] = ctx['alunos'].count()
    else:
        ctx['alunos'] = Aluno.objects.none()
        ctx['total_alunos'] = 0

    ctx['active_page'] = 'alunos'
    ctx['curso_diretor'] = curso_diretor
    return render(request, 'dashboard/gerenciar_alunos.html', ctx)


@_diretor_required
def gerenciar_professores_diretor(request):
    """Página dedicada ao gerenciamento de professores do curso do diretor."""
    ctx = _diretor_context(request)
    diretor = ctx.get('diretor')
    curso_diretor = diretor.curso_fk if diretor else None

    if curso_diretor:
        ctx['professores'] = Professor.objects.filter(
            cursos=curso_diretor
        ).select_related('id_professor').order_by('nome_professor')
        ctx['total_professores'] = ctx['professores'].count()

        # Disciplinas do curso para seleção
        ctx['disciplinas'] = Disciplina.objects.filter(
            curso_fk=curso_diretor
        ).order_by('nome_disciplina')
    else:
        ctx['professores'] = Professor.objects.none()
        ctx['total_professores'] = 0
        ctx['disciplinas'] = Disciplina.objects.none()

    ctx['active_page'] = 'professores'
    ctx['curso_diretor'] = curso_diretor
    return render(request, 'dashboard/gerenciar_professores.html', ctx)
