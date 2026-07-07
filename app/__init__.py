from flask import Flask, redirect, url_for, session
from dotenv import load_dotenv
from app.infrastructure.extensions import db, socketio
from app.infrastructure.config import DevelopmentConfig

load_dotenv()


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

    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    return app
