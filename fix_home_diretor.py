"""Fix home_diretor.html: encoding corruption + inativar/reativar logic."""

file_path = (
    r'C:\Users\mathe\Desktop\TFC 2\Trabalho Final do Curso'
    r'\UniClass_TFC\atividades\dashboard\templates\dashboard\home_diretor.html'
)

with open(file_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

original_count = content.count('\ufffd')
print(f'Replacement chars before: {original_count}')

# ===================================================
# STEP 1: Encoding fixes — specific patterns first
# ===================================================

# Specific combined pattern (must come before single/double replacements)
content = content.replace('a\ufffd\ufffdo \ufffd irrevers', 'ação é irrevers')

# Double U+FFFD sequences
content = content.replace('Dire\ufffd\ufffdo', 'Direção')
content = content.replace('Notifica\ufffd\ufffdes', 'Notificações')
content = content.replace('VALIDA\ufffd\ufffdO', 'VALIDAÇÃO')
content = content.replace('Valida\ufffd\ufffdo', 'Validação')
content = content.replace('valida\ufffd\ufffdo', 'validação')
content = content.replace('Cria\ufffd\ufffdo', 'Criação')
content = content.replace('Altera\ufffd\ufffdes', 'Alterações')
content = content.replace('Observa\ufffd\ufffdes', 'Observações')
content = content.replace('Observa\ufffd\ufffdo', 'Observação')
content = content.replace('rejei\ufffd\ufffdo', 'rejeição')
content = content.replace('A\ufffd\ufffdo', 'Ação')
content = content.replace('a\ufffd\ufffdo', 'ação')

# Single U+FFFD sequences
content = content.replace('Matr\ufffdcula', 'Matrícula')
content = content.replace('Per\ufffdodo', 'Período')
content = content.replace('m\ufffdltiplas', 'múltiplas')
content = content.replace('M\ufffdnimo', 'Mínimo')
content = content.replace('atribu\ufffddo', 'atribuído')
content = content.replace('branco para n\ufffdo alterar', 'branco para não alterar')
content = content.replace('Conclu\ufffda', 'Concluída')
content = content.replace('irrevers\ufffdvel', 'irreversível')
content = content.replace('Exclus\ufffdo', 'Exclusão')
content = content.replace('Decis\ufffdo', 'Decisão')
content = content.replace('Coment\ufffdrio', 'Comentário')
content = content.replace('Voc\ufffd deve', 'Você deve')
content = content.replace('ser\ufffdo', 'serão')
content = content.replace('pluralize:"\ufffd,\ufffdo"', 'pluralize:"á,ão"')
content = content.replace('ser\ufffd{{ prof', 'será{{ prof')
content = content.replace('{{ aluno.periodo }}\ufffd</td>', '{{ aluno.periodo }}º</td>')
content = content.replace('&nbsp;\ufffd&nbsp;', '&nbsp;·&nbsp;')
content = content.replace('<span style="color:#999;">\ufffd</span>', '<span style="color:#999;">—</span>')

# Separator dashes in comments/labels
content = content.replace('Painel \ufffd Dire', 'Painel — Dire')
content = content.replace('MODAL \ufffd Cadastrar Aluno', 'MODAL — Cadastrar Aluno')
content = content.replace('MODAL \ufffd Cadastrar Professor', 'MODAL — Cadastrar Professor')
content = content.replace('MODAIS \ufffd Editar / Excluir ALUNOS', 'MODAIS — Editar / Excluir ALUNOS')
content = content.replace('MODAIS \ufffd Editar / Excluir PROFESSORES', 'MODAIS — Editar / Excluir PROFESSORES')
content = content.replace('MODAIS \ufffd Editar / Excluir PORTARIAS', 'MODAIS — Editar / Excluir PORTARIAS')
content = content.replace('MODAIS \ufffd Analisar', 'MODAIS — Analisar')
content = content.replace('\ufffd RESPOSTAS APROVADAS', '— RESPOSTAS APROVADAS')
content = content.replace('" \ufffd {{ p.id_alunofk.matricula_aluno }}', '" — {{ p.id_alunofk.matricula_aluno }}')
content = content.replace('Prazo \ufffd Criar', 'Prazo — Criar')
content = content.replace('Prazo \ufffd Respostas', 'Prazo — Respostas')
content = content.replace('Prazo \ufffd Valida', 'Prazo — Valida')
content = content.replace('Validar Resposta \ufffd {{ r', 'Validar Resposta — {{ r')
content = content.replace('} \ufffd Criada em', '} — Criada em')

remaining_after_encoding = content.count('\ufffd')
print(f'Replacement chars after encoding fix: {remaining_after_encoding}')

# ===================================================
# STEP 2: Aluno table — add Status column header
# ===================================================

old_aluno_header = (
    '                            <th style="text-align:left;">Matrícula</th>\n'
    '                            <th style="text-align:left;">Curso</th>\n'
    '                            <th style="text-align:center;">Per.</th>\n'
    '                            <th class="uc-th-actions">Ações</th>\n'
    '                        </tr>'
)
new_aluno_header = (
    '                            <th style="text-align:left;">Matrícula</th>\n'
    '                            <th style="text-align:left;">Curso</th>\n'
    '                            <th style="text-align:center;">Per.</th>\n'
    '                            <th style="text-align:center;">Status</th>\n'
    '                            <th class="uc-th-actions">Ações</th>\n'
    '                        </tr>'
)
if old_aluno_header in content:
    content = content.replace(old_aluno_header, new_aluno_header, 1)
    print('✓ Aluno table header updated')
else:
    print('✗ Aluno table header NOT found')

# ===================================================
# STEP 3: Aluno table row — status badge + conditional buttons
# ===================================================

old_aluno_row = """\
                        <tr>
                            <td>{{ aluno.nome_aluno }} {{ aluno.sobrenome_aluno }}</td>
                            <td style="font-size:12px;">{{ aluno.id_aluno.email }}</td>
                            <td><code style="background:#f0f0f0; padding:2px 6px; border-radius:4px; font-size:12px;">{{ aluno.matricula_aluno|default:"-" }}</code></td>
                            <td>{{ aluno.curso_aluno }}</td>
                            <td style="text-align:center;">{{ aluno.periodo }}º</td>
                            <td class="uc-td-actions">
                                <button type="button" class="uc-btn uc-btn--outline uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalEditarAluno{{ aluno.pk }}" title="Editar">
                                    <i class="fas fa-pen"></i>
                                </button>
                                <button type="button" class="uc-btn uc-btn--danger uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalExcluirAluno{{ aluno.pk }}">
                                    <i class="fas fa-user-slash"></i> Inativar
                                </button>
                            </td>
                        </tr>"""

new_aluno_row = """\
                        <tr>
                            <td>{{ aluno.nome_aluno }} {{ aluno.sobrenome_aluno }}</td>
                            <td style="font-size:12px;">{{ aluno.id_aluno.email }}</td>
                            <td><code style="background:#f0f0f0; padding:2px 6px; border-radius:4px; font-size:12px;">{{ aluno.matricula_aluno|default:"-" }}</code></td>
                            <td>{{ aluno.curso_aluno }}</td>
                            <td style="text-align:center;">{{ aluno.periodo }}º</td>
                            <td style="text-align:center;">
                                {% if aluno.ativo %}
                                    <span class="uc-badge uc-badge--success">Ativo</span>
                                {% else %}
                                    <span class="uc-badge uc-badge--danger">Inativo</span>
                                {% endif %}
                            </td>
                            <td class="uc-td-actions">
                                <button type="button" class="uc-btn uc-btn--outline uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalEditarAluno{{ aluno.pk }}" title="Editar">
                                    <i class="fas fa-pen"></i>
                                </button>
                                {% if aluno.ativo %}
                                <button type="button" class="uc-btn uc-btn--danger uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalExcluirAluno{{ aluno.pk }}">
                                    <i class="fas fa-user-slash"></i> Inativar
                                </button>
                                {% else %}
                                <button type="button" class="uc-btn uc-btn--success uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalReativarAluno{{ aluno.pk }}">
                                    <i class="fas fa-user-check"></i> Reativar
                                </button>
                                {% endif %}
                            </td>
                        </tr>"""

if old_aluno_row in content:
    content = content.replace(old_aluno_row, new_aluno_row, 1)
    print('✓ Aluno table row updated')
else:
    print('✗ Aluno table row NOT found')

# ===================================================
# STEP 4: Professor table — add Status column header
# ===================================================

old_prof_header = (
    '                            <th style="text-align:center;">Disciplinas</th>\n'
    '                            <th class="uc-th-actions">Ações</th>\n'
    '                        </tr>'
)
new_prof_header = (
    '                            <th style="text-align:center;">Disciplinas</th>\n'
    '                            <th style="text-align:center;">Status</th>\n'
    '                            <th class="uc-th-actions">Ações</th>\n'
    '                        </tr>'
)
if old_prof_header in content:
    content = content.replace(old_prof_header, new_prof_header, 1)
    print('✓ Professor table header updated')
else:
    print('✗ Professor table header NOT found')

# ===================================================
# STEP 5: Professor table row — status badge + conditional buttons
# ===================================================

old_prof_row = """\
                        <tr>
                            <td>{{ prof.nome_professor }} {{ prof.sobrenome_professor }}</td>
                            <td style="font-size:12px;">{{ prof.id_professor.email }}</td>
                            <td>{{ prof.curso_professor }}</td>
                            <td style="text-align:center;">
                                <span class="uc-badge uc-badge--orange">{{ prof.disciplinas.count }}</span>
                            </td>
                            <td class="uc-td-actions">
                                <button type="button" class="uc-btn uc-btn--outline uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalEditarProf{{ prof.pk }}" title="Editar">
                                    <i class="fas fa-pen"></i>
                                </button>
                                <button type="button" class="uc-btn uc-btn--danger uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalExcluirProf{{ prof.pk }}">
                                    <i class="fas fa-user-slash"></i> Inativar
                                </button>
                            </td>
                        </tr>"""

new_prof_row = """\
                        <tr>
                            <td>{{ prof.nome_professor }} {{ prof.sobrenome_professor }}</td>
                            <td style="font-size:12px;">{{ prof.id_professor.email }}</td>
                            <td>{{ prof.curso_professor }}</td>
                            <td style="text-align:center;">
                                <span class="uc-badge uc-badge--orange">{{ prof.disciplinas.count }}</span>
                            </td>
                            <td style="text-align:center;">
                                {% if prof.ativo %}
                                    <span class="uc-badge uc-badge--success">Ativo</span>
                                {% else %}
                                    <span class="uc-badge uc-badge--danger">Inativo</span>
                                {% endif %}
                            </td>
                            <td class="uc-td-actions">
                                <button type="button" class="uc-btn uc-btn--outline uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalEditarProf{{ prof.pk }}" title="Editar">
                                    <i class="fas fa-pen"></i>
                                </button>
                                {% if prof.ativo %}
                                <button type="button" class="uc-btn uc-btn--danger uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalExcluirProf{{ prof.pk }}">
                                    <i class="fas fa-user-slash"></i> Inativar
                                </button>
                                {% else %}
                                <button type="button" class="uc-btn uc-btn--success uc-btn--sm" data-bs-toggle="modal" data-bs-target="#modalReativarProf{{ prof.pk }}">
                                    <i class="fas fa-user-check"></i> Reativar
                                </button>
                                {% endif %}
                            </td>
                        </tr>"""

if old_prof_row in content:
    content = content.replace(old_prof_row, new_prof_row, 1)
    print('✓ Professor table row updated')
else:
    print('✗ Professor table row NOT found')

# ===================================================
# STEP 6: Fix modalExcluirAluno — replace "Excluir" modal with
#         proper "Inativar" modal + add new "Reativar" modal
# ===================================================

old_modal_aluno = """\
<div class="modal fade" id="modalExcluirAluno{{ aluno.pk }}" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-sm">
        <div class="modal-content" style="border-radius:12px; overflow:hidden;">
            <div class="modal-header" style="background:#dc3545; color:#fff; border:none;">
                <h5 class="modal-title"><i class="fas fa-exclamation-triangle me-2"></i> Excluir Aluno</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="{% url 'dashboard:excluir_aluno' aluno.pk %}">
                {% csrf_token %}
                <div class="modal-body p-4">
                    <p style="font-size:14px;">Excluir <strong>{{ aluno.nome_completo }}</strong>?</p>
                    <small class="text-danger"><i class="fas fa-exclamation-circle me-1"></i>Ação irreversível.</small>
                </div>
                <div class="modal-footer" style="border:none; padding-top:0;">
                    <button type="button" class="uc-btn uc-btn--ghost uc-btn--sm" data-bs-dismiss="modal">Cancelar</button>
                    <button type="submit" class="uc-btn uc-btn--danger uc-btn--sm">
                        <i class="fas fa-trash-alt me-1"></i> Excluir
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>"""

new_modal_aluno = """\
<div class="modal fade" id="modalExcluirAluno{{ aluno.pk }}" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-sm">
        <div class="modal-content" style="border-radius:12px; overflow:hidden;">
            <div class="modal-header" style="background:#dc3545; color:#fff; border:none;">
                <h5 class="modal-title"><i class="fas fa-user-slash me-2"></i> Inativar Aluno</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="{% url 'dashboard:excluir_aluno' aluno.pk %}">
                {% csrf_token %}
                <div class="modal-body p-4">
                    <p style="font-size:14px;">Inativar <strong>{{ aluno.nome_completo }}</strong>?</p>
                    <small class="text-muted"><i class="fas fa-info-circle me-1"></i>O aluno poderá ser reativado posteriormente.</small>
                </div>
                <div class="modal-footer" style="border:none; padding-top:0;">
                    <button type="button" class="uc-btn uc-btn--ghost uc-btn--sm" data-bs-dismiss="modal">Cancelar</button>
                    <button type="submit" class="uc-btn uc-btn--danger uc-btn--sm">
                        <i class="fas fa-user-slash me-1"></i> Inativar
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<div class="modal fade" id="modalReativarAluno{{ aluno.pk }}" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-sm">
        <div class="modal-content" style="border-radius:12px; overflow:hidden;">
            <div class="modal-header" style="background:#166534; color:#fff; border:none;">
                <h5 class="modal-title"><i class="fas fa-user-check me-2"></i> Reativar Aluno</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="{% url 'dashboard:reativar_aluno' aluno.pk %}">
                {% csrf_token %}
                <div class="modal-body p-4">
                    <p style="font-size:14px;">Reativar <strong>{{ aluno.nome_completo }}</strong>?</p>
                    <small class="text-success"><i class="fas fa-check-circle me-1"></i>O aluno voltará a ter acesso ao sistema.</small>
                </div>
                <div class="modal-footer" style="border:none; padding-top:0;">
                    <button type="button" class="uc-btn uc-btn--ghost uc-btn--sm" data-bs-dismiss="modal">Cancelar</button>
                    <button type="submit" class="uc-btn uc-btn--success uc-btn--sm">
                        <i class="fas fa-user-check me-1"></i> Reativar
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>"""

if old_modal_aluno in content:
    content = content.replace(old_modal_aluno, new_modal_aluno)
    print('✓ modalExcluirAluno/modalReativarAluno updated')
else:
    print('✗ modalExcluirAluno NOT found')

# ===================================================
# STEP 7: Fix modalExcluirProf — replace with proper
#         "Inativar" modal + add new "Reativar" modal
# ===================================================

old_modal_prof = """\
<div class="modal fade" id="modalExcluirProf{{ prof.pk }}" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content" style="border-radius:16px; overflow:hidden; border:none; box-shadow:0 20px 60px rgba(0,0,0,.18);">
            <div class="modal-header" style="background:linear-gradient(135deg,#b91c1c,#dc3545); color:#fff; border:none; padding:20px 24px;">
                <h5 class="modal-title">
                    <i class="fas fa-user-slash me-2"></i> Inativar Professor
                </h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="{% url 'dashboard:excluir_professor' prof.pk %}">
                {% csrf_token %}
                <div class="modal-body p-4">
                    <p style="font-size:14px;">Excluir <strong>{{ prof.nome_completo }}</strong>?</p>
                    {% if prof.disciplinas.count %}
                    <small class="text-warning"><i class="fas fa-exclamation-triangle me-1"></i>{{ prof.disciplinas.count }} disciplina{{ prof.disciplinas.count|pluralize }} vinculada{{ prof.disciplinas.count|pluralize }} será{{ prof.disciplinas.count|pluralize:"á,ão" }} removida{{ prof.disciplinas.count|pluralize }}.</small><br>
                    {% endif %}
                    <small class="text-danger"><i class="fas fa-exclamation-circle me-1"></i>Ação irreversível.</small>
                </div>
                <div class="modal-footer" style="border:none; padding-top:0;">
                    <button type="button" class="uc-btn uc-btn--ghost uc-btn--sm" data-bs-dismiss="modal">Cancelar</button>
                    <button type="submit" class="uc-btn uc-btn--danger uc-btn--sm">
                        <i class="fas fa-trash-alt me-1"></i> Excluir
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>"""

new_modal_prof = """\
<div class="modal fade" id="modalExcluirProf{{ prof.pk }}" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-sm">
        <div class="modal-content" style="border-radius:12px; overflow:hidden;">
            <div class="modal-header" style="background:#dc3545; color:#fff; border:none;">
                <h5 class="modal-title"><i class="fas fa-user-slash me-2"></i> Inativar Professor</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="{% url 'dashboard:excluir_professor' prof.pk %}">
                {% csrf_token %}
                <div class="modal-body p-4">
                    <p style="font-size:14px;">Inativar <strong>{{ prof.nome_completo }}</strong>?</p>
                    <small class="text-muted"><i class="fas fa-info-circle me-1"></i>O professor poderá ser reativado posteriormente.</small>
                </div>
                <div class="modal-footer" style="border:none; padding-top:0;">
                    <button type="button" class="uc-btn uc-btn--ghost uc-btn--sm" data-bs-dismiss="modal">Cancelar</button>
                    <button type="submit" class="uc-btn uc-btn--danger uc-btn--sm">
                        <i class="fas fa-user-slash me-1"></i> Inativar
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<div class="modal fade" id="modalReativarProf{{ prof.pk }}" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-sm">
        <div class="modal-content" style="border-radius:12px; overflow:hidden;">
            <div class="modal-header" style="background:#166534; color:#fff; border:none;">
                <h5 class="modal-title"><i class="fas fa-user-check me-2"></i> Reativar Professor</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <form method="post" action="{% url 'dashboard:reativar_professor' prof.pk %}">
                {% csrf_token %}
                <div class="modal-body p-4">
                    <p style="font-size:14px;">Reativar <strong>{{ prof.nome_completo }}</strong>?</p>
                    <small class="text-success"><i class="fas fa-check-circle me-1"></i>O professor voltará a ter acesso ao sistema.</small>
                </div>
                <div class="modal-footer" style="border:none; padding-top:0;">
                    <button type="button" class="uc-btn uc-btn--ghost uc-btn--sm" data-bs-dismiss="modal">Cancelar</button>
                    <button type="submit" class="uc-btn uc-btn--success uc-btn--sm">
                        <i class="fas fa-user-check me-1"></i> Reativar
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>"""

if old_modal_prof in content:
    content = content.replace(old_modal_prof, new_modal_prof)
    print('✓ modalExcluirProf/modalReativarProf updated')
else:
    print('✗ modalExcluirProf NOT found')

# ===================================================
# STEP 8: Write fixed file (UTF-8 without BOM)
# ===================================================
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

remaining_final = content.count('\ufffd')
print(f'Replacement chars remaining: {remaining_final}')
print('Done.')
