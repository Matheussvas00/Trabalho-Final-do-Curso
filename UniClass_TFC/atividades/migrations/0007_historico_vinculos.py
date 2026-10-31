"""
Vincula cada registro do histórico à portaria, ao aluno e ao professor envolvidos,
para permitir os filtros da tela de Histórico. Os registros antigos são preenchidos
a partir do texto da descrição e do perfil de quem fez a ação.
"""
import re

import django.db.models.deletion
from django.db import migrations, models


def preencher_vinculos(apps, schema_editor):
    Historico = apps.get_model('atividades', 'Historico')
    RespostaAtividade = apps.get_model('atividades', 'RespostaAtividade')
    Portaria = apps.get_model('atividades', 'Portaria')
    Atividade = apps.get_model('atividades', 'Atividade')
    Aluno = apps.get_model('atividades', 'Aluno')
    Professor = apps.get_model('atividades', 'Professor')

    for h in Historico.objects.select_related('id_usuario').iterator():
        texto = h.descricao or ''
        portaria = aluno = professor = None

        # "Resposta #12 do aluno ..." -> resposta -> atividade -> portaria / aluno / professor
        m = re.search(r'Resposta #(\d+)', texto)
        if m:
            resposta = (RespostaAtividade.objects
                        .select_related('id_atividade__id_portariafk')
                        .filter(pk=int(m.group(1))).first())
            if resposta:
                portaria = resposta.id_atividade.id_portariafk
                aluno = resposta.id_alunofk
                professor = resposta.id_atividade.id_professorfk

        # "... (Portaria nº 005/2026)" -> portaria -> aluno
        if portaria is None:
            m = re.search(r'[Pp]ortaria nº\s*([^\s)]+)', texto)
            if m:
                portaria = Portaria.objects.filter(numero_portaria=m.group(1).rstrip('.,;')).first()
        if portaria is not None and aluno is None:
            aluno = portaria.id_alunofk
        if portaria is not None and professor is None:
            m = re.search(r'tividade "(.+?)"', texto)
            if m:
                atividade = Atividade.objects.filter(id_portariafk=portaria, titulo=m.group(1)).first()
                if atividade:
                    professor = atividade.id_professorfk

        # Quem fez a ação também identifica o aluno ou o professor
        tipo = h.id_usuario.tipo_usuario if h.id_usuario_id else None
        if tipo == 'aluno' and aluno is None:
            aluno = Aluno.objects.filter(pk=h.id_usuario_id).first()
        if tipo == 'professor' and professor is None:
            professor = Professor.objects.filter(pk=h.id_usuario_id).first()

        if portaria or aluno or professor:
            h.id_portariafk = portaria
            h.id_alunofk = aluno
            h.id_professorfk = professor
            h.save(update_fields=['id_portariafk', 'id_alunofk', 'id_professorfk'])


class Migration(migrations.Migration):

    dependencies = [
        ("atividades", "0006_arquivo_armazenado"),
    ]

    operations = [
        migrations.AddField(
            model_name="historico",
            name="id_alunofk",
            field=models.ForeignKey(
                blank=True,
                db_column="id_alunofk",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="historico_aluno",
                to="atividades.aluno",
            ),
        ),
        migrations.AddField(
            model_name="historico",
            name="id_portariafk",
            field=models.ForeignKey(
                blank=True,
                db_column="id_portariafk",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="historico_portaria",
                to="atividades.portaria",
            ),
        ),
        migrations.AddField(
            model_name="historico",
            name="id_professorfk",
            field=models.ForeignKey(
                blank=True,
                db_column="id_professorfk",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="historico_professor",
                to="atividades.professor",
            ),
        ),
        migrations.RunPython(preencher_vinculos, migrations.RunPython.noop),
    ]
