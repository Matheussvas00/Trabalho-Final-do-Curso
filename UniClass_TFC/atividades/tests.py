"""
Testes unitários do UniClass
Cobertura: modelos, autenticação, regras de negócio e fluxo de validação
Execute com: python manage.py test atividades
"""

from django.test import TestCase
from django.db import IntegrityError
from datetime import date, timedelta

from atividades.models import (
    Usuario, Curso, Aluno, Professor, Diretor,
    Disciplina, ProfessorDisciplina, AlunoDisciplina,
    Portaria, PortariaDisciplina, Atividade, RespostaAtividade,
    PasswordResetToken,
)
from atividades.authentication.backends import (
    UniClassAuthBackend,
    validar_email_academico,
    detectar_tipo_usuario_por_email,
)


# =========================================================
# HELPERS
# =========================================================

def criar_curso(nome="Engenharia de Software"):
    return Curso.objects.create(nome_curso=nome)

def criar_usuario(email="teste@unirv.edu.br", tipo="professor", senha="Senha@123"):
    u = Usuario(email=email, tipo_usuario=tipo)
    u.set_password(senha)
    u.save()
    return u

def criar_diretor(curso, nome="Carlos", sobrenome="Silva", email="diretor@unirv.edu.br"):
    u = criar_usuario(email=email, tipo="diretor")
    return Diretor.objects.create(
        id_diretor=u, nome_diretor=nome, sobrenome_diretor=sobrenome,
        curso_diretor=curso.nome_curso, curso_fk=curso,
    )

def criar_professor(curso=None, nome="Ana", sobrenome="Costa", email="professor@unirv.edu.br"):
    u = criar_usuario(email=email, tipo="professor")
    p = Professor.objects.create(
        id_professor=u, nome_professor=nome, sobrenome_professor=sobrenome,
        curso_professor=curso.nome_curso if curso else "Eng. Software",
    )
    if curso:
        p.cursos.add(curso)
    return p

def criar_aluno(curso, nome="Lucas", sobrenome="Rocha",
                email="aluno@academico.unirv.edu.br", matricula="20210001"):
    u = criar_usuario(email=email, tipo="aluno")
    a = Aluno.objects.create(
        id_aluno=u, nome_aluno=nome, sobrenome_aluno=sobrenome,
        curso_aluno=curso.nome_curso, periodo="5", matricula_aluno=matricula,
    )
    a.cursos.add(curso)
    return a

def criar_disciplina(curso, codigo="ES001", nome="Engenharia de Requisitos"):
    return Disciplina.objects.create(
        codigo_disciplina=codigo, nome_disciplina=nome, curso_fk=curso,
    )

def criar_portaria(diretor, aluno, disciplinas=None, num="PORT-001"):
    hoje = date.today()
    p = Portaria.objects.create(
        id_diretorfk=diretor, id_alunofk=aluno, numero_portaria=num,
        prazo_professor_criar_atividades=hoje + timedelta(days=5),
        prazo_aluno_responder=hoje + timedelta(days=10),
        prazo_validacao_final=hoje + timedelta(days=15),
        motivo_portaria="Afastamento por doença", status="aguardando_atividades",
    )
    if disciplinas:
        for d in disciplinas:
            PortariaDisciplina.objects.create(id_portariafk=p, codigo_disciplinafk=d)
    return p

def criar_atividade(portaria, disciplina, professor, titulo="Atividade 1"):
    return Atividade.objects.create(
        id_portariafk=portaria, codigo_disciplinafk=disciplina,
        id_professorfk=professor, titulo=titulo,
        descricao="Descrição da atividade de teste.",
        data_limite_resposta=portaria.prazo_aluno_responder,
        status="aguardando_resposta",
    )


# =========================================================
# TESTES — USUARIO
# =========================================================

