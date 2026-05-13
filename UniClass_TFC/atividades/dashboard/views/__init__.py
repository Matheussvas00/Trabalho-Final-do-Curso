"""
Views do dashboard — pacote modular.

Cada tipo de usuário tem seu próprio módulo de views.
O roteamento principal fica em dashboard_view().
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .common import base_context
from .aluno import (
    home_aluno,
    minhas_portarias,
    atividades_disponiveis,
    visualizar_atividade,
    responder_atividade,
    minhas_respostas,
    visualizar_resposta,
    editar_resposta,
    excluir_resposta,
    minhas_disciplinas
)
from .professor import (
    home_professor,
    gerenciar_atividades,
    cadastrar_atividade,
    editar_atividade,
    excluir_atividade,
    validar_respostas,
    validar_resposta_professor,
    rejeitar_resposta_professor,
    criar_atividade,
    avaliar_resposta,
    portarias_professor,
    disciplinas_professor,
    api_disciplinas_portaria_professor,
)
from .administrador import (
    home_admin,
    gerenciar_diretores,
    cadastrar_diretor,
    editar_diretor,
    excluir_diretor,
    reativar_diretor,
    gerenciar_cursos,
    cadastrar_curso_admin,
    editar_curso_admin,
    excluir_curso_admin,
    gerenciar_disciplinas,
    cadastrar_disciplina,
    editar_disciplina,
    excluir_disciplina,
)
from .diretor import (
    home_diretor,
    gerenciar_alunos,
    cadastrar_aluno,
    editar_aluno,
    excluir_aluno,
    reativar_aluno,
    gerenciar_professores,
    cadastrar_professor,
    editar_professor,
    excluir_professor,
    reativar_professor,
    gerenciar_portarias,
    cadastrar_portaria,
    editar_portaria,
    excluir_portaria,
    api_disciplinas_aluno,
    gerenciar_validacoes,
    validar_resposta_diretor,
    gerenciar_alunos_diretor,
    gerenciar_professores_diretor,
)


@login_required(login_url='authentication:login')
def dashboard_view(request):
    """Roteador principal — direciona para a home correta por tipo de usuário."""
    user = request.user

    if user.tipo_usuario == 'aluno':
        return home_aluno(request)
    elif user.tipo_usuario == 'professor':
        return home_professor(request)
    elif user.tipo_usuario == 'diretor':
        return home_diretor(request)
    elif user.tipo_usuario == 'admin':
        return home_admin(request)

    # fallback
    return render(request, 'dashboard/index.html', base_context(request))


__all__ = [
    'dashboard_view',
    'gerenciar_alunos',
    'cadastrar_aluno',
    'editar_aluno',
    'excluir_aluno',
    'gerenciar_professores',
    'cadastrar_professor',
    'editar_professor',
    'excluir_professor',
    'cadastrar_disciplina',
    'editar_disciplina',
    'excluir_disciplina',
    'cadastrar_portaria',
    'editar_portaria',
    'excluir_portaria',
    'gerenciar_portarias',
    'api_disciplinas_aluno',
    'gerenciar_validacoes',
    'validar_resposta_diretor',
    'criar_atividade',
    'avaliar_resposta',
    'home_aluno',
    'home_professor',
    'home_diretor',
    'home_admin',
]
