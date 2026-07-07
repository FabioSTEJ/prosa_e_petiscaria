from flask import Blueprint
from app.api.admin.controller import (
    dashboard_view, historico_vendas_view, painel_cozinha, mudar_status,
    gerenciar_usuarios_view, excluir_usuario, alternar_status_usuario, mudar_senha_usuario,
    gerenciar_cardapio_view, deletar_produto_view, reativar_produto_view, gerenciar_mesas_view,
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

admin_bp.add_url_rule('/dashboard', view_func=dashboard_view)
admin_bp.add_url_rule('/vendas', view_func=historico_vendas_view)
admin_bp.add_url_rule('/cozinha', view_func=painel_cozinha)
admin_bp.add_url_rule('/pedido/status/<int:pedido_id>/<string:novo_status>', view_func=mudar_status)
admin_bp.add_url_rule('/usuarios', view_func=gerenciar_usuarios_view, methods=['GET', 'POST'])
admin_bp.add_url_rule('/usuarios/excluir/<int:usuario_id>', view_func=excluir_usuario)
admin_bp.add_url_rule('/usuarios/status/<int:usuario_id>', view_func=alternar_status_usuario)
admin_bp.add_url_rule('/usuarios/senha/<int:usuario_id>', view_func=mudar_senha_usuario, methods=['POST'])
admin_bp.add_url_rule('/cardapio', view_func=gerenciar_cardapio_view, methods=['GET', 'POST'])
admin_bp.add_url_rule('/cardapio/deletar/<int:produto_id>', view_func=deletar_produto_view)
admin_bp.add_url_rule('/cardapio/reativar/<int:produto_id>', view_func=reativar_produto_view)
admin_bp.add_url_rule('/mesas', view_func=gerenciar_mesas_view, methods=['GET', 'POST'])
