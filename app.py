from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import db
from models import Usuario, Pedido, Produto, Mesa
from functools import wraps
import os
from datetime import datetime
from sqlalchemy import func

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
            nome_exibicao='Administrador',
            senha='petiscaria2026',
            cargo='admin',
            ativo=True
        )
        db.session.add(novo_admin)
        db.session.commit()
        print(">>> SUCESSO: Banco recriado e Admin pronto!")

# Decorator de Segurança
def login_requerido(cargo_necessario=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
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
        
        # verificação de usuario
        usuario = Usuario.query.filter_by(username=user_input, ativo=True).first()
        
        if usuario and usuario.senha == pwd_input:
            session['usuario_id'] = usuario.id
            session['username'] = usuario.username
            session['nome_real'] = usuario.nome_exibicao or usuario.username
            session['cargo'] = usuario.cargo
            
            if usuario.cargo == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('painel_garcom'))
        
        flash("Usuário/Senha inválidos ou conta inativa!")
    return render_template("login.html")

@app.route("/admin/painel")
@login_requerido(cargo_necessario='admin')
def painel_admin():
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@login_requerido(cargo_necessario='admin')
def admin_dashboard():
    hoje = datetime.now().date()
    
    #  vendas do dia
    vendas_hoje = db.session.query(func.sum(Pedido.valor_total)).filter(
        func.date(Pedido.data) == hoje,
        Pedido.status == 'Pago'
    ).scalar() or 0.0

    # mesas ocupadas
    mesas_ativas = Mesa.query.filter_by(status='Ocupada').count()

    # pedidos do dia
    total_pedidos = Pedido.query.filter(func.date(Pedido.data) == hoje).count()

    # ticket medio
    ticket_medio = vendas_hoje / total_pedidos if total_pedidos > 0 else 0.0

    # desempenho funcionario
    desempenho = db.session.query(
        Usuario.nome_exibicao, 
        func.sum(Pedido.valor_total)
    ).join(Pedido).filter(
        func.date(Pedido.data) == hoje
    ).group_by(Usuario.id).all()

    contexto = {
        "vendas_hoje": vendas_hoje,
        "mesas_ativas": mesas_ativas,
        "total_pedidos": total_pedidos,
        "ticket_medio": ticket_medio,
        "data_atual": datetime.now().strftime('%d/%m/%Y'),
        "mais_vendidos": [],
        "desempenho_garcons": [{"nome": d[0], "total_vendas": d[1]} for d in desempenho]
    }
    return render_template('admin_dashboard.html', **contexto)

@app.route("/admin/usuarios", methods=['GET', 'POST'])
@login_requerido(cargo_necessario='admin')
def gerenciar_usuarios():
    if request.method == 'POST':
        nome_login = request.form.get('username')
        nome_real = request.form.get('nome_exibicao')
        senha_acesso = request.form.get('password')
        cargo_usuario = request.form.get('cargo')
        
        if nome_login and senha_acesso:
            novo_usuario = Usuario(
                username=nome_login,
                nome_exibicao=nome_real,
                senha=senha_acesso,
                cargo=cargo_usuario,
                ativo=True
            )
            db.session.add(novo_usuario)
            db.session.commit()
            flash(f"Usuário {nome_real} cadastrado!")
            return redirect(url_for('gerenciar_usuarios'))

    usuarios = Usuario.query.all()
    return render_template("admin_usuarios.html", usuarios=usuarios)

# rota cardapio
@app.route("/admin/cardapio", methods=['GET', 'POST'])
@login_requerido(cargo_necessario='admin')
def gerenciar_cardapio():
    if request.method == 'POST':
        nome = request.form.get('nome')
        preco_raw = request.form.get('preco')
        categoria = request.form.get('categoria')
        
        if nome and preco_raw:
            try:
                preco = float(preco_raw)
                novo_produto = Produto(nome=nome, preco=preco, categoria=categoria)
                db.session.add(novo_produto)
                db.session.commit()
                flash(f"Produto '{nome}' adicionado!")
            except ValueError:
                flash("Preço inválido!")
            return redirect(url_for('gerenciar_cardapio'))

    produtos = Produto.query.order_by(Produto.categoria).all()
    return render_template("admin_cardapio.html", produtos=produtos)

