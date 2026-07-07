from app.infrastructure.extensions import db
from sqlalchemy import func


class Mesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Livre')
    data_abertura = db.Column(db.DateTime, nullable=True)
    aberta_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

    aberta_por = db.relationship('Usuario', foreign_keys=[aberta_por_id])

    def calcular_total(self):
        from app.core.models.pedido import Pedido
        if self.status == 'Livre' or not self.data_abertura:
            return 0.0
        total = db.session.query(func.sum(Pedido.valor_total)).filter(
            Pedido.mesa_id == self.id,
            Pedido.status != 'Cancelado',
            Pedido.data >= self.data_abertura,
        ).scalar()
        return total or 0.0
