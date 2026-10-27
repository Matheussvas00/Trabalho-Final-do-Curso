"""
Armazenamento dos arquivos enviados no banco de dados.

Substitui o FileSystemStorage padrão do Django. Todos os arquivos salvos
com default_storage (atestados das portarias, respostas dos alunos e anexos
das atividades) passam a ficar na tabela arquivo_armazenado, o que permite
hospedar o sistema na Vercel, onde a pasta media/ não pode ser gravada.
"""
import mimetypes

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class BancoDeDadosStorage(Storage):

    def _modelo(self):
        from atividades.models import ArquivoArmazenado
        return ArquivoArmazenado

    def _normalizar(self, name):
        return str(name).replace('\\', '/').lstrip('/')

    def _open(self, name, mode='rb'):
        obj = self._modelo().objects.get(nome=self._normalizar(name))
        arquivo = ContentFile(bytes(obj.conteudo))
        arquivo.name = obj.nome
        return arquivo

    def _save(self, name, content):
        name = self._normalizar(name)
        if hasattr(content, 'seek'):
            content.seek(0)
        dados = content.read()
        if isinstance(dados, str):
            dados = dados.encode('utf-8')
        tipo = getattr(content, 'content_type', None) or mimetypes.guess_type(name)[0] or ''
        self._modelo().objects.create(nome=name, conteudo=dados, tipo=tipo, tamanho=len(dados))
        return name

    def exists(self, name):
        return self._modelo().objects.filter(nome=self._normalizar(name)).exists()

    def delete(self, name):
        self._modelo().objects.filter(nome=self._normalizar(name)).delete()

    def size(self, name):
        obj = self._modelo().objects.filter(nome=self._normalizar(name)).only('tamanho').first()
        return obj.tamanho if obj else 0

    def url(self, name):
        return settings.MEDIA_URL + self._normalizar(name)

    def get_available_name(self, name, max_length=None):
        # mantém o comportamento do Django: acrescenta um sufixo se o nome já existir
        return super().get_available_name(self._normalizar(name), max_length=max_length)
