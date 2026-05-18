"""Script de teste completo do sistema UniClass"""
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'UniCLass.settings'
django.setup()

from django.test import Client
from atividades.models import (
    Usuario, Aluno, Professor, Diretor, Atividade,
    RespostaAtividade, Portaria, Notificacao, Historico, Disciplina
)

OK = "[OK]"
FAIL = "[FAIL]"

def check(cond, msg):
    print(f"  {OK if cond else FAIL} {msg}")
    return cond

def make_client():
    return Client(SERVER_NAME='127.0.0.1')

print("\n" + "="*60)
print("  TESTE COMPLETO — UNICLASS")
print("="*60)

# ─── ESTADO DO BANCO ───────────────────────────────────────
print("\n[1] ESTADO DO BANCO DE DADOS")
usuarios = Usuario.objects.all()
check(usuarios.filter(tipo_usuario='admin').exists(), f"Admin existe")
check(usuarios.filter(tipo_usuario='diretor').exists(), f"Diretor existe")
check(usuarios.filter(tipo_usuario='professor').exists(), f"Professor existe")
check(usuarios.filter(tipo_usuario='aluno').exists(), f"Aluno(s) existe(m)")

atividades = Atividade.objects.all()
check(atividades.exists(), f"Atividades cadastradas: {atividades.count()}")
for a in atividades:
    check(a.status in ['aguardando_resposta','pendente','concluida','inativa'],
          f"Status da atividade '{a.titulo}': {a.status}")

respostas = RespostaAtividade.objects.all()
check(respostas.exists(), f"Respostas cadastradas: {respostas.count()}")
for r in respostas:
    status_validos_prof = ['pendente','aprovada','rejeitada']
    status_validos_dir  = ['pendente','aprovada','rejeitada']
    status_validos_geral = ['pendente','aprovada','rejeitada','aprovada_diretor','rejeitada_diretor']
    check(r.status_professor in status_validos_prof,
          f"Resposta '{r.id_atividade.titulo}' status_professor={r.status_professor}")
    check(r.status_diretor in status_validos_dir,
          f"Resposta '{r.id_atividade.titulo}' status_diretor={r.status_diretor}")
    check(r.status in status_validos_geral,
          f"Resposta '{r.id_atividade.titulo}' status_geral={r.status}")

portarias = Portaria.objects.all()
check(portarias.exists(), f"Portarias cadastradas: {portarias.count()}")
for p in portarias:
    check(p.status in ['aguardando_atividades','em_andamento','concluida','inativa'],
          f"Portaria {p.numero_portaria} status={p.status}")

notifs = Notificacao.objects.all()
print(f"  ℹ️  Notificações: {notifs.count()} (lidas={notifs.filter(lida=True).count()}, não lidas={notifs.filter(lida=False).count()})")

historico_count = Historico.objects.count()
print(f"  ℹ️  Histórico: {historico_count} registros")

# ─── LOGIN ─────────────────────────────────────────────────
print("\n[2] TESTE DE LOGIN")
credenciais = [
    ('admin@unirv.edu.br', 'Admin@1234', 'admin'),
    ('diretor@unirv.edu.br', 'Diretor@1234', 'diretor'),
    ('professor@unirv.edu.br', 'Prof@1234', 'professor'),
    ('_inativo_5_aluno@academico.unirv.edu.br', 'Aluno@1234', 'aluno'),
]
clients = {}
for email, senha, tipo in credenciais:
    c = make_client()
    resp = c.post('/login/', {'email': email, 'senha': senha})
    ok = resp.status_code in [200, 302]
    redirect = resp.get('Location','')
    logged = '/dashboard' in redirect or resp.status_code == 302
    check(logged, f"Login {tipo} ({email}) → {redirect or resp.status_code}")
    clients[tipo] = c

# ─── PÁGINAS DO PROFESSOR ──────────────────────────────────
print("\n[3] PÁGINAS DO PROFESSOR")
cp = clients.get('professor', make_client())
cp.post('/login/', {'email': 'professor@unirv.edu.br', 'senha': 'Prof@1234'})
pages_prof = [
    ('/dashboard/', 'Dashboard professor'),
    ('/dashboard/professor/atividades/', 'Gerenciar atividades'),
    ('/dashboard/professor/portarias/', 'Portarias professor'),
    ('/dashboard/professor/validar/', 'Validar respostas'),
    ('/dashboard/notificacoes/', 'Notificações professor'),
]
for url, nome in pages_prof:
    r = cp.get(url)
    check(r.status_code == 200, f"{nome} ({url}) → {r.status_code}")

# ─── PÁGINAS DO DIRETOR ────────────────────────────────────
print("\n[4] PÁGINAS DO DIRETOR")
cd = clients.get('diretor', make_client())
cd.post('/login/', {'email': 'diretor@unirv.edu.br', 'senha': 'Diretor@1234'})
pages_dir = [
    ('/dashboard/', 'Dashboard diretor'),
    ('/dashboard/gerenciar/alunos/', 'Gerenciar alunos'),
    ('/dashboard/gerenciar/professores/', 'Gerenciar professores'),
    ('/dashboard/gerenciar/portarias/', 'Gerenciar portarias'),
    ('/dashboard/gerenciar/validacoes/', 'Validar atividades'),
    ('/dashboard/historico/', 'Histórico sistema'),
    ('/dashboard/notificacoes/', 'Notificações diretor'),
]
for url, nome in pages_dir:
    r = cd.get(url)
    check(r.status_code == 200, f"{nome} ({url}) → {r.status_code}")

