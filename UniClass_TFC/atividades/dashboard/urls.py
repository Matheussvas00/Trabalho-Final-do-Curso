"""
URLs do módulo dashboard
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Home (roteador principal)
    path('', views.dashboard_view, name='index'),

    # Diretor — Páginas dedicadas de CRUD
    path('diretor/alunos/', views.gerenciar_alunos_diretor, name='gerenciar_alunos_diretor'),
    path('diretor/professores/', views.gerenciar_professores_diretor, name='gerenciar_professores_diretor'),

    # Diretor — CRUD Alunos
    path('gerenciar/alunos/', views.gerenciar_alunos, name='gerenciar_alunos'),
    path('gerenciar/alunos/cadastrar/', views.cadastrar_aluno, name='cadastrar_aluno'),
    path('gerenciar/alunos/<int:aluno_id>/editar/', views.editar_aluno, name='editar_aluno'),
    path('gerenciar/alunos/<int:aluno_id>/excluir/', views.excluir_aluno, name='excluir_aluno'),

    # Diretor — CRUD Professores
    path('gerenciar/professores/', views.gerenciar_professores, name='gerenciar_professores'),
    path('gerenciar/professores/cadastrar/', views.cadastrar_professor, name='cadastrar_professor'),
    path('gerenciar/professores/<int:professor_id>/editar/', views.editar_professor, name='editar_professor'),
    path('gerenciar/professores/<int:professor_id>/excluir/', views.excluir_professor, name='excluir_professor'),

    # Diretor — CRUD Portarias
    path('gerenciar/portarias/', views.gerenciar_portarias, name='gerenciar_portarias'),
    path('gerenciar/portarias/cadastrar/', views.cadastrar_portaria, name='cadastrar_portaria'),
    path('gerenciar/portarias/<int:portaria_id>/editar/', views.editar_portaria, name='editar_portaria'),
    path('gerenciar/portarias/<int:portaria_id>/excluir/', views.excluir_portaria, name='excluir_portaria'),

    # Diretor — API
    path('api/aluno/<int:aluno_id>/disciplinas/', views.api_disciplinas_aluno, name='api_disciplinas_aluno'),

    # Diretor — Validação final
    path('gerenciar/validacoes/', views.gerenciar_validacoes, name='gerenciar_validacoes'),
    path('gerenciar/validar/<int:resposta_id>/', views.validar_resposta_diretor, name='validar_resposta_diretor'),

    # Admin — CRUD Diretores
    path('admin/diretores/', views.gerenciar_diretores, name='gerenciar_diretores'),
    path('admin/diretores/cadastrar/', views.cadastrar_diretor, name='cadastrar_diretor'),
    path('admin/diretores/<int:diretor_id>/editar/', views.editar_diretor, name='editar_diretor'),
    path('admin/diretores/<int:diretor_id>/excluir/', views.excluir_diretor, name='excluir_diretor'),

    # Admin — CRUD Cursos
    path('admin/cursos/', views.gerenciar_cursos, name='gerenciar_cursos'),
    path('admin/cursos/cadastrar/', views.cadastrar_curso_admin, name='cadastrar_curso_admin'),
    path('admin/cursos/<int:curso_id>/editar/', views.editar_curso_admin, name='editar_curso_admin'),
    path('admin/cursos/<int:curso_id>/excluir/', views.excluir_curso_admin, name='excluir_curso_admin'),

    # Admin — CRUD Disciplinas
    path('admin/disciplinas/', views.gerenciar_disciplinas, name='gerenciar_disciplinas'),
    path('admin/disciplinas/cadastrar/', views.cadastrar_disciplina, name='cadastrar_disciplina'),
    path('admin/disciplinas/<str:disciplina_codigo>/editar/', views.editar_disciplina, name='editar_disciplina'),
    path('admin/disciplinas/<str:disciplina_codigo>/excluir/', views.excluir_disciplina, name='excluir_disciplina'),

    # Professor — Gerenciar atividades e validar respostas
    path('professor/atividades/', views.gerenciar_atividades, name='gerenciar_atividades'),
    path('professor/atividades/criar/', views.cadastrar_atividade, name='cadastrar_atividade'),
    path('professor/atividades/<int:id_atividade>/editar/', views.editar_atividade, name='editar_atividade'),
    path('professor/atividades/<int:id_atividade>/excluir/', views.excluir_atividade, name='excluir_atividade'),
    path('professor/validar/', views.validar_respostas, name='validar_respostas'),
    path('professor/validar/<int:id_resposta>/aprovar/', views.validar_resposta_professor, name='validar_resposta_professor'),
    path('professor/validar/<int:id_resposta>/rejeitar/', views.rejeitar_resposta_professor, name='rejeitar_resposta_professor'),
    path('professor/portarias/', views.portarias_professor, name='portarias_professor'),
    path('professor/disciplinas/', views.disciplinas_professor, name='disciplinas_professor'),
    path('api/professor/portaria/<int:portaria_id>/disciplinas/', views.api_disciplinas_portaria_professor, name='api_disciplinas_portaria_professor'),

    # Aluno — Portarias, atividades e respostas
    path('aluno/portarias/', views.minhas_portarias, name='minhas_portarias'),
    path('aluno/atividades/', views.atividades_disponiveis, name='atividades_disponiveis'),
    path('aluno/atividades/<int:atividade_id>/', views.visualizar_atividade, name='visualizar_atividade'),
    path('aluno/atividades/<int:atividade_id>/responder/', views.responder_atividade, name='responder_atividade'),
    path('aluno/respostas/', views.minhas_respostas, name='minhas_respostas'),
    path('aluno/respostas/<int:resposta_id>/', views.visualizar_resposta, name='visualizar_resposta'),
    path('aluno/respostas/<int:resposta_id>/editar/', views.editar_resposta, name='editar_resposta'),
    path('aluno/respostas/<int:resposta_id>/excluir/', views.excluir_resposta, name='excluir_resposta'),
    path('aluno/disciplinas/', views.minhas_disciplinas, name='minhas_disciplinas'),
]
