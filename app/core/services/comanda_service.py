from datetime import datetime
from app.core.models import Comanda, Mesa, Pedido, Venda, Usuario
from app.infrastructure.extensions import db


class ComandaService:
    @staticmethod
    def abrir(mesa_id: int, usuario_id: int, nome: str = None) -> Comanda:
        """Abre uma nova comanda ancorada na mesa. Marca a mesa como Ocupada."""
        mesa = Mesa.query.get_or_404(mesa_id)
        if not mesa.ativa:
            raise ValueError(f"Mesa {mesa.numero} está desativada e não pode ser aberta.")
        nome = (nome or '').strip()
        if not nome:
            quantidade_comandas = Comanda.query.filter_by(mesa_id=mesa.id).count()
            nome = f"Comanda {quantidade_comandas + 1}"
        comanda = Comanda(
            mesa_id=mesa.id,
            nome=nome,
            status='Aberta',
            data_abertura=datetime.now(),
            aberta_por_id=usuario_id,
        )
        db.session.add(comanda)
        mesa.status = 'Ocupada'
        db.session.commit()
        return comanda

    @staticmethod
    def finalizar(comanda_id: int, usuario_id: int) -> dict:
        """Retorna {'mesa_numero': str, 'comanda_nome': str, 'total': float}."""
        comanda = Comanda.query.get_or_404(comanda_id)
        mesa = comanda.mesa_rel
        itens = Pedido.query.filter(
            Pedido.comanda_id == comanda.id,
            Pedido.status != 'Cancelado',
            Pedido.status != 'Finalizado',
        ).all()

        nao_entregues = [i for i in itens if i.status != 'Entregue']
        if nao_entregues:
            raise ValueError(
                f"Não é possível fechar a comanda: {len(nao_entregues)} item(ns) ainda "
                "não foram entregues ao cliente."
            )

        total = 0.0
        if itens:
            total = comanda.calcular_total()
            usuario_abriu = Usuario.query.get(comanda.aberta_por_id)
            nome_abriu = usuario_abriu.nome_exibicao if usuario_abriu else "Sistema"
            resumo = "|||".join(
                f"{i.quantidade}::{i.item_nome}::{i.valor_unitario:.2f}::{i.valor_total:.2f}"
                for i in itens
            )
            db.session.add(Venda(
                mesa_numero=mesa.numero,
                comanda_nome=comanda.nome,
                data_abertura=comanda.data_abertura or datetime.now(),
                data_fechamento=datetime.now(),
                valor_total=total,
                aberta_por_nome=nome_abriu,
                fechada_por_id=usuario_id,
                observacoes=resumo,
                grupo_mesa_id=mesa.grupo_id,
            ))
            for item in itens:
                item.status = 'Finalizado'

        comanda.status = 'Finalizada'
        comanda.data_fechamento = datetime.now()

        outras_abertas = Comanda.query.filter(
            Comanda.mesa_id == mesa.id,
            Comanda.status == 'Aberta',
            Comanda.id != comanda.id,
        ).count()
        if outras_abertas == 0:
            mesa.status = 'Livre'

        db.session.commit()
        return {'mesa_numero': mesa.numero, 'comanda_nome': comanda.nome, 'total': total}

    @staticmethod
    def listar_abertas_por_mesa(mesa_id: int) -> list:
        """Lista comandas abertas ancoradas na mesa (ou em todo o grupo de mesas unidas)."""
        mesa = Mesa.query.get_or_404(mesa_id)
        if mesa.grupo_id:
            mesa_ids = [m.id for m in Mesa.query.filter_by(grupo_id=mesa.grupo_id).all()]
        else:
            mesa_ids = [mesa.id]
        return Comanda.query.filter(
            Comanda.mesa_id.in_(mesa_ids),
            Comanda.status == 'Aberta',
        ).all()