#cardapio delete
@app.route("/admin/cardapio/deletar/<int:id>")
@login_requerido(cargo_necessario='admin')
def deletar_produto(id):
    produto = Produto.query.get(id)
    if produto:
        db.session.delete(produto)
        db.session.commit()
        flash("Produto removido!")
    return redirect(url_for('gerenciar_cardapio'))

# rota mesas adm
@app.route("/admin/mesas", methods=['GET', 'POST'])
@login_requerido(cargo_necessario='admin')
def gerenciar_mesas():
    if request.method == 'POST':
        quantidade_str = request.form.get('quantidade')
        if quantidade_str:
            quantidade = int(quantidade_str)
            # Para evitar erros de FK ao deletar mesas com pedidos, 
            # em um sistema real faríamos um 'soft delete' ou aviso.
            Mesa.query.delete() 
            for i in range(1, quantidade + 1):
                numero_formatado = str(i).zfill(2)
                nova_mesa = Mesa(numero=numero_formatado, status='Livre')
                db.session.add(nova_mesa)
            db.session.commit()
            flash(f"Salão configurado com {quantidade} mesas!")
            return redirect(url_for('gerenciar_mesas'))

    mesas = Mesa.query.order_by(Mesa.numero).all()
    return render_template("admin_mesas.html", mesas=mesas)

# painel funcionario
@app.route("/garcom/painel")
@login_requerido(cargo_necessario='garcom')
def painel_garcom():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return render_template("painel_garcom.html", mesas=mesas)

# rota mesas funcionario
@app.route("/garcom/mesa/<int:mesa_id>")
@login_requerido(cargo_necessario='garcom')
def detalhe_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    
    if mesa.status == 'Livre':
        return render_template("garcom_abrir_mesa.html", mesa=mesa)
    
    # Buscamos TODOS os itens pendentes dessa mesa
    itens_pedido = Pedido.query.filter_by(mesa_id=mesa.id, status='Pendente').all()
    
    # Calculamos o total da mesa para exibir na tela
    total_mesa = sum(item.valor_total for item in itens_pedido)
    
    # Buscamos a lista de produtos para o garçom poder escolher o que lançar
    produtos = Produto.query.filter_by(disponivel=True).all()
    
    return render_template("garcom_pedido.html", 
                           mesa=mesa, 
                           itens=itens_pedido, 
                           total=total_mesa,
                           produtos=produtos)

#rota ocupar mesa
@app.route("/garcom/mesa/abrir/<int:mesa_id>", methods=['POST'])
@login_requerido(cargo_necessario='garcom')
def abrir_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    if mesa.status == 'Livre':
        mesa.status = 'Ocupada'
        db.session.commit() # Apenas muda o status da mesa
        flash(f"Mesa {mesa.numero} aberta! Agora você pode lançar os itens.")
    
    return redirect(url_for('detalhe_mesa', mesa_id=mesa.id))

#rota lançar itens

@app.route("/garcom/mesa/lancar/<int:mesa_id>", methods=['POST'])
@login_requerido(cargo_necessario='garcom')
def lancar_item(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    produto_id = request.form.get('produto_id')
    quantidade = int(request.form.get('quantidade', 1))
    
    produto = Produto.query.get(produto_id)
    if produto:
        # Agora sim criamos o registro no banco com todos os dados obrigatórios
        novo_item = Pedido(
            mesa_id=mesa.id,
            usuario_id=session['usuario_id'],
            item_nome=produto.nome,
            quantidade=quantidade,
            valor_unitario=produto.preco,
            valor_total=produto.preco * quantidade,
            status='Pendente'
        )
        db.session.add(novo_item)
        db.session.commit()
        flash(f"{quantidade}x {produto.nome} adicionado!")
    
    return redirect(url_for('detalhe_mesa', mesa_id=mesa.id))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, port=5500)