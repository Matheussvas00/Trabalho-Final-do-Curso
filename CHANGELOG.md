# Changelog — UniClass

Todas as mudanças notáveis deste projeto estão documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).

---

## [1.1.0] — 2026-05-11

### Adicionado
- Testes unitários completos (42 testes) cobrindo: Usuario, Aluno, Professor,
  Diretor, Disciplina, Portaria, Atividade, RespostaAtividade, PasswordResetToken,
  backend de autenticação e validação de e-mail (`atividades/tests.py`)
- Arquivo de configuração de testes `pytest.ini`
- Dependências de desenvolvimento `requirements-dev.txt` (pytest, flake8, coverage)
- Configuração de análise estática `.flake8`
- Estratégia de versionamento Git (`CONTRIBUTING.md`, branch strategy)

### Corrigido
- Remoção de espaços em branco em linhas vazias em todos os arquivos Python
  (146 ocorrências de W293/W291 eliminadas)

---

## [1.0.0] — 2026-05-07

### Adicionado
- RF001 — Manter Usuário: cadastro, listagem, edição e inativação
  de alunos, professores e diretores
- RF002 — Realizar Login: autenticação com e-mail institucional
  (domínio @academico.unirv.edu.br para alunos / @unirv.edu.br para staff)
  e senha; sessão persistente com "Lembrar-me"; fluxo de recuperação de senha
  com token SHA-256
- RF003 — Manter Disciplina: cadastro, listagem, edição e exclusão
  de disciplinas vinculadas a cursos e professores
- RF004 — Manter Portaria: cadastro de portarias com upload de atestado,
  prazos hierárquicos (criar atividades → responder → validação final)
  e validação de vínculo aluno-diretor por curso
- RF005 — Manter Atividade: criação e gestão de atividades domiciliares
  com validação de prazos em relação à portaria e vínculo professor-disciplina
- RF006 — Enviar Resposta de Atividade: upload de resposta pelo aluno
  com atualização automática de status
- RF007 — Validar Atividade: fluxo de dupla validação (professor → diretor)
  com estados distintos por etapa
- Backend de autenticação customizado (`UniClassAuthBackend`) com proteção
  contra timing attacks
- Modelos: Usuario, Curso, Aluno, Professor, Diretor, Admin, Disciplina,
  ProfessorDisciplina, AlunoDisciplina, Portaria, PortariaDisciplina,
  Atividade, RespostaAtividade, Notificacao, Historico, PasswordResetToken
- Painéis separados por perfil: Aluno, Professor, Diretor, Admin
- Identidade visual UniClass (logo e paleta de cores)
- Suporte a variáveis de ambiente via python-dotenv

---

## [0.2.0] — 2026-04-15 (desenvolvimento iterativo)

### Adicionado
- Telas de Aluno: listagem de atividades, visualização de portarias,
  envio de respostas, visualização de respostas
- Telas de Professor: gerenciamento de atividades, validação de respostas
- Telas de Diretor: gerenciamento de portarias, usuários, disciplinas,
  validações finais
- Perfil Admin com acesso completo ao sistema

---

## [0.1.0] — 2026-03-01 (bootstrap)

### Adicionado
- Estrutura inicial do projeto Django 6.0.1
- Modelos base: Usuario, Curso, Aluno, Professor, Diretor
- Tela de login e cadastro
- Configuração do banco de dados MySQL via PyMySQL

---

## [1.2.0] — 2026-05-11

### Corrigido
- **Bug crítico**: cadastro de Diretor via form público quebrava com `ValueError`
  porque `curso_fk` (NOT NULL) não era enviado pelo formulário.
  Diretores agora são criados exclusivamente via painel do Admin.
- `elif tipo_usuario == 'admin'` órfão removido do `cadastro_view`
- S3 configurado apenas para arquivos de media (não estáticos),
  evitando conflito com whitenoise

### Adicionado
- `whitenoise.middleware.WhiteNoiseMiddleware` no MIDDLEWARE (produção)
- `CompressedManifestStaticFilesStorage` para assets com cache busting
- `CSRF_TRUSTED_ORIGINS` gerado automaticamente a partir de `ALLOWED_HOSTS`
- `Procfile` para Railway (gunicorn + migrate + collectstatic)
- `runtime.txt` (python-3.13.0)
- `nixpacks.toml` com `libmysqlclient` para build no Railway
- `.env.example` completo com variáveis Railway, S3 e SMTP
