from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, request
from app.api.decorators import login_requerido
from app.core.models import Mesa, Pedido, Produto
from app.core.services.mesa_service import MesaService
from app.core.services.pedido_service import PedidoService


@login_requerido(cargo_necessario='garcom')
def home_garcom():
    return render_template("garcom/home.html")


@login_requerido(cargo_necessario='garcom')
def painel_garcom():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    for mesa in mesas:
        mesa.alerta_tipo = None
        if mesa.status == 'Ocupada':
            pedidos_cozinha = Pedido.query.filter(
                Pedido.mesa_id == mesa.id,
                Pedido.status.in_(['Pendente', 'Em Preparo', 'Pronto']),
            ).all()
            if any(p.status == 'Pronto' for p in pedidos_cozinha):
                mesa.alerta_tipo = 'pronto'
            elif any(p.status == 'Em Preparo' for p in pedidos_cozinha):
                mesa.alerta_tipo = 'preparo'
            elif any(p.status == 'Pendente' for p in pedidos_cozinha):
                mesa.alerta_tipo = 'pendente'
            mesa.total_atual = mesa.calcular_total()
        else:
            mesa.total_atual = 0.0
    return render_template("garcom/painel.html", mesas=mesas)


@login_requerido(cargo_necessario='garcom')
def detalhe_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    if mesa.status == 'Livre':
        return render_template("garcom/abrir_mesa.html", mesa=mesa)
    itens_pedido = Pedido.query.filter(
        Pedido.mesa_id == mesa.id,
        Pedido.status != 'Cancelado',
        Pedido.status != 'Finalizado',
        Pedido.data >= mesa.data_abertura,
    ).all()
    produtos = Produto.query.filter_by(disponivel=True).all()
    return render_template("garcom/pedido.html",
                           mesa=mesa, itens=itens_pedido,
                           total=mesa.calcular_total(), produtos=produtos)


@login_requerido(cargo_necessario='garcom')
def abrir_mesa(mesa_id):
    mesa, foi_aberta = MesaService.abrir(mesa_id, session.get('usuario_id'))
    if foi_aberta:
        flash(f"Mesa {mesa.numero} aberta com sucesso!")
    return redirect(url_for('garcom.detalhe_mesa', mesa_id=mesa.id))


@login_requerido(cargo_necessario='garcom')
def lancar_item(mesa_id):
    if request.method == 'POST':
        produto_id = request.form.get('produto_id')
        quantidade = int(request.form.get('quantidade', 1))
        observacao = request.form.get('observacao', '')
        pedido = PedidoService.lancar(mesa_id, produto_id, quantidade, session.get('usuario_id'), observacao)
        flash(f"{pedido.item_nome} adicionado!")
    return redirect(url_for('garcom.detalhe_mesa', mesa_id=mesa_id))


@login_requerido(cargo_necessario='admin')
def excluir_item(mesa_id, pedido_id):
    PedidoService.excluir(pedido_id)
    flash("Item removido com sucesso.")
    return redirect(url_for('garcom.detalhe_mesa', mesa_id=mesa_id))


@login_requerido(cargo_necessario='admin')
def finalizar_mesa(mesa_id):
    resultado = MesaService.finalizar(mesa_id, session.get('usuario_id'))
    if resultado['total'] > 0:
        flash(f"Mesa {resultado['mesa_numero']} fechada! Total: R$ {resultado['total']:.2f}")
    else:
        flash(f"Mesa {resultado['mesa_numero']} estava vazia.")
    return redirect(url_for('garcom.painel_garcom'))


@login_requerido(cargo_necessario='garcom')
def pedidos_prontos_view():
    pedidos = Pedido.query.filter_by(status='Pronto').order_by(Pedido.data.asc()).all()
    return render_template("garcom/pedidos_prontos.html", pedidos=pedidos, now=datetime.now())


@login_requerido(cargo_necessario='garcom')
def entregar_pedido(pedido_id):
    PedidoService.mudar_status(pedido_id, 'Entregue')
    flash("Item marcado como entregue!")
    return redirect(url_for('garcom.pedidos_prontos_view'))
