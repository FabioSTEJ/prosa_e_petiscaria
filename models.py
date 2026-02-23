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
    # Relacionamento para saber quais vendas este admin/garçom fechou
    vendas_finalizadas = db.relationship('Venda', backref='responsavel_fechamento', lazy=True)

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
    
    # Novos campos para controle de tempo e gestão
    data_abertura = db.Column(db.DateTime, nullable=True)
    aberta_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    
    # Relacionamento para facilitar a busca do usuário que abriu
    aberta_por = db.relationship('Usuario', foreign_keys=[aberta_por_id])

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesa.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    item_nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    valor_unitario = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    
    data = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='Pendente') # Pendente, Pago, Cancelado

    mesa_rel = db.relationship('Mesa', backref='pedidos_da_mesa')

# --- NOVA CLASSE PARA GESTÃO E HISTÓRICO ---

class Venda(db.Model):
    """
    Esta tabela armazena o histórico definitivo de cada mesa encerrada.
    É aqui que o Admin tirará os relatórios financeiros.
    """
    id = db.Column(db.Integer, primary_key=True)
    mesa_numero = db.Column(db.String(10), nullable=False)
    
    # Datas para cálculo de permanência
    data_abertura = db.Column(db.DateTime, nullable=False)
    data_fechamento = db.Column(db.DateTime, default=datetime.now)
    
    # Valores financeiros
    valor_total = db.Column(db.Float, nullable=False)
    
    # Quem participou (IDs para auditoria)
    aberta_por_nome = db.Column(db.String(100)) # Guardamos o nome caso o usuário seja deletado
    fechada_por_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Campo para observações (ex: descontos ou motivo de exclusão)
    observacoes = db.Column(db.Text, nullable=True)

    def tempo_permanencia(self):
        """Retorna o tempo que a mesa ficou aberta em minutos"""
        if self.data_fechamento and self.data_abertura:
            delta = self.data_fechamento - self.data_abertura
            return int(delta.total_seconds() / 60)
        return 0