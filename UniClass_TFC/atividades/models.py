from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password as django_check_password
import uuid
import hashlib
import secrets


class Usuario(models.Model):
    """Modelo base para todos os usuários do sistema"""
    TIPO_CHOICES = [
        ('admin', 'Administrador'),
        ('diretor', 'Diretor'),
        ('professor', 'Professor'),
        ('aluno', 'Aluno'),
    ]

    id_usuario = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=150, unique=True)
    senha = models.CharField(max_length=255)  # aumentado para comportar hash
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_CHOICES)

    # Campos exigidos pelo sistema de sessão do Django
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f"{self.email} ({self.get_tipo_usuario_display()})"

    # ── Compatibilidade com Django auth / session framework ─────────────────
    is_anonymous = False
    is_active = True

    @property
    def is_authenticated(self):
        return True

    def set_password(self, raw_password):
        """Gera hash da senha e armazena em self.senha"""
        self.senha = make_password(raw_password)

    def check_password(self, raw_password):
        """Verifica se a senha em texto puro bate com o hash armazenado"""
        return django_check_password(raw_password, self.senha)

    def get_session_auth_hash(self):
        """Retorna hash da senha para controle de sessão do Django"""
        from django.utils.crypto import salted_hmac
        key_salt = 'django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash'
        return salted_hmac(key_salt, self.senha).hexdigest()


class Curso(models.Model):
    """Cursos oferecidos pela faculdade"""
    id_curso = models.AutoField(primary_key=True)
    nome_curso = models.CharField(max_length=100)

    class Meta:
        db_table = 'curso'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'

    def __str__(self):
        return self.nome_curso


class Aluno(models.Model):
    """Informações específicas de alunos"""
    id_aluno = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='id_aluno'
    )
    nome_aluno = models.CharField(max_length=150)
    sobrenome_aluno = models.CharField(max_length=150)
    curso_aluno = models.CharField(max_length=150)
    periodo = models.CharField(max_length=150)
    matricula_aluno = models.CharField(max_length=150, blank=True, null=True)
    ativo = models.BooleanField(default=True, help_text='False = inativado por LGPD (não excluído)')
    cursos = models.ManyToManyField(
        'Curso',
        related_name='alunos',
        blank=True,
        db_table='aluno_curso',
    )

    class Meta:
        db_table = 'aluno'
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'

    def __str__(self):
        return f"{self.nome_aluno} {self.sobrenome_aluno} - {self.matricula_aluno}"

    @property
    def nome_completo(self):
        return f"{self.nome_aluno} {self.sobrenome_aluno}"


class Professor(models.Model):
    """Informações específicas de professores"""
    id_professor = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='id_professor'
    )
    nome_professor = models.CharField(max_length=150)
    sobrenome_professor = models.CharField(max_length=150)
    curso_professor = models.CharField(max_length=150)
    ativo = models.BooleanField(default=True, help_text='False = inativado por LGPD (não excluído)')
    cursos = models.ManyToManyField(
        'Curso',
        related_name='professores',
        blank=True,
        db_table='professor_curso',
    )

    class Meta:
        db_table = 'professor'
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'

    def __str__(self):
        return f"Prof. {self.nome_professor} {self.sobrenome_professor}"

    @property
    def nome_completo(self):
        return f"{self.nome_professor} {self.sobrenome_professor}"


