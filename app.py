from flask import Flask, render_template, request, redirect, url_for, flash, session # Adicione session aquifrom flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from livereload import Server
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'petiscaria_secreta_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comandas.db'
db = SQLAlchemy(app)

# Modelo do Banco de Dados
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mesa = db.Column(db.String(10), nullable=False)
    item = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pendente') 
    # Pendente, Pronto, Entregue

# banco de usuarios
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(20), default='garcom') # 'admin' ou 'garcom'

# Rode isso no terminal para atualizar o banco se necessário:
# with app.app_context(): db.create_all()
# Criar o banco de dados
with app.app_context():
    db.create_all()


def login_requerido(cargo_necessario=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verifica se existe alguém logado na sessão
            if 'usuario_id' not in session:
                flash("Por favor, faça login para acessar esta página.")
                return redirect(url_for('login'))
            
            # Se a rota exige um cargo específico (ex: admin) e o usuário não tem
            if cargo_necessario and session.get('cargo') != cargo_necessario:
                flash("Acesso negado: Você não tem permissão de administrador.")
                return redirect(url_for('login'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_input = request.form.get('username')
        pwd_input = request.form.get('password')
        
        # Busca o usuário no banco de dados
        usuario = Usuario.query.filter_by(username=user_input).first()
        
        if usuario and usuario.senha == pwd_input:
            # Guardamos as informações na sessão
            session['usuario_id'] = usuario.id
            session['username'] = usuario.username
            session['cargo'] = usuario.cargo
            
            # Redireciona dependendo do cargo
            if usuario.cargo == 'admin':
                return redirect(url_for('gerenciar_usuarios'))
            else:
                return redirect(url_for('painel_garcom')) # Vamos criar essa rota logo
        else:
            flash("Usuário ou senha inválidos!")
            
    return render_template("login.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))



@app.route("/admin/usuarios", methods=['GET', 'POST'])
@login_requerido(cargo_necessario='admin') # <--- Só entra se for Admin
def gerenciar_usuarios():
    if request.method == 'POST':
        novo_nome = request.form.get('username')
        nova_senha = request.form.get('password')
        tipo = request.form.get('cargo') # Pegando o cargo do formulário
        
        if novo_nome and nova_senha:
            novo_usuario = Usuario(username=novo_nome, senha=nova_senha, cargo=tipo)
            db.session.add(novo_usuario)
            db.session.commit()
            flash(f"Usuário {novo_nome} cadastrado como {tipo}!")
            return redirect(url_for('gerenciar_usuarios'))

    usuarios = Usuario.query.all()
    return render_template("admin_usuarios.html", usuarios=usuarios)

@app.route("/garcom/painel")
@login_requerido(cargo_necessario='garcom') # <--- Só entra se for Garçom
def painel_garcom():
    return render_template("painel_garcom.html")

@app.route("/admin/painel")
@login_requerido(cargo_necessario='admin')
def painel_admin():
    return render_template("index_admin.html")

# Lembre-se de atualizar a rota de login para redirecionar para 'painel_admin' 
# em vez de 'gerenciar_usuarios' diretamente!

@app.route("/")
def home():
    return redirect(url_for('login'))

if __name__ == "__main__":
    server = Server(app.wsgi_app)
    server.watch('static/css/*.css')
    server.watch('templates/*.html')
    server.serve(port=5500, debug=True) # <--- Tem que ser PORT 5500