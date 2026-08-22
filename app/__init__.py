from flask import Flask, redirect, url_for, session, jsonify
from dotenv import load_dotenv

load_dotenv()

from app.infrastructure.extensions import db, socketio
from app.infrastructure.config import DevelopmentConfig
from app.api.decorators import login_requerido


def _contar_pedidos_sidebar():
    prontos = 0
    pendentes = 0
    try:
        from app.core.models.pedido import Pedido
        if session.get('cargo') in ('admin', 'garcom'):
            prontos = Pedido.query.filter_by(status='Pronto').count()
        if session.get('cargo') in ('admin', 'cozinha'):
            pendentes = Pedido.query.filter_by(status='Pendente').count()
    except Exception:
        pass
    return {'pedidos_prontos_count': prontos, 'pedidos_pendentes_count': pendentes}


def create_app(config_class=DevelopmentConfig):
    app = Flask(
        __name__,
        template_folder='presentation/templates',
        static_folder='presentation/static',
    )
    app.config.from_object(config_class)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    from app.api.auth import auth_bp
    from app.api.admin import admin_bp
    from app.api.garcom import garcom_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(garcom_bp)

    @app.context_processor
    def inject_sidebar_data():
        return _contar_pedidos_sidebar()

    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    @app.route('/contadores-sidebar')
    @login_requerido()
    def contadores_sidebar():
        """Contagem atual de pedidos prontos/pendentes, em JSON — usado pelo
        JS da sidebar pra atualizar os badges em tempo real via Socket.IO
        sem precisar recarregar a página (a sidebar existe em toda tela,
        inclusive telas com formulário em andamento, onde um reload
        perderia o que o usuário estava digitando)."""
        return jsonify(_contar_pedidos_sidebar())

    return app
