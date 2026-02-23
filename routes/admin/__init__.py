from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Importamos as funções dos arquivos individuais
from .dashboard import dashboard_view
# Atualizado: importando as novas funções de gestão de usuários
from .usuarios import (
    gerenciar_usuarios_view, 
    excluir_usuario, 
    alternar_status_usuario, 
    mudar_senha_usuario
)
from .cardapio import gerenciar_cardapio_view, deletar_produto_view
from .mesas import gerenciar_mesas_view
from .vendas import historico_vendas_view  # <--- Nova funcionalidade adicionada

# --- REGISTRO DE ROTAS ---

# Dashboard e Financeiro
admin_bp.add_url_rule('/dashboard', view_func=dashboard_view)
admin_bp.add_url_rule('/vendas', view_func=historico_vendas_view) # <--- Nova rota registrada

# Gerenciamento de Usuários
admin_bp.add_url_rule('/usuarios', view_func=gerenciar_usuarios_view, methods=['GET', 'POST'])
admin_bp.add_url_rule('/usuarios/excluir/<int:usuario_id>', view_func=excluir_usuario)
admin_bp.add_url_rule('/usuarios/status/<int:usuario_id>', view_func=alternar_status_usuario)
admin_bp.add_url_rule('/usuarios/senha/<int:usuario_id>', view_func=mudar_senha_usuario, methods=['POST'])

# Gerenciamento do Cardápio
admin_bp.add_url_rule('/cardapio', view_func=gerenciar_cardapio_view, methods=['GET', 'POST'])
admin_bp.add_url_rule('/cardapio/deletar/<int:id>', view_func=deletar_produto_view)

# Gerenciamento de Mesas
admin_bp.add_url_rule('/mesas', view_func=gerenciar_mesas_view, methods=['GET', 'POST'])