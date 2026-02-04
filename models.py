from database import db
from datetime import datetime

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False) # Login
    nome_exibicao = db.Column(db.String(100)) # Nome que aparece na tela
    senha = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(20), default='garcom')
    # No futuro, aqui entrarão os campos de pontos/comissões

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50)) # Ex: Bebidas, Petiscos
    disponivel = db.Column(db.Boolean, default=True)

class Mesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Livre') # Livre, Ocupada, Aguardando Pagamento

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mesa = db.Column(db.String(10), nullable=False)
    item = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pendente')