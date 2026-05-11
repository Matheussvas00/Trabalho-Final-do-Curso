# Guia de Contribuição — UniClass

## Estratégia de Branches (Git Flow Simplificado)

```
main          ← código estável, pronto para entrega/produção
  └── develop ← integração de features
        ├── feature/nome-da-feature   ← desenvolvimento de novas funcionalidades
        ├── fix/nome-do-bug           ← correção de bugs
        └── hotfix/nome-do-hotfix     ← correções urgentes em produção
```

### Regras
- **Nunca** commitar diretamente em `main`
- Todo desenvolvimento acontece em branches a partir de `develop`
- Nomes de branch em minúsculas com hífens: `feature/validacao-email`

---

## Padrão de Commits (Conventional Commits)

Formato: `<tipo>(escopo opcional): descrição curta`

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `test` | Adição ou correção de testes |
| `refactor` | Refatoração sem mudança de comportamento |
| `docs` | Documentação |
| `style` | Formatação, espaços, etc. (sem lógica) |
| `chore` | Configurações, dependências |

### Exemplos
```bash
git commit -m "feat(auth): adicionar validação de domínio de e-mail por tipo de usuário"
git commit -m "fix(portaria): corrigir validação de ordem de prazos"
git commit -m "test(models): adicionar testes unitários de RespostaAtividade"
git commit -m "docs: atualizar CHANGELOG para v1.1.0"
git commit -m "refactor(views): extrair lógica de validação para camada de serviço"
git commit -m "style: remover espaços em branco em linhas vazias"
git commit -m "chore: adicionar flake8 e pytest ao requirements-dev.txt"
```

---

## Como Executar os Testes

```bash
cd UniClass_TFC

# Testes unitários (Django TestCase)
python manage.py test atividades -v 2

# Com pytest (requer pytest.ini configurado)
pytest atividades/tests.py -v

# Com cobertura de código
pytest atividades/tests.py --cov=atividades --cov-report=term-missing
```

## Análise Estática (Flake8)

```bash
cd UniClass_TFC
flake8 atividades/ --exclude=atividades/migrations/
```

---

## Versionamento Semântico (SemVer)

Versão: `MAJOR.MINOR.PATCH`

- **MAJOR**: mudança incompatível (ex: nova arquitetura de banco)
- **MINOR**: nova funcionalidade compatível (ex: novo RF implementado)  
- **PATCH**: correção de bug compatível (ex: fix em validação)

Criar tag de versão:
```bash
git tag -a v1.1.0 -m "Release v1.1.0: testes unitários e análise estática"
git push origin v1.1.0
```
