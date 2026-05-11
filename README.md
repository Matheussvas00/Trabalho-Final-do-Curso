# UniClass — Gestão de Atividades Domiciliares (RED)

Sistema web desenvolvido em Django para automatizar o Regime de Exercícios Domiciliares (RED) da Universidade de Rio Verde (UniRV).

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.13, Django 6.0.1 |
| Banco de dados | MySQL 8.x |
| Driver MySQL | PyMySQL 1.1.0 |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5 |
| Auth | Backend customizado (UniClassAuthBackend) |
| Testes | Django TestCase, pytest |
| Análise estática | Flake8 |

## Pré-requisitos

- Python 3.11+
- MySQL 8.0+
- pip

## Instalação (ambiente de desenvolvimento)

```bash
# 1. Clone o repositório
git clone https://github.com/Matheussvas00/Trabalho-Final-do-Curso.git
cd Trabalho-Final-do-Curso/UniClass_TFC

# 2. Instale as dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt  # testes e linting

# 3. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais MySQL

# 4. Aplique as migrations
python manage.py migrate

# 5. Crie um admin inicial
python manage.py criar_admin

# 6. Execute o servidor
python manage.py runserver
```

## Configuração do banco de dados (.env)

```env
SECRET_KEY=sua-chave-secreta
DEBUG=True
DB_NAME=uniclass
DB_USER=root
DB_PASSWORD=sua-senha
DB_HOST=localhost
DB_PORT=3306
```

## Executar testes

```bash
# Testes unitários
python manage.py test atividades -v 2

# Com cobertura
pytest atividades/tests.py --cov=atividades --cov-report=term-missing
```

## Análise estática

```bash
flake8 atividades/ --exclude=atividades/migrations/
```

## Perfis de usuário

| Perfil | E-mail | Funcionalidades |
|--------|--------|-----------------|
| Aluno | `@academico.unirv.edu.br` | Visualizar e responder atividades |
| Professor | `@unirv.edu.br` | Criar e validar atividades |
| Diretor | `@unirv.edu.br` | Gerenciar portarias, usuários, validação final |
| Admin | Qualquer | Acesso completo (gestão do sistema) |

## Estrutura do projeto

```
UniClass_TFC/
├── UniCLass/               # Configurações do projeto Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── atividades/             # App principal
│   ├── models.py           # Entidades do sistema
│   ├── tests.py            # Testes unitários (42 testes)
│   ├── authentication/     # Login, cadastro, recuperação de senha
│   │   ├── backends.py     # UniClassAuthBackend
│   │   ├── forms.py
│   │   └── views.py
│   ├── dashboard/          # Painéis por perfil
│   │   └── views/
│   │       ├── aluno.py
│   │       ├── professor.py
│   │       ├── diretor.py
│   │       └── administrador.py
│   └── migrations/
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── .flake8
```

## Contribuição

Consulte [CONTRIBUTING.md](../CONTRIBUTING.md) para o guia de versionamento e padrão de commits.

## Versão atual

**v1.1.0** — Veja o [CHANGELOG](../CHANGELOG.md) para o histórico completo.

---

*Trabalho Final de Curso — Engenharia de Software — UniRV (2026)*  
*Autor: Matheus Silva Vasconcelos*  
*Orientador: Prof. Me. João Dionísio Paraíba*
