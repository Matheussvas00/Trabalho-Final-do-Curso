#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# IMPORTANTE: Patches de compatibilidade MySQL 5.6 + PyMySQL + Django 6.0
import pymysql
pymysql.install_as_MySQLdb()
pymysql.version_info = (2, 2, 1, "final", 0)

# Patch para desabilitar verificação de versão do MySQL
def patch_mysql_check():
    from django.db.backends.mysql import base
    from django.db.backends.base import base as generic_base
    
    # Sobrescreve o método de verificação para aceitar MySQL 5.6
    original_check = generic_base.BaseDatabaseWrapper.check_database_version_supported
    
    def patched_check(self):
        if hasattr(self, 'mysql_version'):
            # Para MySQL, aceita versão 5.6+
            if self.mysql_version < (5, 6, 0):
                from django.db.utils import NotSupportedError
                raise NotSupportedError('MySQL 5.6.0 or later is required (found %s).' % '.'.join(str(x) for x in self.mysql_version))
            return
        # Para outros bancos, usa a verificação original
        return original_check(self)
    
    generic_base.BaseDatabaseWrapper.check_database_version_supported = patched_check


def main(): 
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UniCLass.settings')
    
    # Aplica o patch ANTES de qualquer comando Django
    patch_mysql_check()
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