class UsuarioModelTests(TestCase):

    def test_senha_armazenada_como_hash(self):
        u = Usuario(email="u@unirv.edu.br", tipo_usuario="professor")
        u.set_password("MinhaSenh@123")
        self.assertNotEqual(u.senha, "MinhaSenh@123")
        self.assertTrue(u.senha.startswith("pbkdf2_sha256"))

    def test_check_password_correto(self):
        u = criar_usuario(email="ck@unirv.edu.br")
        self.assertTrue(u.check_password("Senha@123"))

    def test_check_password_incorreto(self):
        u = criar_usuario(email="ck2@unirv.edu.br")
        self.assertFalse(u.check_password("SenhaErrada"))

    def test_is_authenticated_retorna_true(self):
        u = criar_usuario(email="ia@unirv.edu.br")
        self.assertTrue(u.is_authenticated)

    def test_email_unico(self):
        criar_usuario(email="duplicado@unirv.edu.br")
        with self.assertRaises(IntegrityError):
            criar_usuario(email="duplicado@unirv.edu.br")

    def test_str_contem_email(self):
        u = criar_usuario(email="str@unirv.edu.br", tipo="professor")
        self.assertIn("str@unirv.edu.br", str(u))

    def test_get_session_auth_hash_retorna_string(self):
        u = criar_usuario(email="session@unirv.edu.br")
        h = u.get_session_auth_hash()
        self.assertIsInstance(h, str)
        self.assertTrue(len(h) > 0)


# =========================================================
# TESTES — PERFIS
# =========================================================

class PerfilTests(TestCase):

    def setUp(self):
        self.curso = criar_curso()

    def test_nome_completo_aluno(self):
        a = criar_aluno(self.curso)
        self.assertEqual(a.nome_completo, "Lucas Rocha")

    def test_nome_completo_professor(self):
        p = criar_professor(self.curso)
        self.assertEqual(p.nome_completo, "Ana Costa")

    def test_nome_completo_diretor(self):
        d = criar_diretor(self.curso)
        self.assertEqual(d.nome_completo, "Carlos Silva")

    def test_str_professor_contem_nome(self):
        p = criar_professor(self.curso)
        self.assertIn("Ana", str(p))

    def test_str_aluno_contem_nome(self):
        a = criar_aluno(self.curso)
        self.assertIn("Lucas", str(a))

    def test_str_diretor_contem_nome(self):
        d = criar_diretor(self.curso)
        self.assertIn("Carlos", str(d))


# =========================================================
# TESTES — DISCIPLINA
# =========================================================

class DisciplinaTests(TestCase):

    def setUp(self):
        self.curso = criar_curso()

    def test_criar_disciplina(self):
        d = criar_disciplina(self.curso)
        self.assertEqual(d.codigo_disciplina, "ES001")

    def test_str_disciplina_contem_codigo_e_nome(self):
        d = criar_disciplina(self.curso)
        self.assertIn("ES001", str(d))
        self.assertIn("Engenharia de Requisitos", str(d))

    def test_disciplina_vinculada_ao_curso(self):
        d = criar_disciplina(self.curso)
        self.assertEqual(d.curso_fk, self.curso)

    def test_vincular_professor_a_disciplina(self):
        p = criar_professor(self.curso)
        d = criar_disciplina(self.curso)
        ProfessorDisciplina.objects.create(id_professorfk=p, codigo_disciplinafk=d)
        self.assertIn(p, d.professores.all())


# =========================================================
# TESTES — PORTARIA
# =========================================================

