from werkzeug.security import check_password_hash, generate_password_hash
from app.core.models import Usuario
from app.infrastructure.extensions import db


class AuthService:
    @staticmethod
    def autenticar(username: str, senha: str):
        usuario = Usuario.query.filter_by(username=username, ativo=True).first()
        if usuario and check_password_hash(usuario.senha, senha):
            return usuario
        return None

    @staticmethod
    def trocar_senha(usuario: Usuario, nova_senha: str) -> None:
        usuario.senha = generate_password_hash(nova_senha)
        usuario.primeiro_acesso = False
        db.session.commit()

    @staticmethod
    def criar_usuario(username: str, nome_exibicao: str, senha: str, cargo: str) -> Usuario:
        novo = Usuario(
            username=username,
            nome_exibicao=nome_exibicao,
            senha=generate_password_hash(senha),
            cargo=cargo,
            ativo=True,
            primeiro_acesso=True,
        )
        db.session.add(novo)
        db.session.commit()
        return novo

    @staticmethod
    def excluir_usuario(usuario: Usuario) -> None:
        db.session.delete(usuario)
        db.session.commit()

    @staticmethod
    def alternar_status(usuario_id: int) -> bool:
        usuario = Usuario.query.get_or_404(usuario_id)
        usuario.ativo = not usuario.ativo
        db.session.commit()
        return usuario.ativo

    @staticmethod
    def resetar_senha(usuario_id: int, nova_senha: str) -> None:
        usuario = Usuario.query.get_or_404(usuario_id)
        usuario.senha = generate_password_hash(nova_senha)
        usuario.primeiro_acesso = True
        db.session.commit()
