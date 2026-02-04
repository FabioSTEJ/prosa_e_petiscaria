from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import db
from models import Usuario, Pedido, Produto, Mesa
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'petiscaria_secreta_123'

# Configuração do Banco
basdir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basdir, 'comandas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco com o app
db.init_app(app)

# Cria as tabelas e o admin inicial
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(username='adminprosa').first():
        novo_admin = Usuario(
            username='adminprosa',
            nome_exibicao='Administrador', # Adicione isso aqui!
            senha='petiscaria2026',
            cargo='admin'
        )
        db.session.add(novo_admin)
        db.session.commit()
        print(">>> SUCESSO: Banco resetado e Admin criado com nome real!")

# Decorator de Segurança
def login_requerido(cargo_necessario=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                flash("Por favor, faça login.")
                return redirect(url_for('login'))
            if cargo_necessario and session.get('cargo') != cargo_necessario:
                flash("Acesso negado!")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- ROTAS ---

@app.route("/")
def home():
    return redirect(url_for('login'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_input = request.form.get('username')
        pwd_input = request.form.get('password')
        usuario = Usuario.query.filter_by(username=user_input).first()
        
        if usuario and usuario.senha == pwd_input:
            session.update({'usuario_id': usuario.id, 'username': usuario.username, 'cargo': usuario.cargo})
            return redirect(url_for('painel_admin' if usuario.cargo == 'admin' else 'painel_garcom'))
        
        flash("Usuário ou senha inválidos!")
    return render_template("login.html")

@app.route("/admin/painel")
@login_requerido(cargo_necessario='admin')
def painel_admin():
    return render_template("index_admin.html")

@app.route("/admin/usuarios", methods=['GET', 'POST'])
@login_requerido(cargo_necessario='admin')
def gerenciar_usuarios():
    if request.method == 'POST':
        novo_nome = request.form.get('username')
        nova_senha = request.form.get('password')
        tipo = request.form.get('cargo')
        if novo_nome and nova_senha:
            db.session.add(Usuario(username=novo_nome, senha=nova_senha, cargo=tipo))
            db.session.commit()
            flash(f"Usuário {novo_nome} cadastrado!")
    
    usuarios = Usuario.query.all()
    return render_template("admin_usuarios.html", usuarios=usuarios)

@app.route("/admin/cardapio", methods=['GET', 'POST'])
@login_requerido(cargo_necessario='admin')
def gerenciar_cardapio():
    if request.method == 'POST':
        nome = request.form.get('nome')
        preco = float(request.form.get('preco'))
        categoria = request.form.get('categoria')
        
        if nome and preco:
            novo_produto = Produto(nome=nome, preco=preco, categoria=categoria)
            db.session.add(novo_produto)
            db.session.commit()
            flash(f"Produto '{nome}' adicionado com sucesso!")
            return redirect(url_for('gerenciar_cardapio'))

    produtos = Produto.query.all()
    return render_template("admin_cardapio.html", produtos=produtos)

# Rota extra para deletar itens (muito útil!)
@app.route("/admin/cardapio/deletar/<int:id>")
@login_requerido(cargo_necessario='admin')
def deletar_produto(id):
    produto = Produto.query.get(id)
    if produto:
        db.session.delete(produto)
        db.session.commit()
        flash("Produto removido!")
    return redirect(url_for('gerenciar_cardapio'))

@app.route("/admin/mesas", methods=['GET', 'POST'])
@login_requerido(cargo_necessario='admin')
def gerenciar_mesas():
    if request.method == 'POST':
        quantidade = int(request.form.get('quantidade'))
        
        # Limpa as mesas antigas para reconfigurar (opcional, mas evita bagunça)
        # Se preferir apenas adicionar, remova a linha abaixo
        Mesa.query.delete() 
        
        for i in range(1, quantidade + 1):
            nova_mesa = Mesa(numero=str(i), status='Livre')
            db.session.add(nova_mesa)
        
        db.session.commit()
        flash(f"Salão configurado com {quantidade} mesas!")
        return redirect(url_for('gerenciar_mesas'))

    mesas = Mesa.query.all()
    return render_template("admin_mesas.html", mesas=mesas)

@app.route("/garcom/painel")
@login_requerido(cargo_necessario='garcom')
def painel_garcom():
    return render_template("painel_garcom.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, port=5500)