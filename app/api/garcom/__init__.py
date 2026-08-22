from flask import Blueprint
from app.api.garcom.controller import (
    home_garcom, painel_garcom, detalhe_mesa,
    tela_unir_mesas, unir_mesas, desunir_mesa,
    abrir_comanda, detalhe_comanda, lancar_item, excluir_item, finalizar_comanda,
    pedidos_prontos_view, entregar_pedido,
)

garcom_bp = Blueprint('garcom', __name__, url_prefix='/garcom')

garcom_bp.add_url_rule('/home', view_func=home_garcom)
garcom_bp.add_url_rule('/painel', view_func=painel_garcom)
garcom_bp.add_url_rule('/mesa/<int:mesa_id>', view_func=detalhe_mesa)
garcom_bp.add_url_rule('/mesas/unir', view_func=tela_unir_mesas, methods=['GET'])
garcom_bp.add_url_rule('/mesas/unir', view_func=unir_mesas, methods=['POST'])
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/desunir', view_func=desunir_mesa, methods=['POST'])
garcom_bp.add_url_rule('/mesa/<int:mesa_id>/abrir-comanda', view_func=abrir_comanda, methods=['POST'])
garcom_bp.add_url_rule('/comanda/<int:comanda_id>', view_func=detalhe_comanda)
garcom_bp.add_url_rule('/comanda/<int:comanda_id>/lancar', view_func=lancar_item, methods=['POST'])
garcom_bp.add_url_rule('/comanda/<int:comanda_id>/excluir/<int:pedido_id>', view_func=excluir_item)
garcom_bp.add_url_rule('/comanda/<int:comanda_id>/finalizar', view_func=finalizar_comanda)
garcom_bp.add_url_rule('/pedidos-prontos', view_func=pedidos_prontos_view)
garcom_bp.add_url_rule('/entregar/<int:pedido_id>', view_func=entregar_pedido)
