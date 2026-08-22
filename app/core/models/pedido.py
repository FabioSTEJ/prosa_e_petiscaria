from app.infrastructure.extensions import db
from datetime import datetime


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesa.id'), nullable=False)
    comanda_id = db.Column(db.Integer, db.ForeignKey('comanda.id'), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    item_nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    valor_unitario = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Pendente')
    observacao = db.Column(db.Text, nullable=True)
    precisa_preparo = db.Column(db.Boolean, default=True, nullable=False)

    comanda_rel = db.relationship('Comanda', backref='pedidos')
