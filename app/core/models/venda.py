from app.infrastructure.extensions import db
from datetime import datetime


class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mesa_numero = db.Column(db.String(10), nullable=False)
    data_abertura = db.Column(db.DateTime, nullable=False)
    data_fechamento = db.Column(db.DateTime, default=datetime.now)
    valor_total = db.Column(db.Float, nullable=False)
    aberta_por_nome = db.Column(db.String(100))
    fechada_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    comanda_nome = db.Column(db.String(80), nullable=True)

    def tempo_permanencia(self):
        if self.data_fechamento and self.data_abertura:
            return int((self.data_fechamento - self.data_abertura).total_seconds() / 60)
        return 0
