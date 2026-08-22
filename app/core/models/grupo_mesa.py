from app.infrastructure.extensions import db
from datetime import datetime


class GrupoMesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    criado_em = db.Column(db.DateTime, default=datetime.now)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