# ─── PÁGINAS DO ALUNO ──────────────────────────────────────
print("\n[5] PÁGINAS DO ALUNO")
ca = clients.get('aluno', make_client())
ca.post('/login/', {'email': '_inativo_5_aluno@academico.unirv.edu.br', 'senha': 'Aluno@1234'})
pages_aluno = [
    ('/dashboard/', 'Dashboard aluno'),
    ('/dashboard/aluno/portarias/', 'Portarias aluno'),
    ('/dashboard/aluno/atividades/', 'Atividades aluno'),
    ('/dashboard/aluno/disciplinas/', 'Disciplinas aluno'),
    ('/dashboard/aluno/respostas/', 'Respostas aluno'),
    ('/dashboard/notificacoes/', 'Notificações aluno'),
]
for url, nome in pages_aluno:
    r = ca.get(url)
    check(r.status_code == 200, f"{nome} ({url}) → {r.status_code}")

# ─── PÁGINAS DO ADMIN ──────────────────────────────────────
print("\n[6] PÁGINAS DO ADMIN")
cadm = clients.get('admin', make_client())
cadm.post('/login/', {'email': 'admin@unirv.edu.br', 'senha': 'Admin@1234'})
pages_admin = [
    ('/dashboard/', 'Dashboard admin'),
    ('/dashboard/admin/diretores/', 'Gerenciar diretores'),
    ('/dashboard/admin/cursos/', 'Gerenciar cursos'),
    ('/dashboard/admin/disciplinas/', 'Gerenciar disciplinas'),
    ('/dashboard/historico/', 'Histórico admin'),
    ('/dashboard/notificacoes/', 'Notificações admin'),
]
for url, nome in pages_admin:
    r = cadm.get(url)
    check(r.status_code == 200, f"{nome} ({url}) → {r.status_code}")

# ─── VALIDAÇÃO EMAIL ALUNO ─────────────────────────────────
print("\n[7] VALIDAÇÃO DE EMAIL NO CADASTRO DE ALUNO")
cd2 = make_client()
cd2.post('/login/', {'email': 'diretor@unirv.edu.br', 'senha': 'Diretor@1234'})
# Email inválido (não @academico)
r_inv = cd2.post('/dashboard/gerenciar/alunos/cadastrar/', {
    'nome_aluno': 'Teste', 'sobrenome_aluno': 'Invalido',
    'periodo': '1', 'matricula_aluno': 'MAT9999',
    'email': 'invalido@gmail.com', 'senha': 'Senha@1234',
    'disciplinas': []
}, follow=True)
def get_messages(resp):
    from django.contrib.messages import get_messages as _gm
    return [str(m) for m in _gm(resp.wsgi_request)]
msgs_inv = get_messages(r_inv)
check(any('academico' in m.lower() or 'dom' in m.lower() for m in msgs_inv),
      f"Rejeita email @gmail.com: {msgs_inv}")

# Email válido (@academico)
r_val = cd2.post('/dashboard/gerenciar/alunos/cadastrar/', {
    'nome_aluno': 'Teste', 'sobrenome_aluno': 'Valido',
    'periodo': '1', 'matricula_aluno': 'MAT8888',
    'email': 'teste.valido@academico.unirv.edu.br', 'senha': 'Senha@1234',
    'disciplinas': []
}, follow=True)
msgs_val = get_messages(r_val)
# Pode falhar por falta de disciplinas, mas não por email
email_ok = not any('academico' in m.lower() or 'dom' in m.lower() for m in msgs_val)
check(email_ok, f"Aceita email @academico.unirv.edu.br: {msgs_val}")

# ─── FLUXO DE STATUS DE ATIVIDADE ─────────────────────────
print("\n[8] STATUS DAS RESPOSTAS DE ATIVIDADE")
for r in RespostaAtividade.objects.all():
    print(f"  ℹ️  '{r.id_atividade.titulo}':")
    print(f"       Professor={r.status_professor} | Diretor={r.status_diretor} | Geral={r.status}")
    # Lógica: se prof=aprovada e dir=aprovada -> geral=aprovada_diretor
    if r.status_professor == 'aprovada' and r.status_diretor == 'aprovada':
        check(r.status == 'aprovada_diretor',
              f"Fluxo correto: prof aprovada + dir aprovada → geral=aprovada_diretor")
    elif r.status_professor == 'rejeitada':
        check(r.status in ['rejeitada','rejeitada_diretor'],
              f"Fluxo correto: prof rejeitada → geral rejeitada")

print("\n" + "="*60)
print("  FIM DOS TESTES")
print("="*60 + "\n")
