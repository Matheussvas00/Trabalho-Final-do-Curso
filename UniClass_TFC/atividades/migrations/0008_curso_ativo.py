from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('atividades', '0007_historico_vinculos'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='ativo',
            field=models.BooleanField(default=True, help_text='False = curso inativado (os dados são mantidos)'),
        ),
    ]
