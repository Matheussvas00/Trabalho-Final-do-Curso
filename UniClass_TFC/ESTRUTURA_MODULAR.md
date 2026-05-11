# Estrutura Modular do Projeto UniClass

## Visão Geral

O projeto foi reorganizado em uma estrutura modular, separando funcionalidades em pacotes dedicados:

```
UniClass_TFC/
├── manage.py                    # Django CLI com patches MySQL 5.6
├── db.sqlite3                   # (não usado - usando MySQL)
├── requirements.txt             # Dependências do projeto
├── .env                         # Variáveis de ambiente (DB credentials)
│
├── UniCLass/                    # Configurações do projeto
│   ├── __init__.py
│   ├── settings.py              # Configurações Django
│   ├── urls.py                  # URLs principais
│   ├── wsgi.py
│   ├── asgi.py
│   └── mysql_compat.py          # Patches de compatibilidade MySQL
│
├── atividades/                  # App principal (modular)
│   ├── __init__.py
│   ├── admin.py                 # Registro de models no admin
│   ├── apps.py
│   ├── models.py                # Todos os 13 models do banco
│   ├── urls.py                  # URLs principais (inclui módulos)
│   ├── tests.py
│   │
│   ├── authentication/          # Módulo de autenticação
│   │   ├── __init__.py
│   │   ├── backends.py          # UniClassAuthBackend + validações
│   │   ├── forms.py             # LoginForm, CadastroUsuarioForm
│   │   ├── views.py             # login_view, logout_view
│   │   ├── urls.py              # URLs: login/, logout/
│   │   └── templates/
│   │       └── authentication/
│   │           └── login.html   # Template de login
│   │
│   ├── dashboard/               # Módulo de dashboards
│   │   ├── __init__.py
│   │   ├── views.py             # dashboard_view (roteamento)
│   │   ├── urls.py              # URLs: dashboard/
│   │   └── templates/
│   │       └── dashboard/
│   │           ├── index.html   # Dashboard genérico
│   │           ├── aluno.html
│   │           ├── professor.html
│   │           └── diretor.html
│   │
│   ├── core/                    # Módulo core (para futuras funcionalidades compartilhadas)
│   │   ├── __init__.py
│   │   └── templates/
│   │       └── core/
│   │
│   └── templates/               # Templates globais
│       └── base.html            # Template base (compartilhado)
│
└── static/                      # Arquivos estáticos
    ├── css/
    │   └── styles.css           # Estilos globais
    └── js/
        └── scripts.js           # JavaScript global
```

## Módulos

### 1. **authentication/** - Autenticação

**Responsabilidade**: Gerenciar login, logout e validação de emails acadêmicos.

**Arquivos**:

- `backends.py`:
  - `UniClassAuthBackend` - Backend customizado usando modelo `Usuario`
  - `validar_email_academico()` - Valida domínios @academico.unirv.edu.br e @unirv.edu.br
  - `detectar_tipo_usuario_por_email()` - Detecta tipo de usuário pelo domínio

- `forms.py`:
  - `LoginForm` - Formulário de login com validação de domínio
  - `CadastroUsuarioForm` - Formulário de cadastro (para uso futuro)

- `views.py`:
  - `login_view` - Autentica usuário e configura sessão
  - `logout_view` - Encerra sessão do usuário

- `urls.py`:
  - `authentication:login` → `/login/`
  - `authentication:logout` → `/logout/`

**Templates**:

- `authentication/login.html` - Página de login

---

### 2. **dashboard/** - Dashboards

**Responsabilidade**: Gerenciar dashboards específicos por tipo de usuário.

**Arquivos**:

- `views.py`:
  - `dashboard_view` - Roteia para dashboard específico baseado em `user.tipo_usuario`

- `urls.py`:
  - `dashboard:index` → `/dashboard/`

**Templates**:

- `dashboard/aluno.html` - Dashboard do aluno
- `dashboard/professor.html` - Dashboard do professor
- `dashboard/diretor.html` - Dashboard do diretor
- `dashboard/index.html` - Dashboard genérico (fallback)

---

### 3. **core/** - Funcionalidades Compartilhadas

**Responsabilidade**: Utilitários, mixins, decorators e outras funcionalidades compartilhadas (para uso futuro).

---

## Configurações Importantes

### settings.py

```python
# Backend de autenticação customizado
AUTHENTICATION_BACKENDS = [
    'atividades.authentication.backends.UniClassAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# URLs de autenticação
LOGIN_URL = 'authentication:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
```

### URLs Principais (atividades/urls.py)

```python
urlpatterns = [
    path('', include('atividades.authentication.urls')),      # Login/logout
    path('dashboard/', include('atividades.dashboard.urls')), # Dashboards
]
```

## Fluxo de Autenticação

1. **Acesso à aplicação** → Redireciona para `authentication:login`
2. **Usuário insere email e senha** → `LoginForm` valida domínio acadêmico
3. **Validação bem-sucedida** → `UniClassAuthBackend` autentica usando `Usuario`
4. **Login** → Django cria sessão e redireciona para `dashboard:index`
5. **Dashboard** → `dashboard_view` roteia para template específico baseado em `tipo_usuario`

## Próximos Passos (Módulos Futuros)

### 4. atestados/

- Submissão de atestados
- Aprovação por professores/diretores
- Histórico de atestados

### 5. atividades/

- Criação de atividades domiciliares (professores)
- Submissão de respostas (alunos)
- Correção e feedback

### 6. notificacoes/

- Sistema de notificações em tempo real
- Alertas de prazos
- Comunicados gerais

## Vantagens da Estrutura Modular

✅ **Organização**: Cada funcionalidade tem seu próprio pacote  
✅ **Manutenibilidade**: Fácil localizar e editar código específico  
✅ **Escalabilidade**: Simples adicionar novos módulos sem afetar existentes  
✅ **Testabilidade**: Testes podem ser organizados por módulo  
✅ **Colaboração**: Múltiplos desenvolvedores podem trabalhar em módulos diferentes  
✅ **Reusabilidade**: Templates e código podem ser compartilhados via `core/`

## Como Adicionar Novo Módulo

1. **Criar estrutura**:

```bash
mkdir atividades/novo_modulo
mkdir atividades/novo_modulo/templates/novo_modulo
```

2. **Criar arquivos base**:

```python
# atividades/novo_modulo/__init__.py
"""Módulo de funcionalidade X"""

# atividades/novo_modulo/views.py
from django.shortcuts import render

# atividades/novo_modulo/urls.py
from django.urls import path
from . import views

app_name = 'novo_modulo'
urlpatterns = []
```

3. **Registrar URLs**:

```python
# atividades/urls.py
path('novo-modulo/', include('atividades.novo_modulo.urls')),
```

## Comandos Úteis

```bash
# Verificar estrutura do projeto
python manage.py check

# Iniciar servidor
python manage.py runserver

# Criar usuário de teste
python manage.py shell
>>> from atividades.models import Usuario
>>> from django.contrib.auth.hashers import make_password
>>> user = Usuario.objects.create(
...     email='aluno@academico.unirv.edu.br',
...     senha=make_password('senha123'),
...     tipo_usuario='aluno',
...     status_usuario='ativo'
... )
```