class Diretor(models.Model):
    """Informações específicas de diretores"""
    id_diretor = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='id_diretor'
    )
    nome_diretor = models.CharField(max_length=150)
    sobrenome_diretor = models.CharField(max_length=150)
    curso_diretor = models.CharField(max_length=150)  # legado — mantido por compatibilidade
    ativo = models.BooleanField(default=True, help_text='False = inativado por LGPD (não excluído)')
    curso_fk = models.ForeignKey(
        'Curso',
        on_delete=models.PROTECT,  # PROTECT para evitar exclusão de curso com diretor vinculado
        null=False,  # Obrigatório - diretor DEVE ter um curso
        blank=False,
        db_column='curso_fk',
        related_name='diretores',
        help_text='Curso que o diretor administra (obrigatório)'
    )

    class Meta:
        db_table = 'diretor'
        verbose_name = 'Diretor'
        verbose_name_plural = 'Diretores'

    def __str__(self):
        return f"Dir. {self.nome_diretor} {self.sobrenome_diretor}"

    @property
    def nome_completo(self):
        return f"{self.nome_diretor} {self.sobrenome_diretor}"

    def save(self, *args, **kwargs):
        """Valida que diretor tem curso vinculado antes de salvar"""
        if not self.curso_fk:
            raise ValueError("Diretor deve estar vinculado a um curso")
        super().save(*args, **kwargs)


class Admin(models.Model):
    """Informações específicas de administradores do sistema"""
    id_admin = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='id_admin'
    )
    nome_admin = models.CharField(max_length=150)
    sobrenome_admin = models.CharField(max_length=150)

    class Meta:
        db_table = 'admin_perfil'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return f"Admin {self.nome_admin} {self.sobrenome_admin}"

    @property
    def nome_completo(self):
        return f"{self.nome_admin} {self.sobrenome_admin}"


class Disciplina(models.Model):
    """Disciplinas oferecidas nos cursos"""
    codigo_disciplina = models.CharField(max_length=25, primary_key=True)
    nome_disciplina = models.CharField(max_length=50)
    curso_fk = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        db_column='curso_fk',
        related_name='disciplinas'
    )
    professores = models.ManyToManyField(
        Professor,
        through='ProfessorDisciplina',
        related_name='disciplinas_lecionadas'
    )

    class Meta:
        db_table = 'disciplina'
        verbose_name = 'Disciplina'
        verbose_name_plural = 'Disciplinas'

    def __str__(self):
        return f"{self.codigo_disciplina} - {self.nome_disciplina}"


class ProfessorDisciplina(models.Model):
    """Relação many-to-many entre Professor e Disciplina"""
    id_professorfk = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,
        db_column='id_professorfk',
        related_name='disciplinas_professor'
    )
    codigo_disciplinafk = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        db_column='codigo_disciplinafk',
        related_name='professores_disciplina'
    )
    data_atribuicao = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'professor_disciplina'
        unique_together = ('id_professorfk', 'codigo_disciplinafk')
        verbose_name = 'Professor-Disciplina'
        verbose_name_plural = 'Professores-Disciplinas'

    def __str__(self):
        return f"{self.id_professorfk.nome_completo} - {self.codigo_disciplinafk.nome_disciplina}"


class AlunoDisciplina(models.Model):
    """Relação many-to-many entre Aluno e Disciplina"""
    id_alunofk = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        db_column='id_alunofk',
        related_name='matriculas'
    )
    codigo_disciplinafk = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        db_column='codigo_disciplinafk',
        related_name='alunos_matriculados'
    )
    data_matricula = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'aluno_disciplina'
        unique_together = ('id_alunofk', 'codigo_disciplinafk')
        verbose_name = 'Matrícula em Disciplina'
        verbose_name_plural = 'Matrículas em Disciplinas'

    def __str__(self):
        return f"{self.id_alunofk} - {self.codigo_disciplinafk}"


