"""
Comando de gerenciamento: cria o usuário administrador padrão do sistema UniClass.

Uso:
    python manage.py criar_admin
    python manage.py criar_admin --email admin@uniclass.edu.br --senha Senha@1234
    python manage.py criar_admin --email admin@uniclass.edu.br --nome Admin --sobrenome Sistema --senha Senha@1234
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Cria o usuário administrador do sistema UniClass.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@uniclass.edu.br',
            help='E-mail do administrador (padrão: admin@uniclass.edu.br)',
        )
        parser.add_argument(
            '--nome',
            type=str,
            default='Administrador',
            help='Primeiro nome (padrão: Administrador)',
        )
        parser.add_argument(
            '--sobrenome',
            type=str,
            default='Sistema',
            help='Sobrenome (padrão: Sistema)',
        )
        parser.add_argument(
            '--senha',
            type=str,
            default=None,
            help='Senha do administrador (será solicitada interativamente se omitida)',
        )

    def handle(self, *args, **options):
        from atividades.models import Usuario, Admin

        email     = options['email'].strip()
        nome      = options['nome'].strip()
        sobrenome = options['sobrenome'].strip()
        senha     = options.get('senha')

        # Solicita senha interativamente se não foi passada via argumento
        if not senha:
            import getpass
            self.stdout.write(self.style.WARNING(f'Criando administrador: {email}'))
            senha = getpass.getpass('Senha: ')
            confirmar = getpass.getpass('Confirme a senha: ')
            if senha != confirmar:
                raise CommandError('As senhas não coincidem.')

        if len(senha) < 8:
            raise CommandError('A senha deve ter pelo menos 8 caracteres.')

        if Usuario.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(
                f'Já existe um usuário com o e-mail "{email}". '
                'Use outro e-mail ou exclua o usuário existente primeiro.'
            ))
            return

        with transaction.atomic():
            usuario = Usuario(email=email, tipo_usuario='admin')
            usuario.set_password(senha)
            usuario.save()

            Admin.objects.create(
                id_admin=usuario,
                nome_admin=nome,
                sobrenome_admin=sobrenome,
            )

        self.stdout.write(self.style.SUCCESS(
            f'\n✔ Administrador criado com sucesso!\n'
            f'  E-mail : {email}\n'
            f'  Nome   : {nome} {sobrenome}\n'
            f'\nAcesse o sistema e faça login com esse e-mail e senha.\n'
        ))