class PortariaTests(TestCase):

    def setUp(self):
        self.curso = criar_curso()
        self.diretor = criar_diretor(self.curso)
        self.aluno = criar_aluno(self.curso)
        self.disciplina = criar_disciplina(self.curso)
        AlunoDisciplina.objects.create(id_alunofk=self.aluno, codigo_disciplinafk=self.disciplina)
        p = criar_professor(self.curso, email="prof.port@unirv.edu.br")
        ProfessorDisciplina.objects.create(id_professorfk=p, codigo_disciplinafk=self.disciplina)

    def test_criar_portaria_valida(self):
        portaria = criar_portaria(self.diretor, self.aluno, num="PORT-001")
        self.assertEqual(portaria.status, "aguardando_atividades")
        self.assertIsNotNone(portaria.id_portaria)

    def test_prazo_atividades_apos_respostas_falha(self):
        hoje = date.today()
        with self.assertRaises(ValueError):
            Portaria.objects.create(
                id_diretorfk=self.diretor, id_alunofk=self.aluno,
                numero_portaria="PORT-ERR",
                prazo_professor_criar_atividades=hoje + timedelta(days=10),
                prazo_aluno_responder=hoje + timedelta(days=5),  # menor!
                prazo_validacao_final=hoje + timedelta(days=15),
                motivo_portaria="Inválido",
            )

    def test_prazo_validacao_antes_respostas_falha(self):
        hoje = date.today()
        with self.assertRaises(ValueError):
            Portaria.objects.create(
                id_diretorfk=self.diretor, id_alunofk=self.aluno,
                numero_portaria="PORT-ERR2",
                prazo_professor_criar_atividades=hoje + timedelta(days=5),
                prazo_aluno_responder=hoje + timedelta(days=10),
                prazo_validacao_final=hoje + timedelta(days=8),  # menor!
                motivo_portaria="Inválido",
            )

    def test_prazo_atividades_vencido_true(self):
        portaria = criar_portaria(self.diretor, self.aluno, num="PORT-002")
        Portaria.objects.filter(pk=portaria.pk).update(
            prazo_professor_criar_atividades=date.today() - timedelta(days=1)
        )
        portaria.refresh_from_db()
        self.assertTrue(portaria.prazo_atividades_vencido)

    def test_prazo_atividades_nao_vencido(self):
        portaria = criar_portaria(self.diretor, self.aluno, num="PORT-003")
        self.assertFalse(portaria.prazo_atividades_vencido)

    def test_numero_portaria_unico(self):
        criar_portaria(self.diretor, self.aluno, num="PORT-DUP")
        with self.assertRaises(IntegrityError):
            criar_portaria(self.diretor, self.aluno, num="PORT-DUP")

    def test_str_portaria_contem_numero(self):
        portaria = criar_portaria(self.diretor, self.aluno, num="PORT-STR")
        self.assertIn("PORT-STR", str(portaria))


# =========================================================
# TESTES — ATIVIDADE
# =========================================================

class AtividadeTests(TestCase):

    def setUp(self):
        self.curso = criar_curso()
        self.diretor = criar_diretor(self.curso)
        self.aluno = criar_aluno(self.curso)
        self.disciplina = criar_disciplina(self.curso)
        self.professor = criar_professor(self.curso, email="prof.atv@unirv.edu.br")
        AlunoDisciplina.objects.create(id_alunofk=self.aluno, codigo_disciplinafk=self.disciplina)
        ProfessorDisciplina.objects.create(id_professorfk=self.professor, codigo_disciplinafk=self.disciplina)
        self.portaria = criar_portaria(self.diretor, self.aluno, disciplinas=[self.disciplina], num="PORT-ATI")

    def test_criar_atividade_valida(self):
        atv = criar_atividade(self.portaria, self.disciplina, self.professor)
        self.assertEqual(atv.titulo, "Atividade 1")
        self.assertEqual(atv.status, "aguardando_resposta")

    def test_data_limite_alem_do_prazo_falha(self):
        with self.assertRaises(ValueError):
            Atividade.objects.create(
                id_portariafk=self.portaria, codigo_disciplinafk=self.disciplina,
                id_professorfk=self.professor, titulo="Fora do prazo",
                descricao="Teste",
                data_limite_resposta=self.portaria.prazo_aluno_responder + timedelta(days=5),
                status="aguardando_resposta",
            )

    def test_prazo_vencido_false_quando_futuro(self):
        atv = criar_atividade(self.portaria, self.disciplina, self.professor)
        self.assertFalse(atv.prazo_vencido)

    def test_prazo_vencido_true_quando_passado(self):
        atv = criar_atividade(self.portaria, self.disciplina, self.professor)
        Atividade.objects.filter(pk=atv.pk).update(
            data_limite_resposta=date.today() - timedelta(days=1)
        )
        atv.refresh_from_db()
        self.assertTrue(atv.prazo_vencido)

    def test_str_atividade_contem_titulo(self):
        atv = criar_atividade(self.portaria, self.disciplina, self.professor)
        self.assertIn("Atividade 1", str(atv))


# =========================================================
# TESTES — RESPOSTA ATIVIDADE
# =========================================================