class Portaria(models.Model):
    """
    Portarias criadas pelo diretor para autorizar atividades domiciliares.
    Define prazos para criação de atividades, respostas e validações.
    """
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aguardando_atividades', 'Aguardando Criação de Atividades'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
    ]

    id_portaria = models.AutoField(primary_key=True)
    id_diretorfk = models.ForeignKey(
        Diretor,
        on_delete=models.CASCADE,
        db_column='id_diretorfk',
        related_name='portarias_criadas'
    )
    id_alunofk = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        db_column='id_alunofk',
        related_name='portarias'
    )
    numero_portaria = models.CharField(max_length=50, unique=True)
    data_criacao = models.DateTimeField(default=timezone.now)

    # Prazos da portaria
    prazo_professor_criar_atividades = models.DateField(
        help_text="Data limite para professores criarem as atividades"
    )
    prazo_aluno_responder = models.DateField(
        help_text="Data limite para o aluno responder as atividades"
    )
    prazo_validacao_final = models.DateField(
        help_text="Data limite para conclusão de todo o processo"
    )

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pendente')
    observacoes = models.TextField(blank=True, null=True)
    motivo_portaria = models.TextField(
        help_text="Motivo da criação da portaria (ex: afastamento por doença)"
    )
    atestado = models.FileField(
        upload_to='atestados/',
        blank=True,
        null=True,
        help_text="Atestado médico ou documento comprobatório"
    )

    # Relacionamento com disciplinas via tabela intermediária
    disciplinas = models.ManyToManyField(
        Disciplina,
        through='PortariaDisciplina',
        related_name='portarias'
    )

    class Meta:
        db_table = 'portaria'
        verbose_name = 'Portaria'
        verbose_name_plural = 'Portarias'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Portaria {self.numero_portaria} - {self.id_alunofk.nome_completo}"

    @property
    def prazo_atividades_vencido(self):
        """Verifica se o prazo para criação de atividades venceu"""
        from django.utils import timezone
        return timezone.now().date() > self.prazo_professor_criar_atividades

    @property
    def prazo_respostas_vencido(self):
        """Verifica se o prazo para respostas venceu"""
        from django.utils import timezone
        return timezone.now().date() > self.prazo_aluno_responder

    def save(self, *args, **kwargs):
        """
        Valida as regras de negócio antes de salvar:
        1. Diretor só pode criar portaria para alunos do seu curso
        2. Prazos devem estar em ordem cronológica
        """
        # Verifica se aluno está matriculado no curso que o diretor administra
        if not self.id_alunofk.cursos.filter(id_curso=self.id_diretorfk.curso_fk.id_curso).exists():
            raise ValueError(
                f"O diretor só pode criar portaria para alunos matriculados no curso "
                f"{self.id_diretorfk.curso_fk.nome_curso}"
            )

        # Valida ordem dos prazos
        if self.prazo_professor_criar_atividades >= self.prazo_aluno_responder:
            raise ValueError("Prazo para criar atividades deve ser anterior ao prazo para respostas")

        if self.prazo_aluno_responder >= self.prazo_validacao_final:
            raise ValueError("Prazo para respostas deve ser anterior ao prazo de validação final")

        super().save(*args, **kwargs)

    def validar_disciplinas(self, disciplinas_list):
        """
        Valida que todas as disciplinas da portaria são disciplinas em que:
        1. O aluno está matriculado
        2. Pertencem ao curso do diretor

        Args:
            disciplinas_list: Lista de objetos Disciplina

        Returns:
            tuple: (válido: bool, mensagem_erro: str ou None)
        """
        disciplinas_aluno = self.id_alunofk.matriculas.values_list(
            'codigo_disciplinafk', flat=True
        )

        for disciplina in disciplinas_list:
            # Verifica se aluno está matriculado na disciplina
            if disciplina.codigo_disciplina not in disciplinas_aluno:
                return False, f"Aluno não está matriculado na disciplina {disciplina.nome_disciplina}"

            # Verifica se disciplina pertence ao curso do diretor
            if disciplina.curso_fk != self.id_diretorfk.curso_fk:
                return False, f"Disciplina {disciplina.nome_disciplina} não pertence ao curso {self.id_diretorfk.curso_fk.nome_curso}"

        return True, None


class PortariaDisciplina(models.Model):
    """Relação many-to-many entre Portaria e Disciplina"""
    id_portariafk = models.ForeignKey(
        Portaria,
        on_delete=models.CASCADE,
        db_column='id_portariafk',
        related_name='disciplinas_portaria'
    )
    codigo_disciplinafk = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        db_column='codigo_disciplinafk',
        related_name='portarias_disciplina'
    )

    class Meta:
        db_table = 'portaria_disciplina'
        unique_together = ('id_portariafk', 'codigo_disciplinafk')
        verbose_name = 'Disciplina da Portaria'
        verbose_name_plural = 'Disciplinas das Portarias'

    def __str__(self):
        return f"Portaria {self.id_portariafk.numero_portaria} - {self.codigo_disciplinafk.nome_disciplina}"


