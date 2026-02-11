from flask import redirect, url_for, flash
from database import db
from models import Mesa

def abrir_mesa_handler(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    if mesa.status == 'Livre':
        mesa.status = 'Ocupada'
        db.session.commit()
        flash(f"Mesa {mesa.numero} aberta!")
    return redirect(url_for('garcom.detalhe_mesa', mesa_id=mesa.id))