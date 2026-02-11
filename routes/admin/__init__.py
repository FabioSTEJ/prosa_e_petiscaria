from flask import Blueprint

# Todas as rotas de admin começarão com /admin/...
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Importações dos arquivos individuais virão aqui depois