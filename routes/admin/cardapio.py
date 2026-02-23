from flask import render_template, request, redirect, url_for, flash
from database import db
from models import Produto
from routes.auth import login_requerido

@login_requerido(cargo_necessario='admin')
def gerenciar_cardapio_view():
    if request.method == 'POST':
        nome = request.form.get('nome')
        preco_raw = request.form.get('preco')
        categoria = request.form.get('categoria')
        
        if nome and preco_raw:
            try:
                preco = float(preco_raw)
                novo_produto = Produto(nome=nome, preco=preco, categoria=categoria)
                db.session.add(novo_produto)
                db.session.commit()
                flash(f"Produto '{nome}' adicionado!")
            except ValueError:
                flash("Preço inválido!")
            return redirect(url_for('admin.gerenciar_cardapio_view'))

    produtos = Produto.query.order_by(Produto.categoria).all()
    return render_template("admin_cardapio.html", produtos=produtos)

@login_requerido(cargo_necessario='admin')
def deletar_produto_view(id):
    produto = Produto.query.get(id)
    if produto:
        db.session.delete(produto)
        db.session.commit()
        flash("Produto removido!")
    return redirect(url_for('admin.gerenciar_cardapio_view'))