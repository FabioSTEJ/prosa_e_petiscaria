from flask import Blueprint
from app.api.garcom.controller import (
    home_garcom, painel_garcom, detalhe_mesa,
    abrir_mesa, lancar_item, excluir_item, finalizar_mesa,
    pedidos_prontos_view, entregar_pedido,
)

garcom_bp = Blueprint('garcom', __name__, url_prefix='/garcom')

garcom_bp.add_url_rule('/home', view_func=home_garcom)
garcom_bp.add_url_rule('/painel', view_func=painel_garcom)
garcom_bp.add_url_rule('/mesa/<int:mesa_id>', view_func=detalhe_mesa)
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/abrir', view_func=abrir_mesa, methods=['POST'])
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/lancar', view_func=lancar_item, methods=['POST'])
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/excluir/<int:pedido_id>', view_func=excluir_item)
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/finalizar', view_func=finalizar_mesa)
garcom_bp.add_url_rule('/pedidos-prontos', view_func=pedidos_prontos_view)
garcom_bp.add_url_rule('/entregar/<int:pedido_id>', view_func=entregar_pedido)
