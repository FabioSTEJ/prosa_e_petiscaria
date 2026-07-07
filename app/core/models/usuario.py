from app.infrastructure.extensions import db


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nome_exibicao = db.Column(db.String(100))
    senha = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(20), default='garcom')
    ativo = db.Column(db.Boolean, default=True)
    primeiro_acesso = db.Column(db.Boolean, default=True)

    pedidos = db.relationship('Pedido', backref='atendente', lazy=True)
    vendas_finalizadas = db.relationship('Venda', backref='responsavel_fechamento', lazy=True)
