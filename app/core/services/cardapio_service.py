from app.core.models import Produto
from app.infrastructure.extensions import db


class CardapioService:
    @staticmethod
    def adicionar(nome: str, preco: float, categoria: str, precisa_preparo: bool = True) -> Produto:
        nome = (nome or '').strip()
        if not nome:
            raise ValueError("Nome do produto não pode ser vazio.")
        if preco <= 0:
            raise ValueError("Preço deve ser maior que zero.")
        produto = Produto(nome=nome, preco=preco, categoria=categoria, precisa_preparo=precisa_preparo)
        db.session.add(produto)
        db.session.commit()
        return produto

    @staticmethod
    def atualizar(produto_id: int, nome: str, preco: float, categoria: str, precisa_preparo: bool = True) -> Produto:
        nome = (nome or '').strip()
        if not nome:
            raise ValueError("Nome do produto não pode ser vazio.")
        if preco <= 0:
            raise ValueError("Preço deve ser maior que zero.")
        produto = Produto.query.get_or_404(produto_id)
        produto.nome = nome
        produto.preco = preco
        produto.categoria = categoria
        produto.precisa_preparo = precisa_preparo
        db.session.commit()
        return produto

    @staticmethod
    def remover(produto_id: int) -> None:
        produto = Produto.query.get_or_404(produto_id)
        produto.disponivel = False
        db.session.commit()

    @staticmethod
    def reativar(produto_id: int) -> Produto:
        produto = Produto.query.get_or_404(produto_id)
        produto.disponivel = True
        db.session.commit()
        return produto