class RespostaAtividadeTests(TestCase):

    def setUp(self):
        self.curso = criar_curso()
        self.diretor = criar_diretor(self.curso)
        self.aluno = criar_aluno(self.curso)
        self.disciplina = criar_disciplina(self.curso)
        self.professor = criar_professor(self.curso, email="prof.resp@unirv.edu.br")
        AlunoDisciplina.objects.create(id_alunofk=self.aluno, codigo_disciplinafk=self.disciplina)
        ProfessorDisciplina.objects.create(id_professorfk=self.professor, codigo_disciplinafk=self.disciplina)
        self.portaria = criar_portaria(self.diretor, self.aluno, disciplinas=[self.disciplina], num="PORT-RESP")
        self.atividade = criar_atividade(self.portaria, self.disciplina, self.professor)

    def _criar_resposta(self):
        return RespostaAtividade.objects.create(
            id_atividade=self.atividade, id_alunofk=self.aluno,
            descricao_resposta="Resposta de teste.", status="pendente",
        )

    def test_criar_resposta_valida(self):
        resp = self._criar_resposta()
        self.assertEqual(resp.status, "pendente")
        self.assertEqual(resp.status_professor, "pendente")

    def test_validar_professor_aprovada(self):
        resp = self._criar_resposta()
        resp.validar_professor(aprovada=True, observacao="Bom trabalho!")
        self.assertEqual(resp.status_professor, "aprovada")
        self.assertEqual(resp.status, "aprovada_professor")
        self.assertIsNotNone(resp.data_validacao_professor)

    def test_validar_professor_rejeitada(self):
        resp = self._criar_resposta()
        resp.validar_professor(aprovada=False, observacao="Refaça o exercício 3.")
        self.assertEqual(resp.status_professor, "rejeitada")
        self.assertEqual(resp.status, "rejeitada_professor")

    def test_validar_diretor_sem_aprovacao_professor_falha(self):
        resp = self._criar_resposta()
        with self.assertRaises(ValueError):
            resp.validar_diretor(aprovada=True)

    def test_fluxo_completo_aprovacao(self):
        resp = self._criar_resposta()
        resp.validar_professor(aprovada=True)
        resp.validar_diretor(aprovada=True, observacao="Aprovado!")
        self.assertEqual(resp.status_diretor, "aprovada")
        self.assertEqual(resp.status, "aprovada_diretor")
        self.assertIsNotNone(resp.data_validacao_diretor)

    def test_diretor_pode_rejeitar_apos_professor_aprovar(self):
        resp = self._criar_resposta()
        resp.validar_professor(aprovada=True)
        resp.validar_diretor(aprovada=False, observacao="Inconsistências.")
        self.assertEqual(resp.status, "rejeitada_diretor")

    def test_aluno_errado_nao_pode_responder(self):
        outro = criar_aluno(
            self.curso, nome="Outro", sobrenome="Aluno",
            email="outro@academico.unirv.edu.br", matricula="20220002",
        )
        with self.assertRaises(ValueError):
            RespostaAtividade.objects.create(
                id_atividade=self.atividade, id_alunofk=outro,
                descricao_resposta="Tentativa inválida.", status="pendente",
            )

    def test_str_resposta_contem_palavra_resposta(self):
        resp = self._criar_resposta()
        self.assertIn("Resposta", str(resp))


# =========================================================
# TESTES — VALIDAÇÃO DE E-MAIL
# =========================================================

class EmailValidationTests(TestCase):

    def test_email_aluno_valido(self):
        valido, msg = validar_email_academico("lucas@academico.unirv.edu.br", tipo_usuario="aluno")
        self.assertTrue(valido)
        self.assertIsNone(msg)

    def test_email_aluno_dominio_errado(self):
        valido, msg = validar_email_academico("lucas@gmail.com", tipo_usuario="aluno")
        self.assertFalse(valido)
        self.assertIn("academico.unirv.edu.br", msg)

    def test_email_professor_valido(self):
        valido, msg = validar_email_academico("prof@unirv.edu.br", tipo_usuario="professor")
        self.assertTrue(valido)

    def test_email_professor_dominio_errado(self):
        valido, msg = validar_email_academico("prof@gmail.com", tipo_usuario="professor")
        self.assertFalse(valido)

    def test_email_diretor_valido(self):
        valido, msg = validar_email_academico("diretor@unirv.edu.br", tipo_usuario="diretor")
        self.assertTrue(valido)

    def test_email_vazio_invalido(self):
        valido, msg = validar_email_academico("")
        self.assertFalse(valido)

    def test_email_none_invalido(self):
        valido, msg = validar_email_academico(None)
        self.assertFalse(valido)

    def test_detectar_tipo_aluno_por_email(self):
        tipo = detectar_tipo_usuario_por_email("aluno@academico.unirv.edu.br")
        self.assertEqual(tipo, "aluno")

    def test_detectar_tipo_staff_por_email(self):
        tipo = detectar_tipo_usuario_por_email("prof@unirv.edu.br")
        self.assertEqual(tipo, "staff")

    def test_detectar_tipo_externo_retorna_none(self):
        tipo = detectar_tipo_usuario_por_email("user@gmail.com")
        self.assertIsNone(tipo)


