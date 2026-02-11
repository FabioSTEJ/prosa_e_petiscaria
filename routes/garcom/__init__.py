from flask import Blueprint

# Criamos o Blueprint
garcom_bp = Blueprint('garcom', __name__, url_prefix='/garcom')

# Importamos as funções dos arquivos individuais
from .painel import painel_view
from .detalhe import detalhe_view
from .abrir import abrir_action
from .lancar import lancar_action

# Registramos as rotas no Blueprint
garcom_bp.add_url_rule('/painel', view_func=painel_view)
garcom_bp.add_url_rule('/mesa/<int:mesa_id>', view_func=detalhe_view)
garcom_bp.add_url_rule('/mesa/abrir/<int:mesa_id>', view_func=abrir_action, methods=['POST'])
garcom_bp.add_url_rule('/mesa/lancar/<int:mesa_id>', view_func=lancar_action, methods=['POST'])