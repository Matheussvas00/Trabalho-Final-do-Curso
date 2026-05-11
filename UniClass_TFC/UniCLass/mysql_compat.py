"""
Patches necessários para compatibilidade com MySQL 5.6 e PyMySQL no Django 6.0
Este arquivo deve ser importado ANTES de qualquer outra configuração do Django
"""
import pymysql

# Instala PyMySQL como MySQLdb
pymysql.install_as_MySQLdb()

# Patch versão do PyMySQL para Django 6.0
pymysql.version_info = (2, 2, 1, "final", 0)

# Patch para aceitar MySQL 5.6 (mínimo oficial é 8.0.11)
def patch_mysql_version():
    from django.db.backends.mysql import base
    base.DatabaseWrapper.mysql_version_required = (5, 6, 0)
    
# Executa o patch antes do Django carregar
patch_mysql_version()
