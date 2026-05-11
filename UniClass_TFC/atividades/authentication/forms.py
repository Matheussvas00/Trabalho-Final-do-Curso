"""
Formulários de autenticação do UniClass
"""
from django import forms
from django.core.exceptions import ValidationError
from .backends import validar_email_academico


class LoginForm(forms.Form):
    """
    Formulário de login com validação de domínio acadêmico
    """
    email = forms.EmailField(
        label='Email Acadêmico',
        max_length=150,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu.email@academico.unirv.edu.br',
            'autocomplete': 'email',
            'autofocus': True,
        })
    )

    senha = forms.CharField(
        label='Senha',
        max_length=150,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )

    lembrar_me = forms.BooleanField(
        label='Lembrar-me',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    def clean_email(self):
        """
        Valida se o email pertence ao domínio acadêmico
        """
        email = self.cleaned_data.get('email')

        if email:
            email = email.lower().strip()

            # Valida domínio acadêmico
            is_valid, error_msg = validar_email_academico(email)

            if not is_valid:
                raise ValidationError(error_msg)

        return email

    def get_session_duration(self):
        """
        Retorna duração da sessão baseado em 'lembrar_me'
        """
        if self.cleaned_data.get('lembrar_me'):
            # 30 dias
            return 30 * 24 * 60 * 60
        else:
            # Sessão expira ao fechar navegador
            return 0


class CadastroUsuarioForm(forms.Form):
    """
    Formulário de cadastro de usuário com dados do perfil
    """
    email = forms.EmailField(
        label='Email Acadêmico',
        max_length=150,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu.email@unirv.edu.br',
        })
    )

    senha = forms.CharField(
        label='Senha',
        max_length=150,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres',
        }),
        min_length=8,
        help_text='Mínimo 8 caracteres'
    )

    confirmar_senha = forms.CharField(
        label='Confirmar Senha',
        max_length=150,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a senha novamente',
        })
    )

    tipo_usuario = forms.ChoiceField(
        label='Tipo de Usuário',
        choices=[
            ('', 'Selecione...'),
            ('aluno', 'Aluno'),
            ('professor', 'Professor'),
            ('diretor', 'Diretor'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_tipo_usuario',
        })
    )

    # ── Campos do perfil (Aluno / Professor) ──
    nome = forms.CharField(
        label='Nome',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu nome',
        })
    )

    sobrenome = forms.CharField(
        label='Sobrenome',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu sobrenome',
        })
    )

    curso = forms.CharField(
        label='Curso',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Sistemas de Informação',
        })
    )

    periodo = forms.CharField(
        label='Período',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 8',
        })
    )

    matricula = forms.CharField(
        label='Matrícula',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua matrícula',
        })
    )

    def clean_email(self):
        """
        Valida email acadêmico
        """
        email = self.cleaned_data.get('email')
        tipo_usuario = self.data.get('tipo_usuario')

        if email:
            email = email.lower().strip()

            # Valida domínio baseado no tipo de usuário
            is_valid, error_msg = validar_email_academico(email, tipo_usuario)

            if not is_valid:
                raise ValidationError(error_msg)

        return email

    def clean(self):
        """
        Valida campos interdependentes
        """
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        tipo = cleaned_data.get('tipo_usuario')

        # Verifica se senhas coincidem
        if senha and confirmar_senha and senha != confirmar_senha:
            raise ValidationError('As senhas não coincidem')

        # Campos obrigatórios conforme o tipo
        if tipo in ('aluno', 'professor'):
            if not cleaned_data.get('nome', '').strip():
                self.add_error('nome', 'O nome é obrigatório.')
            if not cleaned_data.get('sobrenome', '').strip():
                self.add_error('sobrenome', 'O sobrenome é obrigatório.')
            if not cleaned_data.get('curso', '').strip():
                self.add_error('curso', 'O curso é obrigatório.')

        if tipo == 'aluno':
            if not cleaned_data.get('periodo', '').strip():
                self.add_error('periodo', 'O período é obrigatório.')
            if not cleaned_data.get('matricula', '').strip():
                self.add_error('matricula', 'A matrícula é obrigatória.')

        return cleaned_data
