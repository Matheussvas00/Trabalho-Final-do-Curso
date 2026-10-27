"""
Configuração usada apenas para rodar os testes localmente com SQLite,
sem precisar do servidor MySQL.

Uso:
    pytest --ds=uc_test_settings atividades/tests.py
"""
import tempfile
from UniCLass.settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'uniclass_test.sqlite3',
    }
}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
MEDIA_ROOT = tempfile.mkdtemp(prefix='uniclass_media_')
