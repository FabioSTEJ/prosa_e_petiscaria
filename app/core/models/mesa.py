from app.infrastructure.extensions import db


class Mesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Livre')
    ativa = db.Column(db.Boolean, default=True, nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo_mesa.id'), nullable=True)
    data_abertura = db.Column(db.DateTime, nullable=True)
    aberta_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    aberta_por = db.relationship('Usuario', foreign_keys=[aberta_por_id])

    def calcular_total(self):
        from app.core.models.comanda import Comanda
        comandas_abertas = Comanda.query.filter_by(mesa_id=self.id, status='Aberta').all()
        return sum(c.calcular_total() for c in comandas_abertas)
