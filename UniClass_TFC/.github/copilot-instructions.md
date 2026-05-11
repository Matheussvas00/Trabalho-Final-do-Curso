# UniClass - Sistema de Gerenciamento de Atividades Domiciliares

## Visão Geral do Projeto

Sistema web Django 6.0 para gerenciamento de **atividades domiciliares** para alunos com **atestados médicos**. Permite que professores criem atividades compensatórias para alunos afastados, e acompanhem as respostas enviadas pelos alunos.

**Tecnologias:**

- Python 3.13.2 + Django 6.0.1
- MySQL 5.6 (via PyMySQL com patches de compatibilidade)
- Preparado para deploy em AWS

## Arquitetura do Sistema

### Fluxo Principal

1. **Aluno submete atestado médico** → Status: pendente
2. **Diretor aprova/rejeita atestado**
3. **Professor cria atividades** para as disciplinas afetadas pelo atestado
4. **Aluno envia respostas** das atividades
5. **Professor avalia respostas** (aprovada/rejeitada)

### Estrutura do Banco de Dados

**Entidades Principais:**

- **`usuario`** - Base de autenticação (diretor, professor, aluno)
  - Tipos: diretor, professor, aluno
  - Campos: email, senha (hash), tipo_usuario
- **`aluno`** - Dados dos alunos
  - Separado de `usuario` (não possui FK direta - design legado)
  - Campos: nome, sobrenome, matrícula, curso, período
- **`professor`** / **`diretor`** - Dados de professores e diretores
  - FK para `usuario` (OneToOne)
- **`curso`** - Cursos da faculdade
- **`disciplina`** - Disciplinas
  - FK: professor, curso
- **`aluno_disciplina`** - Matrícula (ManyToMany aluno ↔ disciplina)

- **`atestado`** - Atestados médicos
  - FK: aluno
  - Status: pendente, aprovado, rejeitado
  - Campos: data_inicio, data_fim, CID, arquivo (path)
- **`atestado_disciplina`** - Disciplinas afetadas por atestado (ManyToMany)

- **`atividade`** - Atividades domiciliares
  - FK: atestado, disciplina, professor
  - Status: pendente, concluida
  - Campos: título, descrição, data_criacao, data_limite

- **`resposta_atividade`** - Respostas dos alunos
  - FK: atividade, aluno
  - Status: pendente, aprovada, rejeitada
  - Campos: arquivo, data_envio, observacao_professor

- **`notificacao`** - Notificações para usuários
  - FK: usuario (destino)
  - Campo: lida (boolean)

- **`historico`** - Log de ações dos usuários

### Models Django

Todos os models estão em [`atividades/models.py`](atividades/models.py) com:

- Configuração `db_table` para mapear tabelas existentes
- Properties úteis (`nome_completo`, `dias_afastamento`, `prazo_vencido`)
- Métodos `__str__` descritivos
- Related names consistentes

## Configuração Crítica - MySQL 5.6

⚠️ **IMPORTANTE:** Django 6.0 requer MySQL 8.0.11+, mas este projeto usa MySQL 5.6.

**Patches aplicados em [`manage.py`](manage.py):**

```python
# PyMySQL como substituto do MySQLdb
pymysql.install_as_MySQLdb()
pymysql.version_info = (2, 2, 1, "final", 0)

# Patch no check_database_version_supported
# Sobrescreve para aceitar MySQL 5.6+
```

**NÃO remover esses patches!** O projeto não funcionará sem eles.

## Workflows Essenciais

### Configuração Inicial

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar .env (DB: uniclass_tfc)
# Copiar .env.example para .env e preencher

# 3. Aplicar migrações Django (tabelas já existem)
python manage.py migrate

# 4. Criar superusuário
python manage.py createsuperuser

