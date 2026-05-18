from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('atividades', '0004_alter_atividade_status_alter_portaria_status_and_more'),
    ]

    operations = [
        # data_hora already exists in DB from original migration — skip adding it
        migrations.AddField(
            model_name='historico',
            name='acao',
            field=models.CharField(
                choices=[
                    ('login', 'Login'),
                    ('logout', 'Logout'),
                    ('portaria_criada', 'Portaria Criada'),
                    ('portaria_editada', 'Portaria Editada'),
                    ('portaria_excluida', 'Portaria Excluída'),
                    ('atividade_criada', 'Atividade Criada'),
                    ('atividade_editada', 'Atividade Editada'),
                    ('atividade_excluida', 'Atividade Excluída'),
                    ('resposta_enviada', 'Resposta Enviada'),
                    ('resposta_editada', 'Resposta Editada'),
                    ('resposta_aprovada_prof', 'Resposta Aprovada pelo Professor'),
                    ('resposta_rejeitada_prof', 'Resposta Rejeitada pelo Professor'),
                    ('resposta_aprovada_dir', 'Resposta Aprovada pelo Diretor'),
                    ('resposta_rejeitada_dir', 'Resposta Rejeitada pelo Diretor'),
                    ('aluno_cadastrado', 'Aluno Cadastrado'),
                    ('professor_cadastrado', 'Professor Cadastrado'),
                    ('diretor_cadastrado', 'Diretor Cadastrado'),
                ],
                default='login',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='historico',
            name='descricao',
            field=models.TextField(blank=True, null=True),
        ),
    ]
