from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db
from models import Usuario
from functools import wraps
from werkzeug.security import check_password_hash # Importado para verificar a senha criptografada

# Criamos o Blueprint de Autenticação
auth_bp = Blueprint('auth', __name__)

# --- O DECORATOR DE SEGURANÇA ---
def login_requerido(cargo_necessario=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('auth.login'))
            
            # Se um cargo específico é exigido
            if cargo_necessario:
                user_cargo = session.get('cargo')
                # Admin tem acesso a tudo. Se não for admin e não for o cargo exigido, nega.
                if user_cargo != 'admin' and user_cargo != cargo_necessario:
                    flash("Acesso negado: Permissão insuficiente.")
                    return redirect(url_for('auth.login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- ROTAS DE LOGIN/LOGOUT ---

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_input = request.form.get('username')
        pwd_input = request.form.get('password')
        
        usuario = Usuario.query.filter_by(username=user_input, ativo=True).first()
        
        # MODIFICADO: Agora usamos check_password_hash para comparar a senha digitada 
        # com o hash seguro armazenado no banco de dados.
        if usuario and check_password_hash(usuario.senha, pwd_input):
            session['usuario_id'] = usuario.id
            session['username'] = usuario.username
            session['nome_real'] = usuario.nome_exibicao or usuario.username
            session['cargo'] = usuario.cargo
            
            # REDIRECIONAMENTOS ATUALIZADOS PARA OS BLUEPRINTS
            if usuario.cargo == 'admin':
                return redirect(url_for('admin.dashboard_view'))
            else:
                # Modificado para levar à nova página de Boas-Vindas conforme seu pedido
                return redirect(url_for('garcom.home_garcom'))
        
        flash("Usuário/Senha inválidos ou conta inativa!")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.login'))