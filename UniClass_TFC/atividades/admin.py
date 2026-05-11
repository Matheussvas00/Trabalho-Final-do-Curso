from django.contrib import admin
from .models import (
    Usuario, Curso, Aluno, Professor, Diretor, Admin,
    Disciplina, AlunoDisciplina, ProfessorDisciplina,
    Portaria, PortariaDisciplina,
    Atividade, RespostaAtividade, Notificacao, Historico
)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'email', 'tipo_usuario')
    list_filter = ('tipo_usuario',)
    search_fields = ('email',)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('id_curso', 'nome_curso')
    search_fields = ('nome_curso',)


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('id_aluno', 'nome_completo', 'matricula_aluno', 'curso_aluno', 'periodo')
    list_filter = ('curso_aluno', 'periodo')
    search_fields = ('nome_aluno', 'sobrenome_aluno', 'matricula_aluno')


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('id_professor', 'nome_completo', 'curso_professor')
    list_filter = ('curso_professor',)
    search_fields = ('nome_professor', 'sobrenome_professor')


@admin.register(Diretor)
class DiretorAdmin(admin.ModelAdmin):
    list_display = ('id_diretor', 'nome_completo', 'curso_fk')
    list_filter = ('curso_fk',)
    search_fields = ('nome_diretor', 'sobrenome_diretor')


@admin.register(Admin)
class AdminPerfilAdmin(admin.ModelAdmin):
    list_display = ('id_admin', 'nome_completo')
    search_fields = ('nome_admin', 'sobrenome_admin')


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('codigo_disciplina', 'nome_disciplina', 'curso_fk')
    list_filter = ('curso_fk',)
    search_fields = ('codigo_disciplina', 'nome_disciplina')


@admin.register(AlunoDisciplina)
class AlunoDisciplinaAdmin(admin.ModelAdmin):
    list_display = ('id_alunofk', 'codigo_disciplinafk', 'data_matricula')
    search_fields = ('id_alunofk__nome_aluno', 'codigo_disciplinafk__nome_disciplina')
    date_hierarchy = 'data_matricula'


@admin.register(ProfessorDisciplina)
class ProfessorDisciplinaAdmin(admin.ModelAdmin):
    list_display = ('id_professorfk', 'codigo_disciplinafk', 'data_atribuicao')
    search_fields = ('id_professorfk__nome_professor', 'codigo_disciplinafk__nome_disciplina')
    date_hierarchy = 'data_atribuicao'


@admin.register(Portaria)
class PortariaAdmin(admin.ModelAdmin):
    list_display = ('numero_portaria', 'id_alunofk', 'id_diretorfk', 'status', 'data_criacao')
    list_filter = ('status', 'data_criacao', 'id_diretorfk')
    search_fields = ('numero_portaria', 'id_alunofk__nome_aluno', 'motivo_portaria')
    date_hierarchy = 'data_criacao'


@admin.register(PortariaDisciplina)
class PortariaDisciplinaAdmin(admin.ModelAdmin):
    list_display = ('id_portariafk', 'codigo_disciplinafk')
    search_fields = ('id_portariafk__numero_portaria', 'codigo_disciplinafk__nome_disciplina')


@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ('id_atividade', 'titulo', 'codigo_disciplinafk', 'id_professorfk', 'id_portariafk', 'data_limite_resposta', 'status', 'prazo_vencido')
    list_filter = ('status', 'data_criacao', 'data_limite_resposta', 'id_portariafk')
    search_fields = ('titulo', 'descricao')
    date_hierarchy = 'data_criacao'


@admin.register(RespostaAtividade)
class RespostaAtividadeAdmin(admin.ModelAdmin):
    list_display = ('id_resposta', 'id_atividade', 'id_alunofk', 'data_envio', 'status_professor', 'status_diretor', 'status')
    list_filter = ('status', 'status_professor', 'status_diretor', 'data_envio')
    search_fields = ('id_atividade__titulo', 'id_alunofk__nome_aluno')
    date_hierarchy = 'data_envio'
    readonly_fields = ('data_validacao_professor', 'data_validacao_diretor')


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ('id_notificacao', 'titulo', 'id_usuariodestino', 'data_hora', 'lida')
    list_filter = ('lida', 'data_hora')
    search_fields = ('titulo', 'mensagem')
    date_hierarchy = 'data_hora'


@admin.register(Historico)
class HistoricoAdmin(admin.ModelAdmin):
    list_display = ('id_historico', 'id_usuario', 'data_hora')
    list_filter = ('data_hora',)
    search_fields = ('id_usuario__email',)
    date_hierarchy = 'data_hora'
