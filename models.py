from database import db
from datetime import datetime

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nome_exibicao = db.Column(db.String(100))
    senha = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(20), default='garcom')
    ativo = db.Column(db.Boolean, default=True)
    # Relacionamento para saber quais pedidos este garçom fez
    pedidos = db.relationship('Pedido', backref='atendente', lazy=True)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50))
    disponivel = db.Column(db.Boolean, default=True)

class Mesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Livre') # Livre, Ocupada, Aguardando
    # No futuro, podemos ligar a mesa ao garçom que a abriu aqui

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesa.id'), nullable=False) # Ligação real com a Mesa
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False) # Quem atendeu
    
    item_nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    valor_unitario = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False) # Importante para o Dashboard somar rápido
    
    data = db.Column(db.DateTime, default=datetime.now) # Usando hora local para o faturamento bater
    status = db.Column(db.String(20), default='Pendente') # Pendente, Pago, Cancelado

    # Relacionamento para facilitar a busca da mesa
    mesa_rel = db.relationship('Mesa', backref='pedidos_da_mesa')