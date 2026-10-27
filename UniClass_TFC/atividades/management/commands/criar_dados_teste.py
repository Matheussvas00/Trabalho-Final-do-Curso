"""
Cria dados de teste: 1 curso, 2 disciplinas, 2 professores e 1 aluno.

Pode ser executado várias vezes: o que já existe não é duplicado.
A senha dos usuários de teste vem da variável TESTE_SENHA (padrão: Teste@2026).

Uso:
    python manage.py criar_dados_teste
"""
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from atividades.models import (
    Aluno, AlunoDisciplina, Curso, Disciplina, Professor, ProfessorDisciplina, Usuario,
)

CURSO = 'Engenharia de Software'
DISCIPLINAS = [
    ('ES101', 'Engenharia de Requisitos'),
    ('ES102', 'Banco de Dados'),
]
PROFESSORES = [
    # e-mail, nome, sobrenome, disciplina
    ('ana.costa@unirv.edu.br', 'Ana', 'Costa', 'ES101'),
    ('bruno.lima@unirv.edu.br', 'Bruno', 'Lima', 'ES102'),
]
ALUNO = ('lucas.rocha@academico.unirv.edu.br', 'Lucas', 'Rocha', '20260001', '5')


class Command(BaseCommand):
    help = 'Cria um curso, duas disciplinas, dois professores e um aluno para testes.'

    def _usuario(self, email, tipo, senha):
        usuario = Usuario.objects.filter(email=email).first()
        if usuario:
            return usuario, False
        usuario = Usuario(email=email, tipo_usuario=tipo)
        usuario.set_password(senha)
        usuario.save()
        return usuario, True

    @transaction.atomic
    def handle(self, *args, **options):
        senha = os.getenv('TESTE_SENHA', 'Teste@2026')

        curso = Curso.objects.filter(nome_curso=CURSO).first() or Curso.objects.create(nome_curso=CURSO)

        disciplinas = {}
        for codigo, nome in DISCIPLINAS:
            disciplinas[codigo], _ = Disciplina.objects.get_or_create(
                codigo_disciplina=codigo, defaults={'nome_disciplina': nome, 'curso_fk': curso})

        for email, nome, sobrenome, codigo in PROFESSORES:
            usuario, novo = self._usuario(email, 'professor', senha)
            professor, _ = Professor.objects.get_or_create(id_professor=usuario, defaults={
                'nome_professor': nome, 'sobrenome_professor': sobrenome, 'curso_professor': CURSO})
            professor.cursos.add(curso)
            ProfessorDisciplina.objects.get_or_create(
                id_professorfk=professor, codigo_disciplinafk=disciplinas[codigo])
            self.stdout.write(f'Professor {nome} {sobrenome} <{email}> ' + ('criado' if novo else 'já existia'))

        email, nome, sobrenome, matricula, periodo = ALUNO
        usuario, novo = self._usuario(email, 'aluno', senha)
        aluno, _ = Aluno.objects.get_or_create(id_aluno=usuario, defaults={
            'nome_aluno': nome, 'sobrenome_aluno': sobrenome, 'curso_aluno': CURSO,
            'periodo': periodo, 'matricula_aluno': matricula})
        aluno.cursos.add(curso)
        for disciplina in disciplinas.values():
            AlunoDisciplina.objects.get_or_create(id_alunofk=aluno, codigo_disciplinafk=disciplina)
        self.stdout.write(f'Aluno {nome} {sobrenome} <{email}> ' + ('criado' if novo else 'já existia'))

        self.stdout.write(self.style.SUCCESS('Dados de teste prontos.'))
