from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('atividades', '0002_add_atestado_to_portaria'),
    ]

    operations = [
        migrations.AddField(
            model_name='aluno',
            name='ativo',
            field=models.BooleanField(
                default=True,
                help_text='False = inativado por LGPD (não excluído)',
            ),
        ),
        migrations.AddField(
            model_name='professor',
            name='ativo',
            field=models.BooleanField(
                default=True,
                help_text='False = inativado por LGPD (não excluído)',
            ),
        ),
        migrations.AddField(
            model_name='diretor',
            name='ativo',
            field=models.BooleanField(
                default=True,
                help_text='False = inativado por LGPD (não excluído)',
            ),
        ),
    ]
