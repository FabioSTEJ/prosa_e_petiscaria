import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.infrastructure.extensions import db
from app.core.models import Usuario
from werkzeug.security import generate_password_hash


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()
        if not Usuario.query.filter_by(username='admin').first():
            db.session.add(Usuario(
                username='admin',
                senha=generate_password_hash('123'),
                nome_exibicao='Administrador Principal',
                cargo='admin',
                ativo=True,
                primeiro_acesso=True,
            ))
            db.session.commit()
            print("Admin criado. Usuário: admin | Senha inicial: 123")
            print("O primeiro acesso exigirá troca de senha.")
        else:
            print("Usuário 'admin' já existe. Nenhuma alteração feita.")


if __name__ == "__main__":
    seed()
