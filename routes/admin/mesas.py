from flask import render_template, request, redirect, url_for, flash
from database import db
from models import Mesa, Pedido  # Importamos Pedido para calcular o consumo
from routes.auth import login_requerido
from sqlalchemy import func

@login_requerido(cargo_necessario='admin')
def gerenciar_mesas_view():
    if request.method == 'POST':
        quantidade_str = request.form.get('quantidade')
        if quantidade_str:
            try:
                nova_quantidade = int(quantidade_str)
                mesas_atuais = Mesa.query.all()
                total_atual = len(mesas_atuais)

                if nova_quantidade > total_atual:
                    for i in range(total_atual + 1, nova_quantidade + 1):
                        numero_formatado = str(i).zfill(2)
                        nova_mesa = Mesa(numero=numero_formatado, status='Livre')
                        db.session.add(nova_mesa)
                    db.session.commit()
                    flash(f"Salão expandido para {nova_quantidade} mesas.")
                
                elif nova_quantidade < total_atual:
                    mesas_para_remover = Mesa.query.filter(Mesa.id > nova_quantidade).all()
                    pode_remover = all(m.status == 'Livre' for m in mesas_para_remover)
                    
                    if pode_remover:
                        for m in mesas_para_remover:
                            db.session.delete(m)
                        db.session.commit()
                        flash(f"Salão reduzido para {nova_quantidade} mesas.")
                    else:
                        flash("Não é possível remover mesas ocupadas!")
            except ValueError:
                flash("Erro ao processar quantidade.")
            return redirect(url_for('admin.gerenciar_mesas_view'))

    # Lógica para pegar mesas e calcular o total de pedidos pendentes/atendidos de cada uma
    mesas = Mesa.query.order_by(Mesa.numero).all()
    
    # Criamos um dicionário de consumos para facilitar no template
    consumos = {}
    for m in mesas:
        total = db.session.query(func.sum(Pedido.valor_total)).filter(
            Pedido.mesa_id == m.id, 
            Pedido.status != 'Finalizado'  # Só conta o que ainda não foi pago
        ).scalar()
        consumos[m.id] = total or 0.0

    return render_template("admin_mesas.html", mesas=mesas, consumos=consumos)