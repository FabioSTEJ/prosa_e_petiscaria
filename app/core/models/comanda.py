from app.infrastructure.extensions import db
from sqlalchemy import func
from datetime import datetime


class Comanda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesa.id'), nullable=False)
    nome = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Aberta')
    data_abertura = db.Column(db.DateTime, nullable=False, default=datetime.now)
    data_fechamento = db.Column(db.DateTime, nullable=True)
    aberta_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    mesa_rel = db.relationship('Mesa', foreign_keys=[mesa_id])
    aberta_por = db.relationship('Usuario', foreign_keys=[aberta_por_id])

    def calcular_total(self):
        from app.core.models.pedido import Pedido
        total = db.session.query(func.sum(Pedido.valor_total)).filter(
            Pedido.comanda_id == self.id,
            Pedido.status != 'Cancelado',
        ).scalar()
        return total or 0.0
