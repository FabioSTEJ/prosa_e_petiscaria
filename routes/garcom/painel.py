from flask import render_template
from models import Mesa
from routes.auth import login_requerido

@login_requerido(cargo_necessario='garcom')
def painel_garcom():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return render_template("painel_garcom.html", mesas=mesas)