from flask import request, redirect, url_for, flash, session
from database import db
from models import Pedido, Produto, Mesa
from routes.auth import login_requerido

@login_requerido(cargo_necessario='garcom')
def lancar_item(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    produto_id = request.form.get('produto_id')
    quantidade = int(request.form.get('quantidade', 1))
    
    produto = Produto.query.get(produto_id)
    if produto:
        novo_item = Pedido(
            mesa_id=mesa.id,
            usuario_id=session['usuario_id'],
            item_nome=produto.nome,
            quantidade=quantidade,
            valor_unitario=produto.preco,
            valor_total=produto.preco * quantidade,
            status='Pendente'
        )
        db.session.add(novo_item)
        db.session.commit()
        flash(f"{quantidade}x {produto.nome} adicionado!")
    
    return redirect(url_for('garcom.detalhe_mesa', mesa_id=mesa.id))