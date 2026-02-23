from flask import render_template, session, redirect, url_for, flash, request
from database import db
from models import Mesa, Pedido, Produto, Venda, Usuario
from routes.auth import login_requerido
from datetime import datetime

@login_requerido(cargo_necessario='garcom')
def detalhe_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    
    if mesa.status == 'Livre':
        return render_template("garcom_abrir_mesa.html", mesa=mesa)
    
    # Buscamos apenas os itens que ainda não foram "arquivados" em uma venda anterior
    itens_pedido = Pedido.query.filter_by(mesa_id=mesa.id, status='Pendente').all()
    produtos = Produto.query.filter_by(disponivel=True).all()
    total_mesa = sum(item.valor_total for item in itens_pedido)
    
    return render_template("garcom_pedido.html", 
                           mesa=mesa, 
                           itens=itens_pedido, 
                           total=total_mesa,
                           produtos=produtos)

@login_requerido(cargo_necessario='garcom')
def abrir_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    if mesa.status == 'Livre':
        mesa.status = 'Ocupada'
        # Gravamos o momento exato da abertura e quem abriu
        mesa.data_abertura = datetime.now()
        mesa.aberta_por_id = session.get('usuario_id')
        db.session.commit()
        flash(f"Mesa {mesa.numero} aberta com sucesso!")
    
    return redirect(url_for('garcom.detalhe_mesa', mesa_id=mesa.id))

@login_requerido(cargo_necessario='garcom')
def lancar_item(mesa_id):
    if request.method == 'POST':
        produto_id = request.form.get('produto_id')
        quantidade = int(request.form.get('quantidade', 1))
        
        produto = Produto.query.get(produto_id)
        if produto:
            novo_pedido = Pedido(
                mesa_id=mesa_id,
                usuario_id=session.get('usuario_id'),
                item_nome=produto.nome,
                quantidade=quantidade,
                valor_unitario=produto.preco,
                valor_total=produto.preco * quantidade,
                status='Pendente'
            )
            db.session.add(novo_pedido)
            db.session.commit()
            flash(f"{produto.nome} adicionado!")
            
    return redirect(url_for('garcom.detalhe_mesa', mesa_id=mesa_id))

@login_requerido(cargo_necessario='admin')
def excluir_item(mesa_id, pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    db.session.delete(pedido)
    db.session.commit()
    flash("Item removido com sucesso.")
    return redirect(url_for('garcom.detalhe_mesa', mesa_id=mesa_id))

@login_requerido(cargo_necessario='admin')
def finalizar_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    itens_pendentes = Pedido.query.filter_by(mesa_id=mesa_id, status='Pendente').all()
    
    if itens_pendentes:
        # 1. Calcula o total da comanda
        total_venda = sum(item.valor_total for item in itens_pendentes)
        
        # 2. Busca o nome de quem abriu para o histórico (auditoria)
        usuario_abriu = Usuario.query.get(mesa.aberta_por_id)
        nome_abriu = usuario_abriu.nome_exibicao if usuario_abriu else "Sistema"

        # 3. Cria o registro definitivo na tabela Venda antes de limpar os dados
        venda_historico = Venda(
            mesa_numero=mesa.numero,
            data_abertura=mesa.data_abertura or datetime.now(),
            data_fechamento=datetime.now(),
            valor_total=total_venda,
            aberta_por_nome=nome_abriu,
            fechada_por_id=session.get('usuario_id'),
            observacoes=f"Finalizada com {len(itens_pendentes)} itens."
        )
        db.session.add(venda_historico)

        # 4. Atualiza o status dos itens para 'Finalizado' (ou deleta se preferir economizar espaço)
        for item in itens_pendentes:
            item.status = 'Finalizado'
            
        flash(f"Mesa {mesa.numero} fechada! Total: R$ {total_venda:.2f}")
    else:
        flash(f"Mesa {mesa.numero} estava vazia.")

    # 5. Limpa a mesa para o próximo cliente
    mesa.status = 'Livre'
    mesa.data_abertura = None
    mesa.aberta_por_id = None
    
    db.session.commit()
    return redirect(url_for('garcom.painel_garcom'))