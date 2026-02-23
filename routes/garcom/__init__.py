from flask import Blueprint
from .home import home_garcom
from .painel import painel_garcom
from .detalhe import detalhe_mesa, abrir_mesa, lancar_item, excluir_item, finalizar_mesa

garcom_bp = Blueprint('garcom', __name__, url_prefix='/garcom')

# Rota da Home (Boas-vindas)
garcom_bp.add_url_rule('/home', view_func=home_garcom)

# Rota do Mapa de Mesas
garcom_bp.add_url_rule('/painel', view_func=painel_garcom)

# Rotas de Gerenciamento da Mesa
garcom_bp.add_url_rule('/mesa/<int:mesa_id>', view_func=detalhe_mesa)
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/abrir', view_func=abrir_mesa, methods=['POST'])
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/lancar', view_func=lancar_item, methods=['POST'])
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/excluir/<int:pedido_id>', view_func=excluir_item)
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/finalizar', view_func=finalizar_mesa)