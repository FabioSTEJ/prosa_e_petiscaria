from app.infrastructure.extensions import db


class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50))
    disponivel = db.Column(db.Boolean, default=True)
    precisa_preparo = db.Column(db.Boolean, default=True, nullable=False)
