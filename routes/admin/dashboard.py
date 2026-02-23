from flask import render_template
from database import db
from models import Usuario, Pedido, Mesa
from routes.auth import login_requerido
from datetime import datetime
from sqlalchemy import func

@login_requerido(cargo_necessario='admin')
def dashboard_view():
    hoje = datetime.now().date()
    
    # Vendas do dia
    vendas_hoje = db.session.query(func.sum(Pedido.valor_total)).filter(
        func.date(Pedido.data) == hoje,
        Pedido.status == 'Pago'
    ).scalar() or 0.0

    # Mesas ocupadas
    mesas_ativas = Mesa.query.filter_by(status='Ocupada').count()

    # Pedidos do dia
    total_pedidos = Pedido.query.filter(func.date(Pedido.data) == hoje).count()

    # Ticket médio
    ticket_medio = vendas_hoje / total_pedidos if total_pedidos > 0 else 0.0

    # Desempenho funcionário
    desempenho = db.session.query(
        Usuario.nome_exibicao, 
        func.sum(Pedido.valor_total)
    ).join(Pedido).filter(
        func.date(Pedido.data) == hoje
    ).group_by(Usuario.id).all()

    contexto = {
        "vendas_hoje": vendas_hoje,
        "mesas_ativas": mesas_ativas,
        "total_pedidos": total_pedidos,
        "ticket_medio": ticket_medio,
        "data_atual": datetime.now().strftime('%d/%m/%Y'),
        "mais_vendidos": [],
        "desempenho_garcons": [{"nome": d[0], "total_vendas": d[1]} for d in desempenho]
    }
    return render_template('admin_dashboard.html', **contexto)