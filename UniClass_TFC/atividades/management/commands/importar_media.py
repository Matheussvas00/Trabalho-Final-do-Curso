"""
Copia para o banco de dados os arquivos que estão na pasta media/ local
(atestados e respostas enviados antes do armazenamento no banco).

Uso:
    python manage.py importar_media
"""
import mimetypes
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from atividades.models import ArquivoArmazenado


class Command(BaseCommand):
    help = 'Importa os arquivos da pasta media/ para a tabela arquivo_armazenado.'

    def handle(self, *args, **options):
        raiz = str(settings.MEDIA_ROOT)
        if not os.path.isdir(raiz):
            self.stdout.write(f'Pasta {raiz} não encontrada. Nada a importar.')
            return
        novos = existentes = 0
        for pasta, _, arquivos in os.walk(raiz):
            for nome_arquivo in arquivos:
                caminho = os.path.join(pasta, nome_arquivo)
                nome = os.path.relpath(caminho, raiz).replace(os.sep, '/')
                if ArquivoArmazenado.objects.filter(nome=nome).exists():
                    existentes += 1
                    continue
                with open(caminho, 'rb') as f:
                    dados = f.read()
                ArquivoArmazenado.objects.create(
                    nome=nome, conteudo=dados, tamanho=len(dados),
                    tipo=mimetypes.guess_type(nome)[0] or '')
                novos += 1
        self.stdout.write(self.style.SUCCESS(
            f'{novos} arquivo(s) importado(s); {existentes} já estavam no banco.'))
