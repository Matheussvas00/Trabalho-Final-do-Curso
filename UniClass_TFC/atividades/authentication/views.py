"""
Views de autenticação do UniClass
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from atividades.models import Usuario, Aluno, Professor, Diretor
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


def solicitar_reset_view(request):
    """Mantida apenas para compatibilidade de URL — redireciona para o login."""
    return redirect('authentication:login')


def confirmar_reset_view(request, token):
    """Mantida apenas para compatibilidade de URL — redireciona para o login."""
    return redirect('authentication:login')