class Atividade(models.Model):
    """Atividades domiciliares criadas pelos professores para as portarias"""
    STATUS_CHOICES = [
        ('aguardando_resposta', 'Aguardando Resposta'),
        ('respondida', 'Respondida'),
        ('aprovada_professor', 'Aprovada pelo Professor'),
        ('reprovada_professor', 'Reprovada pelo Professor'),
        ('aprovada_diretor', 'Aprovada pelo Diretor'),
        ('reprovada_diretor', 'Reprovada pelo Diretor'),
    ]

    id_atividade = models.AutoField(primary_key=True)
    id_portariafk = models.ForeignKey(
        Portaria,
        on_delete=models.CASCADE,
        db_column='id_portariafk',
        related_name='atividades'
    )
    codigo_disciplinafk = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        db_column='codigo_disciplinafk',
        related_name='atividades'
    )
    id_professorfk = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,
        db_column='id_professorfk',
        related_name='atividades_criadas'
    )
    titulo = models.CharField(max_length=150)
    descricao = models.TextField()
    anexo = models.CharField(max_length=255, blank=True, null=True, help_text="Caminho do arquivo anexo à atividade")
    data_criacao = models.DateTimeField(default=timezone.now)
    data_limite_resposta = models.DateField(
        help_text="Data limite para o aluno responder (dentro do prazo da portaria)"
    )
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='aguardando_resposta')

    class Meta:
        db_table = 'atividade'
        verbose_name = 'Atividade'
        verbose_name_plural = 'Atividades'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.titulo} - {self.codigo_disciplinafk}"

    @property
    def prazo_vencido(self):
        """Verifica se o prazo da atividade já passou"""
        from django.utils import timezone
        return timezone.now().date() > self.data_limite_resposta

    def save(self, *args, **kwargs):
        """
        Valida que a atividade está dentro dos prazos da portaria e que:
        1. A disciplina faz parte da portaria
        2. O professor está vinculado à disciplina
        3. A data limite está dentro do prazo da portaria
        """
        # Valida que data limite está dentro do prazo da portaria
        if self.data_limite_resposta > self.id_portariafk.prazo_aluno_responder:
            raise ValueError("A data limite da atividade não pode ultrapassar o prazo da portaria")

        # Valida que disciplina está na portaria
        if not self.id_portariafk.disciplinas.filter(codigo_disciplina=self.codigo_disciplinafk.codigo_disciplina).exists():
            raise ValueError(
                f"A disciplina {self.codigo_disciplinafk.nome_disciplina} não faz parte da portaria "
                f"{self.id_portariafk.numero_portaria}"
            )

        # Valida que professor está vinculado à disciplina
        professor_disciplinas = self.id_professorfk.disciplinas_professor.values_list(
            'codigo_disciplinafk', flat=True
        )
        if self.codigo_disciplinafk.codigo_disciplina not in professor_disciplinas:
            raise ValueError(
                f"Professor {self.id_professorfk.nome_completo} não está vinculado à disciplina "
                f"{self.codigo_disciplinafk.nome_disciplina}"
            )

        super().save(*args, **kwargs)


