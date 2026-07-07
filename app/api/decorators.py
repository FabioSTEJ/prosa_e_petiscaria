from functools import wraps
from flask import session, redirect, url_for, flash, request
from app.core.models import Usuario


def login_requerido(cargo_necessario=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('auth.login'))
            usuario = Usuario.query.get(session['usuario_id'])
            if usuario and usuario.primeiro_acesso and request.endpoint != 'auth.primeiro_acesso':
                return redirect(url_for('auth.primeiro_acesso'))
            if cargo_necessario:
                if session.get('cargo') != 'admin' and session.get('cargo') != cargo_necessario:
                    flash("Acesso negado: Permissão insuficiente.")
                    return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
