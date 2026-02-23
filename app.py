import os
from flask import Flask, redirect, url_for
from database import db
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.garcom import garcom_bp 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'petiscaria_secreta_123'

# Configuração do banco
basdir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basdir, 'comandas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Registro dos Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(garcom_bp)

@app.route("/")
def home():
    return redirect(url_for('auth.login'))

if __name__ == "__main__":
    # O db.create_all() aqui garante que o arquivo .db exista, mas não mexe nos dados
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5500)