# =========================================================
# TESTES — BACKEND DE AUTENTICAÇÃO
# =========================================================

class AuthBackendTests(TestCase):

    def setUp(self):
        self.backend = UniClassAuthBackend()
        self.u = criar_usuario(email="auth@unirv.edu.br", tipo="professor", senha="Senha@123")

    def test_autenticar_credenciais_corretas(self):
        user = self.backend.authenticate(None, username="auth@unirv.edu.br", password="Senha@123")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "auth@unirv.edu.br")

    def test_autenticar_senha_errada_retorna_none(self):
        user = self.backend.authenticate(None, username="auth@unirv.edu.br", password="SenhaErrada")
        self.assertIsNone(user)

    def test_autenticar_email_inexistente_retorna_none(self):
        user = self.backend.authenticate(None, username="nao@unirv.edu.br", password="Senha@123")
        self.assertIsNone(user)

    def test_autenticar_sem_credenciais_retorna_none(self):
        user = self.backend.authenticate(None, username=None, password=None)
        self.assertIsNone(user)

    def test_get_user_existente(self):
        user = self.backend.get_user(self.u.pk)
        self.assertEqual(user.email, "auth@unirv.edu.br")

    def test_get_user_inexistente_retorna_none(self):
        user = self.backend.get_user(999999)
        self.assertIsNone(user)

    def test_autenticacao_case_insensitive(self):
        user = self.backend.authenticate(None, username="AUTH@unirv.edu.br", password="Senha@123")
        self.assertIsNotNone(user)


# =========================================================
# TESTES — PASSWORD RESET TOKEN
# =========================================================

class PasswordResetTokenTests(TestCase):

    def setUp(self):
        self.u = criar_usuario(email="reset@unirv.edu.br")

    def test_criar_token_retorna_string_nao_vazia(self):
        token_bruto = PasswordResetToken.criar_para(self.u)
        self.assertIsInstance(token_bruto, str)
        self.assertTrue(len(token_bruto) > 10)

    def test_verificar_token_valido_retorna_instancia(self):
        token_bruto = PasswordResetToken.criar_para(self.u)
        inst = PasswordResetToken.verificar(token_bruto)
        self.assertIsNotNone(inst)
        self.assertEqual(inst.usuario, self.u)

    def test_verificar_token_invalido_retorna_none(self):
        inst = PasswordResetToken.verificar("token_invalido_xyz")
        self.assertIsNone(inst)

    def test_novo_token_invalida_anteriores(self):
        PasswordResetToken.criar_para(self.u)
        PasswordResetToken.criar_para(self.u)
        nao_usados = PasswordResetToken.objects.filter(usuario=self.u, usado=False).count()
        self.assertEqual(nao_usados, 1)

    def test_hash_diferente_do_token_bruto(self):
        token_bruto = PasswordResetToken.criar_para(self.u)
        inst = PasswordResetToken.objects.filter(usuario=self.u, usado=False).first()
        self.assertNotEqual(inst.token_hash, token_bruto)


# =========================================================
# TESTES — CURSO
# =========================================================

class CursoTests(TestCase):

    def test_criar_curso(self):
        c = criar_curso("Ciência da Computação")
        self.assertEqual(c.nome_curso, "Ciência da Computação")

    def test_str_curso_retorna_nome(self):
        c = criar_curso("Sistemas de Informação")
        self.assertEqual(str(c), "Sistemas de Informação")