class RespostaAtividade(models.Model):
    """Respostas dos alunos às atividades"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada_prof', 'Aprovada pelo Professor'),
        ('rejeitada_prof', 'Rejeitada pelo Professor'),
        ('aprovada_dir', 'Aprovada pelo Diretor'),
        ('rejeitada_dir', 'Rejeitada pelo Diretor'),
    ]

    id_resposta = models.AutoField(primary_key=True)
    id_atividade = models.ForeignKey(
        Atividade,
        on_delete=models.CASCADE,
        db_column='id_atividade',
        related_name='respostas'
    )
    id_alunofk = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        db_column='id_alunofk',
        related_name='respostas'
    )
    arquivo = models.CharField(max_length=255, blank=True, null=True)
    descricao_resposta = models.TextField(blank=True, null=True)
    data_envio = models.DateTimeField(default=timezone.now)

    # Validação do Professor (primeira etapa)
    data_validacao_professor = models.DateTimeField(blank=True, null=True)
    observacao_professor = models.TextField(blank=True, null=True)
    status_professor = models.CharField(
        max_length=25,
        choices=[
            ('pendente', 'Pendente'),
            ('aprovada', 'Aprovada'),
            ('rejeitada', 'Rejeitada')
        ],
        default='pendente'
    )

    # Validação do Diretor (segunda etapa)
    data_validacao_diretor = models.DateTimeField(blank=True, null=True)
    observacao_diretor = models.TextField(blank=True, null=True)
    status_diretor = models.CharField(
        max_length=25,
        choices=[
            ('pendente', 'Pendente'),
            ('aprovada', 'Aprovada'),
            ('rejeitada', 'Rejeitada')
        ],
        default='pendente'
    )

    # Status geral da resposta
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pendente')

    class Meta:
        db_table = 'resposta_atividade'
        verbose_name = 'Resposta de Atividade'
        verbose_name_plural = 'Respostas de Atividades'
        ordering = ['-data_envio']
        # Um aluno só pode responder uma vez cada atividade
        unique_together = ('id_atividade', 'id_alunofk')

    def __str__(self):
        return f"Resposta #{self.id_resposta} - {self.id_atividade.titulo}"

    def save(self, *args, **kwargs):
        """
        Valida que apenas o aluno da portaria pode responder a atividade
        """
        if self.id_alunofk != self.id_atividade.id_portariafk.id_alunofk:
            raise ValueError(
                f"Apenas o aluno {self.id_atividade.id_portariafk.id_alunofk.nome_completo} "
                f"pode responder esta atividade da portaria {self.id_atividade.id_portariafk.numero_portaria}"
            )
        super().save(*args, **kwargs)

    def validar_professor(self, aprovada, observacao=''):
        """Validação pelo professor (primeira etapa)"""
        from django.utils import timezone
        self.data_validacao_professor = timezone.now()
        self.observacao_professor = observacao
        atividade = self.id_atividade
        if aprovada:
            self.status_professor = 'aprovada'
            self.status = 'aprovada_prof'
            atividade.status = 'aprovada_professor'
        else:
            self.status_professor = 'rejeitada'
            self.status = 'rejeitada_prof'
            atividade.status = 'reprovada_professor'
        self.save()
        atividade.save(update_fields=['status'])

    def validar_diretor(self, aprovada, observacao=''):
        """Validação final pelo diretor (segunda etapa)"""
        from django.utils import timezone
        if self.status_professor != 'aprovada':
            raise ValueError("A resposta deve ser pré-aprovada pelo professor antes da validação do diretor")

        self.data_validacao_diretor = timezone.now()
        self.observacao_diretor = observacao
        atividade = self.id_atividade
        portaria = atividade.id_portariafk
        if aprovada:
            self.status_diretor = 'aprovada'
            self.status = 'aprovada_dir'
            atividade.status = 'aprovada_diretor'
            atividade.save(update_fields=['status'])
            self.save()
            # Se todas as atividades da portaria foram aprovadas, conclui a portaria
            total = portaria.atividades.count()
            aprovadas = portaria.atividades.filter(status='aprovada_diretor').count()
            if total > 0 and aprovadas == total:
                portaria.status = 'concluida'
                portaria.save(update_fields=['status'])
        else:
            self.status_diretor = 'rejeitada'
            self.status = 'rejeitada_dir'
            atividade.status = 'reprovada_diretor'
            atividade.save(update_fields=['status'])
            # Retorna ao professor para reavaliação
            self.status_professor = 'pendente'
            self.status_diretor = 'pendente'
            self.save()




class Notificacao(models.Model):
    """Notificações enviadas aos usuários"""
    id_notificacao = models.AutoField(primary_key=True)
    id_usuariodestino = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='id_usuariodestino',
        related_name='notificacoes'
    )
    titulo = models.CharField(max_length=150)
    mensagem = models.TextField()
    data_hora = models.DateTimeField(default=timezone.now)
    lida = models.BooleanField(default=False)

    class Meta:
        db_table = 'notificacao'
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.titulo} - {self.id_usuariodestino.email}"


class Historico(models.Model):
    """Histórico de ações dos usuários no sistema"""
    ACAO_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('portaria_criada', 'Portaria Criada'),
        ('portaria_editada', 'Portaria Editada'),
        ('portaria_excluida', 'Portaria Excluída'),
        ('atividade_criada', 'Atividade Criada'),
        ('atividade_editada', 'Atividade Editada'),
        ('atividade_excluida', 'Atividade Excluída'),
        ('resposta_enviada', 'Resposta Enviada'),
        ('resposta_reenviada', 'Atividade Refeita e Reenviada'),
        ('resposta_editada', 'Resposta Editada'),
        ('resposta_aprovada_prof', 'Resposta Aprovada pelo Professor'),
        ('resposta_rejeitada_prof', 'Resposta Rejeitada pelo Professor'),
        ('resposta_aprovada_dir', 'Resposta Aprovada pelo Diretor'),
        ('resposta_rejeitada_dir', 'Resposta Rejeitada pelo Diretor'),
        ('aluno_cadastrado', 'Aluno Cadastrado'),
        ('professor_cadastrado', 'Professor Cadastrado'),
        ('diretor_cadastrado', 'Diretor Cadastrado'),
    ]

    id_historico = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='id_usuario',
        related_name='historico'
    )
    data_hora = models.DateTimeField(default=timezone.now)
    acao = models.CharField(max_length=50, choices=ACAO_CHOICES, default='login')
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'historico'
        verbose_name = 'Histórico'
        verbose_name_plural = 'Históricos'
        ordering = ['-data_hora']

    def __str__(self):
        return f"Histórico #{self.id_historico} - {self.id_usuario.email} - {self.get_acao_display()}"


class PasswordResetToken(models.Model):
    """
    Token seguro para redefinição de senha.
    O token bruto é enviado no link; o banco armazena apenas o hash SHA-256.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='reset_tokens',
        db_column='id_usuario'
    )
    token_hash = models.CharField(max_length=64, unique=True)  # SHA-256 hex
    criado_em = models.DateTimeField(default=timezone.now)
    usado = models.BooleanField(default=False)

    EXPIRACAO_MINUTOS = 60  # Link válido por 1 hora

    class Meta:
        db_table = 'password_reset_token'
        verbose_name = 'Token de Reset de Senha'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Reset #{self.id} — {self.usuario.email}"

    @classmethod
    def criar_para(cls, usuario):
        """Gera token bruto, salva hash e retorna o token bruto (para o link)."""
        # Invalida tokens anteriores não usados
        cls.objects.filter(usuario=usuario, usado=False).update(usado=True)
        token_bruto = secrets.token_urlsafe(40)
        token_hash  = hashlib.sha256(token_bruto.encode()).hexdigest()
        cls.objects.create(usuario=usuario, token_hash=token_hash)
        return token_bruto

    @classmethod
    def verificar(cls, token_bruto):
        """Retorna a instância se válida e dentro do prazo, senão None."""
        from django.utils import timezone as tz
        import datetime
        token_hash = hashlib.sha256(token_bruto.encode()).hexdigest()
        try:
            inst = cls.objects.select_related('usuario').get(
                token_hash=token_hash, usado=False
            )
            limite = inst.criado_em + datetime.timedelta(minutes=cls.EXPIRACAO_MINUTOS)
            if tz.now() <= limite:
                return inst
        except cls.DoesNotExist:
            pass
        return None
