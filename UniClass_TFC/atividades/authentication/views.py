"""
Views de autenticação do UniClass
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from atividades.models import Usuario, Aluno, Professor, Diretor, PasswordResetToken
from .forms import LoginForm, CadastroUsuarioForm


@csrf_protect
@never_cache
def login_view(request):
    """
    View de login com validação de domínio acadêmico
    """
    # Se usuário já está autenticado, redireciona para dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha']

            # Autentica usando o backend customizado
            user = authenticate(request, username=email, password=senha)

            if user is not None:
                # Login bem-sucedido
                try:
                    auth_login(request, user, backend='atividades.authentication.backends.UniClassAuthBackend')
                except Exception:
                    # Fallback: sessão manual para modelo Usuario customizado
                    from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
                    request.session[SESSION_KEY] = str(user.id_usuario)
                    request.session[BACKEND_SESSION_KEY] = 'atividades.authentication.backends.UniClassAuthBackend'
                    request.session[HASH_SESSION_KEY] = user.get_session_auth_hash()
                    request.session.modified = True

                # Configura duração da sessão
                session_duration = form.get_session_duration()
                if session_duration == 0:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(session_duration)

                # Mensagem de sucesso
                messages.success(request, f'Bem-vindo(a), {user.email}!')

                # Redireciona para página solicitada ou dashboard
                next_url = request.GET.get('next', 'dashboard:index')
                return redirect(next_url)
            else:
                # Credenciais inválidas
                messages.error(request, 'Email ou senha incorretos.')
        else:
            # Erros de validação do form
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = LoginForm()

    context = {
        'form': form,
        'title': 'Login - UniClass',
    }

    return render(request, 'authentication/login.html', context)


@login_required(login_url='login')
def logout_view(request):
    """
    View de logout
    """
    auth_logout(request)
    messages.success(request, 'Você saiu do sistema com sucesso.')
    return redirect('authentication:login')


@csrf_protect
@never_cache
def cadastro_view(request):
    """
    View de cadastro de novo usuário
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            senha = form.cleaned_data['senha']
            tipo_usuario = form.cleaned_data['tipo_usuario']

            # Verifica se email já cadastrado
            if Usuario.objects.filter(email=email).exists():
                messages.error(request, 'Este email já está cadastrado.')
            else:
                # Cria o usuário
                user = Usuario(email=email, tipo_usuario=tipo_usuario)
                user.set_password(senha)
                user.save()

                # Cria o perfil vinculado
                nome = form.cleaned_data.get('nome', '').strip()
                sobrenome = form.cleaned_data.get('sobrenome', '').strip()
                curso = form.cleaned_data.get('curso', '').strip()

                if tipo_usuario == 'aluno':
                    Aluno.objects.create(
                        id_aluno=user,
                        nome_aluno=nome,
                        sobrenome_aluno=sobrenome,
                        curso_aluno=curso,
                        periodo=form.cleaned_data.get('periodo', '').strip(),
                        matricula_aluno=form.cleaned_data.get('matricula', '').strip(),
                    )
                elif tipo_usuario == 'professor':
                    Professor.objects.create(
                        id_professor=user,
                        nome_professor=nome,
                        sobrenome_professor=sobrenome,
                        curso_professor=curso,
                    )
                elif tipo_usuario == 'diretor':
                    # Diretores são criados pelo Admin via painel dedicado (curso obrigatório).
                    # Aqui apenas cria o usuário base; o perfil é vinculado pelo Admin.
                    pass

                messages.success(request, 'Conta criada com sucesso! Faça o login.')
                return redirect('authentication:login')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = CadastroUsuarioForm()

    context = {
        'form': form,
        'title': 'Cadastro - UniClass',
    }

    return render(request, 'authentication/cadastro.html', context)


@csrf_protect
@never_cache
def solicitar_reset_view(request):
    """
    Recuperação de senha — etapa 1 (RF002, fluxo "Esqueceu a senha").
    O usuário informa o e-mail e recebe um link válido por 60 minutos.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if not email:
            messages.error(request, 'Informe o e-mail cadastrado.')
            return render(request, 'authentication/solicitar_reset.html', {'title': 'Recuperar senha - UniClass'})

        usuario = Usuario.objects.filter(email=email).first()
        if usuario:
            token = PasswordResetToken.criar_para(usuario)
            link = request.build_absolute_uri(reverse('authentication:confirmar_reset', args=[token]))
            mensagem = (
                'Olá,\n\n'
                'Recebemos um pedido para redefinir a sua senha no UniClass.\n'
                'Para criar uma nova senha, acesse o link abaixo '
                f'(válido por {PasswordResetToken.EXPIRACAO_MINUTOS} minutos):\n\n'
                f'{link}\n\n'
                'Se você não fez esse pedido, ignore este e-mail.\n\n'
                'UniClass — Sistema de Atividades Domiciliares'
            )
            try:
                send_mail(
                    'UniClass — Redefinição de senha',
                    mensagem,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    [usuario.email],
                    fail_silently=False,
                )
            except Exception:
                messages.error(request, 'Não foi possível enviar o e-mail agora. Tente novamente em alguns minutos.')
                return render(request, 'authentication/solicitar_reset.html', {'title': 'Recuperar senha - UniClass'})

        # Mesma mensagem para e-mail existente ou não (evita descobrir e-mails cadastrados)
        messages.success(
            request,
            'Se o e-mail estiver cadastrado, você receberá um link para criar uma nova senha.'
        )
        return redirect('authentication:login')

    return render(request, 'authentication/solicitar_reset.html', {'title': 'Recuperar senha - UniClass'})


@csrf_protect
@never_cache
def confirmar_reset_view(request, token):
    """
    Recuperação de senha — etapa 2: o usuário abre o link recebido e define a nova senha.
    """
    registro = PasswordResetToken.verificar(token)
    if registro is None:
        messages.error(request, 'Link inválido ou expirado. Solicite um novo link de redefinição.')
        return redirect('authentication:solicitar_reset')

    if request.method == 'POST':
        senha = request.POST.get('senha', '')
        confirmar = request.POST.get('confirmar_senha', '')
        if len(senha) < 8:
            messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
        elif senha != confirmar:
            messages.error(request, 'As senhas não coincidem.')
        else:
            usuario = registro.usuario
            usuario.set_password(senha)
            usuario.save(update_fields=['senha'])
            registro.usado = True
            registro.save(update_fields=['usado'])
            messages.success(request, 'Senha redefinida com sucesso! Faça o login com a nova senha.')
            return redirect('authentication:login')

    return render(request, 'authentication/confirmar_reset.html', {'title': 'Nova senha - UniClass'})