# 5. Rodar servidor
python manage.py runserver  # http://127.0.0.1:8000/
```

### Admin Django

Acesse `/admin/` para gerenciar todos os models:

- Configurado em [`atividades/admin.py`](atividades/admin.py)
- List displays otimizados para cada model
- Filtros e buscas configurados

### Variáveis de Ambiente ([`.env`](.env))

```bash
# Banco de Dados (OBRIGATÓRIO)
DB_NAME=uniclass_tfc      # Nome do banco MySQL
DB_USER=Matheus
DB_PASSWORD=553948
DB_HOST=127.0.0.1
DB_PORT=3306

# Django
SECRET_KEY=...            # Mudar em produção!
DEBUG=True               # False em produção
ALLOWED_HOSTS=           # Configurar em produção

# AWS (Produção)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
USE_S3=False             # True em produção
```

## Padrões do Projeto

### Idioma e Timezone

- **Idioma:** `pt-br`
- **Timezone:** `America/Sao_Paulo`

### Arquivos

- **Static:** `/static/` → `BASE_DIR / 'staticfiles'`
- **Media:** `/media/` → `BASE_DIR / 'media'` (uploads)

### Convenções de Código

- Models: Nomes em português matching banco existente
- Foreign Keys: Usar `related_name` descritivo
- Choices: TODAS_MAIÚSCULAS_CHOICES em models
- Properties: Para campos calculados (`@property`)

## Preparação para AWS

### Arquivos Importantes

- [`.env.production`](.env.production) - Template para produção
- [`settings.py`](UniCLass/settings.py) - Configuração S3 condicional

### Deploy Checklist

1. ✅ `DEBUG=False`
2. ✅ `ALLOWED_HOSTS` configurado
3. ✅ Nova `SECRET_KEY` (nunca commitada)
4. ✅ Migrar para RDS (MySQL 8+) ou manter 5.6 com patches
5. ✅ S3 para static/media: `USE_S3=True`
6. ✅ `collectstatic` executado
7. ✅ Gunicorn como WSGI server

## Comandos Úteis

```bash
# Desenvolvimento
python manage.py runserver
python manage.py shell

# Migrações
python manage.py migrate

# Admin
python manage.py createsuperuser

# Produção
python manage.py collectstatic
gunicorn UniCLass.wsgi:application
```

## Estrutura de Diretórios

```
UniClass_TFC/
├── manage.py               # Patches MySQL 5.6 aqui!
├── .env                    # Credenciais (NÃO commitado)
├── requirements.txt        # Dependências
├── UniCLass/              # Configuração
│   ├── settings.py        # Settings principal
│   ├── mysql_compat.py    # Patches compatibilidade
│   └── urls.py            # Rotas principais
└── atividades/            # App principal
    ├── models.py          # 13 models mapeando BD
    ├── admin.py           # Django admin config
    ├── views.py           # Views (a implementar)
    └── migrations/        # Migrações Django
```

## Observações Importantes

1. **Banco de dados já existe** - Models mapeiam tabelas existentes
2. **Não rodar makemigrations** sem necessidade - pode conflitar
3. **MySQL 5.6 não é oficialmente suportado** - patches são essenciais
4. **Aluno não tem FK para Usuario** - design legado, cuidado ao criar views
5. **Atestado é central** - atividades sempre ligadas a um atestado
6. **Status são ENUMs** - usar choices definidas nos models

# Criar admin

python manage.py createsuperuser

```

## Estrutura de Pastas Importante

```

UniClass_TFC/
├── .env # Credenciais (NÃO commitado)
├── .env.example # Template de configuração
├── manage.py # CLI Django
├── requirements.txt # Dependências Python
├── UniCLass/ # Configuração principal
│ ├── settings.py # Configurações (com variáveis de ambiente)
│ ├── urls.py # Rotas principais
│ └── wsgi.py # Entry point para produção
└── atividades/ # App de atividades domiciliares

```

## Notas de Segurança

- ✅ Credenciais no `.env` (não no código)
- ✅ `.gitignore` configurado para arquivos sensíveis
- ⚠️ Trocar `SECRET_KEY` antes do deploy em produção
- ⚠️ `DEBUG=False` em produção
- ⚠️ Configurar `ALLOWED_HOSTS` corretamente
```
