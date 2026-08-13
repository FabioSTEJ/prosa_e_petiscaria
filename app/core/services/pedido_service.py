from app.core.models import Pedido, Produto, Mesa
from app.infrastructure.extensions import db, socketio

_STATUS_VALIDOS = {'Pendente', 'Em Preparo', 'Pronto', 'Entregue', 'Cancelado', 'Finalizado'}

# 'Finalizado' não aparece aqui como destino: só é atribuído internamente por
# MesaService.finalizar() ao fechar a conta, nunca via troca manual de status.
_TRANSICOES_VALIDAS = {
    'Pendente': {'Em Preparo', 'Cancelado'},
    'Em Preparo': {'Pronto', 'Cancelado'},
    'Pronto': {'Entregue', 'Cancelado'},
    'Entregue': set(),
    'Cancelado': set(),
    'Finalizado': set(),
}


class PedidoService:
    @staticmethod
    def lancar(mesa_id: int, produto_id: int, quantidade: int, usuario_id: int, observacao: str = '') -> Pedido:
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero.")
        produto = Produto.query.get_or_404(produto_id)
        if not produto.disponivel:
            raise ValueError(f"Produto '{produto.nome}' não está disponível no cardápio.")
        mesa = Mesa.query.get_or_404(mesa_id)
        pedido = Pedido(
            mesa_id=mesa_id,
            usuario_id=usuario_id,
            item_nome=produto.nome,
            quantidade=quantidade,
            valor_unitario=produto.preco,
            valor_total=produto.preco * quantidade,
            status='Pendente',
            observacao=observacao.strip() or None,
        )
        db.session.add(pedido)
        db.session.commit()
        socketio.emit('novo_pedido', {
            'mesa': mesa.numero,
            'item': produto.nome,
            'quantidade': quantidade,
            'observacao': observacao.strip(),
        })
        return pedido

    @staticmethod
    def mudar_status(pedido_id: int, novo_status: str) -> Pedido:
        if novo_status not in _STATUS_VALIDOS:
            raise ValueError(f"Status '{novo_status}' inválido.")
        pedido = Pedido.query.get_or_404(pedido_id)
        if novo_status not in _TRANSICOES_VALIDAS.get(pedido.status, set()):
            raise ValueError(
                f"Não é possível mudar o status de '{pedido.status}' para '{novo_status}'."
            )
        pedido.status = novo_status
        db.session.commit()
        socketio.emit('status_pedido', {
            'pedido_id': pedido.id,
            'novo_status': novo_status,
            'mesa': pedido.mesa_rel.numero,
        })
        return pedido

    @staticmethod
    def excluir(pedido_id: int) -> None:
        pedido = Pedido.query.get_or_404(pedido_id)
        db.session.delete(pedido)
        db.session.commit()
