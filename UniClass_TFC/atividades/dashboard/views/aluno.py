"""
Views do dashboard do Aluno — Responder atividades e acompanhar validações
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from atividades.models import (
    Aluno, Atividade, Portaria, RespostaAtividade, Disciplina, Notificacao, Historico,
    AlunoDisciplina
)
from .common import base_context


# ── helpers ────────────────────────────────────────────────────
def _aluno_required(view_func):
    """Decorator: exige que o usuário logado seja aluno."""
    from functools import wraps

    @wraps(view_func)
    @login_required(login_url='authentication:login')
    def wrapper(request, *args, **kwargs):
        if request.user.tipo_usuario != 'aluno':
            messages.error(request, 'Acesso negado.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def _aluno_context(request):
    """Contexto base + dados do aluno."""
    ctx = base_context(request)
    try:
        aluno = Aluno.objects.prefetch_related('cursos', 'matriculas').get(id_aluno=request.user)
        ctx['display_name'] = aluno.nome_completo
        ctx['aluno'] = aluno
    except Aluno.DoesNotExist:
        pass
    return ctx


# ══════════════════════════════════════════════════════════════
#  HOME ALUNO
# ══════════════════════════════════════════════════════════════
@_aluno_required
def home_aluno(request):
    """Dashboard principal do aluno."""
    ctx = _aluno_context(request)
    aluno = ctx.get('aluno')

    if aluno:
        # Portarias ativas do aluno
        portarias_ativas = Portaria.objects.filter(
            id_alunofk=aluno
        ).exclude(
            status='concluida'
        ).select_related(
            'id_diretorfk__id_diretor'
        ).prefetch_related(
            'disciplinas_portaria__codigo_disciplinafk',
            'atividades'
        ).order_by('-data_criacao')

        ctx['portarias_ativas'] = portarias_ativas
        ctx['total_portarias'] = portarias_ativas.count()

        # Atividades disponíveis para responder (inclui reprovadas para reenvio)
        atividades_disponiveis = Atividade.objects.filter(
            id_portariafk__id_alunofk=aluno,
            status__in=['aguardando_resposta', 'reprovada_professor', 'reprovada_diretor']
        ).exclude(
            # Exclui atividades que o aluno já respondeu e não foram reprovadas
            respostas__id_alunofk=aluno,
            respostas__status__in=['pendente', 'aprovada_prof', 'aprovada_dir']
        ).select_related(
            'codigo_disciplinafk',
            'id_professorfk__id_professor',
            'id_portariafk'
        ).order_by('data_limite_resposta')

        ctx['atividades_disponiveis'] = atividades_disponiveis
        ctx['total_atividades_pendentes'] = atividades_disponiveis.count()

        # Respostas enviadas
        ctx['minhas_respostas'] = RespostaAtividade.objects.filter(
            id_alunofk=aluno
        ).select_related(
            'id_atividade__codigo_disciplinafk',
            'id_atividade__id_professorfk__id_professor',
            'id_atividade__id_portariafk'
        ).order_by('-data_envio')[:10]

        ctx['total_respostas'] = RespostaAtividade.objects.filter(id_alunofk=aluno).count()

        # Respostas aguardando validação
        ctx['aguardando_validacao'] = RespostaAtividade.objects.filter(
            id_alunofk=aluno,
            status__in=['pendente', 'aprovada_prof']
        ).count()

        # Respostas aprovadas finalmente
        ctx['aprovadas'] = RespostaAtividade.objects.filter(
            id_alunofk=aluno,
            status='aprovada_dir'
        ).count()

        # Respostas rejeitadas
        ctx['rejeitadas'] = RespostaAtividade.objects.filter(
            id_alunofk=aluno,
            status__in=['rejeitada_prof', 'rejeitada_dir']
        ).count()
    else:
        ctx['portarias_ativas'] = []
        ctx['total_portarias'] = 0
        ctx['atividades_disponiveis'] = []
        ctx['total_atividades_pendentes'] = 0
        ctx['minhas_respostas'] = []
        ctx['total_respostas'] = 0
        ctx['aguardando_validacao'] = 0
        ctx['aprovadas'] = 0
        ctx['rejeitadas'] = 0

    ctx['active_page'] = 'inicio'
    return render(request, 'dashboard/home_aluno.html', ctx)


# ══════════════════════════════════════════════════════════════
#  MINHAS PORTARIAS
# ══════════════════════════════════════════════════════════════
@_aluno_required
def minhas_portarias(request):
    """Lista todas as portarias do aluno."""
    ctx = _aluno_context(request)
    aluno = ctx.get('aluno')

    if aluno:
        ctx['portarias'] = Portaria.objects.filter(
            id_alunofk=aluno
        ).select_related(
            'id_diretorfk__id_diretor',
            'id_diretorfk__curso_fk'
        ).prefetch_related(
            'disciplinas_portaria__codigo_disciplinafk',
            'atividades__id_professorfk',
            'atividades__respostas'
        ).order_by('-data_criacao')
    else:
        ctx['portarias'] = []

    ctx['active_page'] = 'portarias'
    return render(request, 'dashboard/aluno_portarias.html', ctx)


# ══════════════════════════════════════════════════════════════
#  ATIVIDADES DISPONÍVEIS
# ══════════════════════════════════════════════════════════════
@_aluno_required
def atividades_disponiveis(request):
    """Lista atividades disponíveis para o aluno responder."""
    ctx = _aluno_context(request)
    aluno = ctx.get('aluno')

    if aluno:
        # Atividades que o aluno pode responder (novas ou reprovadas)
        ctx['atividades'] = Atividade.objects.filter(
            id_portariafk__id_alunofk=aluno,
            status__in=['aguardando_resposta', 'reprovada_professor', 'reprovada_diretor']
        ).exclude(
            respostas__id_alunofk=aluno,
            respostas__status__in=['pendente', 'aprovada_prof', 'aprovada_dir']
        ).select_related(
            'codigo_disciplinafk',
            'id_professorfk__id_professor',
            'id_portariafk'
        ).order_by('data_limite_resposta')
    else:
        ctx['atividades'] = []

    ctx['active_page'] = 'atividades'
    return render(request, 'dashboard/aluno_atividades.html', ctx)


# ══════════════════════════════════════════════════════════════
#  RESPONDER ATIVIDADE
# ══════════════════════════════════════════════════════════════
@_aluno_required
def visualizar_atividade(request, atividade_id):
    """Visualiza detalhes de uma atividade e permite responder."""
    ctx = _aluno_context(request)
    aluno = ctx.get('aluno')

    atividade = get_object_or_404(
        Atividade.objects.select_related(
            'codigo_disciplinafk',
            'id_professorfk__id_professor',
            'id_portariafk__id_alunofk'
        ),
        pk=atividade_id
    )

    # Verifica se a atividade é da portaria do aluno
    if atividade.id_portariafk.id_alunofk != aluno:
        messages.error(request, 'Você não tem acesso a esta atividade.')
        return redirect('dashboard:atividades_disponiveis')

    # Verifica se já respondeu
    resposta_existente = RespostaAtividade.objects.filter(
        id_atividade=atividade,
        id_alunofk=aluno
    ).first()

    ctx['atividade'] = atividade
    ctx['resposta_existente'] = resposta_existente
    ctx['active_page'] = 'atividades'

    return render(request, 'dashboard/aluno_visualizar_atividade.html', ctx)


@_aluno_required
@require_POST
def responder_atividade(request, atividade_id):
    """Aluno envia resposta para uma atividade."""
    aluno = Aluno.objects.get(id_aluno=request.user)
    atividade = get_object_or_404(Atividade, pk=atividade_id)

    # Verifica se a atividade é da portaria do aluno
    if atividade.id_portariafk.id_alunofk != aluno:
        messages.error(request, 'Você não tem acesso a esta atividade.')
        return redirect('dashboard:atividades_disponiveis')

    # Verifica se já respondeu (e a resposta não foi reprovada para reenvio)
    resposta_existente = RespostaAtividade.objects.filter(
        id_atividade=atividade, id_alunofk=aluno
    ).first()
    if resposta_existente and resposta_existente.status not in ['rejeitada_prof', 'rejeitada_dir']:
        messages.error(request, 'Você já respondeu esta atividade.')
        return redirect('dashboard:minhas_respostas')

    arquivo_upload = request.FILES.get('arquivo')
    descricao = request.POST.get('descricao_resposta', '').strip()

    if not arquivo_upload and not descricao:
        messages.error(request, 'Envie um arquivo ou descrição da resposta.')
        return redirect('dashboard:visualizar_atividade', atividade_id=atividade_id)

    arquivo_path = None
    if arquivo_upload:
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        arquivo_path = default_storage.save(
            f'respostas/{arquivo_upload.name}',
            ContentFile(arquivo_upload.read())
        )

    try:
        with transaction.atomic():
            is_reenvio = bool(resposta_existente)
            if resposta_existente:
                # Reenvio após reprovação: atualiza a resposta existente
                if arquivo_path:
                    resposta_existente.arquivo = arquivo_path
                if descricao:
                    resposta_existente.descricao_resposta = descricao
                resposta_existente.data_envio = timezone.now()
                resposta_existente.status = 'pendente'
                resposta_existente.status_professor = 'pendente'
                resposta_existente.status_diretor = 'pendente'
                resposta_existente.observacao_professor = None
                resposta_existente.observacao_diretor = None
                resposta_existente.data_validacao_professor = None
                resposta_existente.data_validacao_diretor = None
                resposta_existente.save()
            else:
                resposta_existente = RespostaAtividade(
                    id_atividade=atividade,
                    id_alunofk=aluno,
                    arquivo=arquivo_path,
                    descricao_resposta=descricao or None
                )
                resposta_existente.save()  # Validações do modelo serão executadas
            # Marca a atividade como respondida
            atividade.status = 'respondida'
            atividade.save(update_fields=['status'])
            # Avança portaria para em_andamento se estava aguardando atividades
            portaria = atividade.id_portariafk
            if portaria.status == 'aguardando_atividades':
                portaria.status = 'em_andamento'
                portaria.save(update_fields=['status'])
            # Notifica o professor da atividade
            prof_usuario = atividade.id_professorfk.id_professor
            if is_reenvio:
                notif_titulo = 'Atividade Refeita — Aguardando Nova Avaliação'
                notif_msg = (
                    f'O aluno {aluno.nome_completo} refez a atividade '
                    f'"{atividade.titulo}" (Portaria nº {portaria.numero_portaria}) '
                    f'após sua rejeição. Acesse o painel para reavaliar.'
                )
            else:
                notif_titulo = 'Nova Resposta Aguardando Avaliação'
                notif_msg = (
                    f'O aluno {aluno.nome_completo} enviou uma resposta para a atividade '
                    f'"{atividade.titulo}" (Portaria nº {portaria.numero_portaria}). '
                    f'Acesse o painel para avaliar.'
                )
            Notificacao.objects.create(
                id_usuariodestino=prof_usuario,
                titulo=notif_titulo,
                mensagem=notif_msg,
            )
            # Registra no histórico
            acao_historico = 'resposta_reenviada' if is_reenvio else 'resposta_enviada'
            Historico.objects.create(
                id_usuario=request.user,
                acao=acao_historico,
                descricao=f'Resposta {"reenviada" if is_reenvio else "enviada"} para a atividade "{atividade.titulo}" (Portaria nº {portaria.numero_portaria}).'
            )

        msg_sucesso = (
            f'Atividade refeita com sucesso! Aguarde a nova avaliação do professor {atividade.id_professorfk.nome_completo}.'
            if is_reenvio else
            f'Resposta enviada com sucesso! Aguarde a validação do professor {atividade.id_professorfk.nome_completo}.'
        )
        messages.success(request, msg_sucesso)
    except ValueError as e:
        messages.error(request, f'Erro ao enviar resposta: {str(e)}')
        return redirect('dashboard:visualizar_atividade', atividade_id=atividade_id)

    return redirect('dashboard:minhas_respostas')


# ══════════════════════════════════════════════════════════════
#  REFAZER ATIVIDADE REJEITADA PELO PROFESSOR
# ══════════════════════════════════════════════════════════════
@_aluno_required
def refazer_atividade(request, atividade_id):
    """Aluno refaz uma atividade que foi rejeitada pelo professor."""
    aluno = Aluno.objects.get(id_aluno=request.user)
    atividade = get_object_or_404(
        Atividade.objects.select_related(
            'codigo_disciplinafk',
            'id_professorfk__id_professor',
            'id_portariafk__id_alunofk',
            'id_portariafk__id_diretorfk',
        ),
        pk=atividade_id
    )

    if atividade.id_portariafk.id_alunofk != aluno:
        messages.error(request, 'Você não tem acesso a esta atividade.')
        return redirect('dashboard:minhas_respostas')

    # Busca a resposta rejeitada (deve existir e estar rejeitada pelo professor)
    resposta = RespostaAtividade.objects.filter(
        id_atividade=atividade,
        id_alunofk=aluno,
        status='rejeitada_prof',
    ).first()

    if not resposta:
        messages.error(request, 'Não há resposta rejeitada para refazer nesta atividade.')
        return redirect('dashboard:minhas_respostas')

    if atividade.prazo_vencido:
        messages.error(request, 'O prazo para refazer esta atividade encerrou.')
        return redirect('dashboard:minhas_respostas')

    ctx = _aluno_context(request)
    ctx['atividade'] = atividade
    ctx['resposta'] = resposta
    ctx['active_page'] = 'atividades'

    if request.method == 'GET':
        return render(request, 'dashboard/aluno_refazer_atividade.html', ctx)

    # ── POST: processa o reenvio ──────────────────────────────
    arquivo_upload = request.FILES.get('arquivo')
    descricao = request.POST.get('descricao_resposta', '').strip()

    # Pelo menos um conteúdo é obrigatório (novo ou preexistente)
    if not arquivo_upload and not descricao and not resposta.arquivo:
        messages.error(request, 'Envie um arquivo ou escreva uma descrição para a resposta.')
        return render(request, 'dashboard/aluno_refazer_atividade.html', ctx)

    try:
        with transaction.atomic():
            if arquivo_upload:
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                arquivo_path = default_storage.save(
                    f'respostas/{arquivo_upload.name}',
                    ContentFile(arquivo_upload.read())
                )
                resposta.arquivo = arquivo_path

            if descricao:
                resposta.descricao_resposta = descricao

            # Reseta todos os campos de validação para nova avaliação
            resposta.data_envio = timezone.now()
            resposta.status = 'pendente'
            resposta.status_professor = 'pendente'
            resposta.status_diretor = 'pendente'
            resposta.observacao_professor = None
            resposta.observacao_diretor = None
            resposta.data_validacao_professor = None
            resposta.data_validacao_diretor = None
            resposta.save()

            # Atualiza status da atividade sem disparar as validações do save()
            Atividade.objects.filter(pk=atividade.pk).update(status='respondida')

            portaria = atividade.id_portariafk

            # Notifica o professor
            Notificacao.objects.create(
                id_usuariodestino=atividade.id_professorfk.id_professor,
                titulo='Atividade Refeita — Aguardando Nova Avaliação',
                mensagem=(
                    f'O aluno {aluno.nome_completo} refez a atividade '
                    f'"{atividade.titulo}" (Portaria nº {portaria.numero_portaria}) '
                    f'após a rejeição. Acesse o painel para reavaliar.'
                )
            )

            Historico.objects.create(
                id_usuario=request.user,
                acao='resposta_reenviada',
                descricao=(
                    f'Atividade "{atividade.titulo}" refeita e enviada para nova avaliação '
                    f'(Portaria nº {portaria.numero_portaria}).'
                )
            )

        messages.success(
            request,
            f'Atividade refeita e enviada com sucesso! '
            f'Aguarde a nova avaliação do professor {atividade.id_professorfk.nome_completo}.'
        )
    except Exception as e:
        messages.error(request, f'Erro ao enviar resposta: {str(e)}')
        return render(request, 'dashboard/aluno_refazer_atividade.html', ctx)

    return redirect('dashboard:minhas_respostas')



@_aluno_required
def minhas_respostas(request):
    """Lista todas as respostas enviadas pelo aluno."""
    ctx = _aluno_context(request)
    aluno = ctx.get('aluno')

    if aluno:
        ctx['respostas'] = RespostaAtividade.objects.filter(
            id_alunofk=aluno
        ).select_related(
            'id_atividade__codigo_disciplinafk',
            'id_atividade__id_professorfk__id_professor',
            'id_atividade__id_portariafk'
        ).order_by('-data_envio')

        # Estatísticas
        ctx['total_respostas'] = ctx['respostas'].count()
        ctx['pendentes'] = ctx['respostas'].filter(status_professor='pendente').count()
        ctx['aprovadas_professor'] = ctx['respostas'].filter(status_professor='aprovada', status_diretor='pendente').count()
        ctx['aprovadas_final'] = ctx['respostas'].filter(status='aprovada_dir').count()
        ctx['rejeitadas'] = ctx['respostas'].filter(
            status__in=['rejeitada_prof', 'rejeitada_dir']
        ).count()
    else:
        ctx['respostas'] = []
        ctx['total_respostas'] = 0
        ctx['pendentes'] = 0
        ctx['aprovadas_professor'] = 0
        ctx['aprovadas_final'] = 0
        ctx['rejeitadas'] = 0

    ctx['active_page'] = 'respostas'
    return render(request, 'dashboard/aluno_respostas.html', ctx)


@_aluno_required
def visualizar_resposta(request, resposta_id):
    """Visualiza detalhes de uma resposta enviada, incluindo feedbacks."""
    ctx = _aluno_context(request)
    aluno = ctx.get('aluno')

    resposta = get_object_or_404(
        RespostaAtividade.objects.select_related(
            'id_atividade__codigo_disciplinafk',
            'id_atividade__id_professorfk__id_professor',
            'id_atividade__id_portariafk__id_diretorfk__id_diretor'
        ),
        pk=resposta_id,
        id_alunofk=aluno
    )

    ctx['resposta'] = resposta
    ctx['active_page'] = 'respostas'
    return render(request, 'dashboard/aluno_visualizar_resposta.html', ctx)


@_aluno_required
def editar_resposta(request, resposta_id):
    """Aluno edita uma resposta (apenas se não foi validada)."""
    aluno = Aluno.objects.get(id_aluno=request.user)
    resposta = get_object_or_404(RespostaAtividade, pk=resposta_id, id_alunofk=aluno)

    # Só pode editar se não foi validada ainda
    if resposta.status_professor != 'pendente':
        messages.error(request, 'Não é possível editar resposta que já foi validada.')
        return redirect('dashboard:minhas_respostas')

    if request.method == 'GET':
        ctx = _aluno_context(request)
        ctx['resposta'] = resposta
        ctx['active_page'] = 'respostas'
        return render(request, 'dashboard/editar_resposta.html', ctx)

    arquivo_upload = request.FILES.get('arquivo')
    descricao = request.POST.get('descricao_resposta', '').strip()

    if not arquivo_upload and not descricao and not resposta.arquivo:
        messages.error(request, 'Envie um arquivo ou descrição da resposta.')
        return redirect('dashboard:editar_resposta', resposta_id=resposta_id)

    if arquivo_upload:
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        arquivo_path = default_storage.save(
            f'respostas/{arquivo_upload.name}',
            ContentFile(arquivo_upload.read())
        )
        resposta.arquivo = arquivo_path

    if descricao:
        resposta.descricao_resposta = descricao
    resposta.data_envio = timezone.now()
    resposta.save()

    messages.success(request, 'Resposta atualizada com sucesso!')
    return redirect('dashboard:minhas_respostas')


@_aluno_required
@require_POST
def Inativar_resposta(request, resposta_id):
    """Aluno exclui uma resposta (apenas se não foi validada)."""
    aluno = Aluno.objects.get(id_aluno=request.user)
    resposta = get_object_or_404(RespostaAtividade, pk=resposta_id, id_alunofk=aluno)

    # Só pode Inativar se não foi validada ainda
    if resposta.status_professor != 'pendente':
        messages.error(request, 'Não é possível Inativar resposta que já foi validada.')
        return redirect('dashboard:minhas_respostas')

    atividade_titulo = resposta.id_atividade.titulo
    resposta.delete()

    messages.success(request, f'Resposta da atividade "{atividade_titulo}" excluída com sucesso.')
    return redirect('dashboard:minhas_respostas')


# ══════════════════════════════════════════════════════════════
#  DISCIPLINAS MATRICULADAS
# ══════════════════════════════════════════════════════════════
@_aluno_required
def minhas_disciplinas(request):
    """Lista disciplinas em que o aluno está matriculado."""
    ctx = _aluno_context(request)
    aluno = ctx.get('aluno')

    if aluno:
        ctx['matriculas'] = AlunoDisciplina.objects.filter(
            id_alunofk=aluno
        ).select_related(
            'codigo_disciplinafk__curso_fk'
        ).prefetch_related(
            'codigo_disciplinafk__professores_disciplina__id_professorfk'
        ).order_by('codigo_disciplinafk__nome_disciplina')
    else:
        ctx['matriculas'] = []

    ctx['active_page'] = 'disciplinas'
    return render(request, 'dashboard/aluno_disciplinas.html', ctx)
