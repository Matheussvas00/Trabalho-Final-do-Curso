"""
Backend de autenticação customizado para o UniClass
"""
from django.contrib.auth.backends import BaseBackend
from atividades.models import Usuario


class UniClassAuthBackend(BaseBackend):
    """
    Backend customizado que autentica usando o modelo Usuario
    ao invés do modelo User padrão do Django
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica usando email e senha

        Args:
            request: HttpRequest object
            username: Email do usuário (usado como username)
            password: Senha em texto plano

        Returns:
            Usuario instance se autenticado, None caso contrário
        """
        if username is None or password is None:
            return None

        try:
            # Busca usuário pelo email
            user = Usuario.objects.get(email=username.lower())

            # Verifica se a senha está correta
            if user.check_password(password):
                return user

        except Usuario.DoesNotExist:
            # Executa hasher para evitar timing attacks
            Usuario().set_password(password)
            return None

        return None

    def get_user(self, user_id):
        """
        Recupera usuário pelo ID para manter a sessão

        Args:
            user_id: ID do usuário

        Returns:
            Usuario instance ou None
        """
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None


def validar_email_academico(email, tipo_usuario=None):
    """
    Valida se o email pertence ao domínio acadêmico correto

    Args:
        email: Email a ser validado
        tipo_usuario: Tipo do usuário (aluno, professor, diretor)

    Returns:
        tuple: (is_valid, error_message)
    """
    if not email:
        return False, "Email é obrigatório"

    email = email.lower().strip()

    # Domínios válidos
    DOMINIO_ALUNO = "@academico.unirv.edu.br"
    DOMINIO_STAFF = "@unirv.edu.br"

    if tipo_usuario == 'aluno':
        if not email.endswith(DOMINIO_ALUNO):
            return False, f"Email de aluno deve terminar com {DOMINIO_ALUNO}"
        return True, None

    elif tipo_usuario in ['professor', 'diretor']:
        if not email.endswith(DOMINIO_STAFF):
            return False, f"Email de {tipo_usuario} deve terminar com {DOMINIO_STAFF}"
        return True, None

    else:
        # Se tipo não especificado, verifica se é algum domínio válido
        if email.endswith(DOMINIO_ALUNO) or email.endswith(DOMINIO_STAFF):
            return True, None
        return False, "Email deve ser do domínio @academico.unirv.edu.br (aluno) ou @unirv.edu.br (professor/diretor)"


def detectar_tipo_usuario_por_email(email):
    """
    Detecta o tipo de usuário baseado no domínio do email

    Args:
        email: Email do usuário

    Returns:
        str: 'aluno', 'professor' ou None se não puder detectar
    """
    if not email:
        return None

    email = email.lower().strip()

    if email.endswith("@academico.unirv.edu.br"):
        return 'aluno'
    elif email.endswith("@unirv.edu.br"):
        # Pode ser professor ou diretor, não dá para determinar só pelo email
        return 'staff'  # Retorna genérico

    return None
