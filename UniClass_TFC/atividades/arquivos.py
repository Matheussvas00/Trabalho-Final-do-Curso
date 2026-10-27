"""
Entrega dos arquivos enviados (atestados, respostas e anexos).

Os arquivos ficam no banco de dados (ver atividades/storage.py). Para não
perder arquivos antigos, se o arquivo não estiver no banco a view procura
na pasta media/ local. O acesso exige login, porque os atestados são
dados pessoais de saúde (LGPD).
"""
import mimetypes
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse

from atividades.models import ArquivoArmazenado


@login_required
def servir_arquivo(request, nome):
    nome = nome.replace('\\', '/').lstrip('/')
    obj = ArquivoArmazenado.objects.filter(nome=nome).first()
    if obj is not None:
        tipo = obj.tipo or mimetypes.guess_type(nome)[0] or 'application/octet-stream'
        resposta = HttpResponse(bytes(obj.conteudo), content_type=tipo)
        resposta['Content-Disposition'] = f'inline; filename="{os.path.basename(nome)}"'
        resposta['Content-Length'] = str(obj.tamanho)
        return resposta

    raiz = os.path.realpath(str(settings.MEDIA_ROOT))
    caminho = os.path.realpath(os.path.join(raiz, nome))
    if caminho.startswith(raiz + os.sep) and os.path.isfile(caminho):
        return FileResponse(open(caminho, 'rb'))
    raise Http404('Arquivo não encontrado.')
