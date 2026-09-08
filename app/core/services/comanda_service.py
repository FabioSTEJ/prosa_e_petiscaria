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
    def _itens_pendentes(comanda) -> list:
        """Itens da comanda ainda não cancelados/finalizados (candidatos a bloquear o fechamento)."""
        return Pedido.query.filter(
            Pedido.comanda_id == comanda.id,
            Pedido.status != 'Cancelado',
            Pedido.status != 'Finalizado',
        ).all()

    @staticmethod
    def _aplicar_finalizacao(comanda, itens, usuario_id) -> float:
        """Cria a Venda (se houver itens) e marca itens/comanda como finalizados.
        Não mexe em mesa.status nem commita — isso fica a cargo do chamador."""
        mesa = comanda.mesa_rel
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
        return total

    @staticmethod
    def finalizar(comanda_id: int, usuario_id: int) -> dict:
        """Retorna {'mesa_numero': str, 'comanda_nome': str, 'total': float}."""
        comanda = Comanda.query.get_or_404(comanda_id)
        mesa = comanda.mesa_rel
        itens = ComandaService._itens_pendentes(comanda)

        nao_entregues = [i for i in itens if i.status != 'Entregue']
        if nao_entregues:
            raise ValueError(
                f"Não é possível fechar a comanda: {len(nao_entregues)} item(ns) ainda "
                "não foram entregues ao cliente."
            )

        total = ComandaService._aplicar_finalizacao(comanda, itens, usuario_id)

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
    def finalizar_grupo(mesa_id: int, usuario_id: int) -> dict:
        """Finaliza de uma vez todas as comandas abertas da mesa (ou do grupo de
        mesas unidas). Validação tudo-ou-nada: se qualquer comanda tiver item
        ainda não entregue, nenhuma é finalizada.

        Retorna {'mesas_numeros': [...], 'total_geral': float, 'quantidade_comandas': int}.
        """
        comandas = ComandaService.listar_abertas_por_mesa(mesa_id)

        itens_por_comanda = {}
        nomes_bloqueando = []
        for comanda in comandas:
            itens = ComandaService._itens_pendentes(comanda)
            itens_por_comanda[comanda.id] = itens
            if any(i.status != 'Entregue' for i in itens):
                nomes_bloqueando.append(comanda.nome)

        if nomes_bloqueando:
            raise ValueError(
                "Não é possível fechar o grupo: "
                f"{', '.join(nomes_bloqueando)} ainda tem item(ns) não entregue(s)."
            )

        total_geral = 0.0
        for comanda in comandas:
            total_geral += ComandaService._aplicar_finalizacao(
                comanda, itens_por_comanda[comanda.id], usuario_id,
            )

        mesa = Mesa.query.get_or_404(mesa_id)
        if mesa.grupo_id:
            mesas_grupo = Mesa.query.filter_by(grupo_id=mesa.grupo_id).all()
        else:
            mesas_grupo = [mesa]
        for m in mesas_grupo:
            m.status = 'Livre'

        db.session.commit()
        return {
            'mesas_numeros': [m.numero for m in mesas_grupo],
            'total_geral': total_geral,
            'quantidade_comandas': len(comandas),
        }

    @staticmethod
    def mover(comanda_id: int, nova_mesa_id: int) -> Comanda:
        """Move uma comanda aberta pra outra mesa ativa, atualizando os
        pedidos vinculados e o status de ocupação de origem/destino."""
        comanda = Comanda.query.get_or_404(comanda_id)
        if comanda.status != 'Aberta':
            raise ValueError("Só é possível mover uma comanda que está aberta.")

        mesa_destino = Mesa.query.get_or_404(nova_mesa_id)
        if not mesa_destino.ativa:
            raise ValueError(f"Mesa {mesa_destino.numero} está desativada e não pode receber comandas.")

        if nova_mesa_id == comanda.mesa_id:
            raise ValueError("A comanda já está nessa mesa.")

        mesa_origem = comanda.mesa_rel

        comanda.mesa_id = nova_mesa_id
        Pedido.query.filter_by(comanda_id=comanda.id).update({'mesa_id': nova_mesa_id})
        mesa_destino.status = 'Ocupada'

        outras_abertas = Comanda.query.filter(
            Comanda.mesa_id == mesa_origem.id,
            Comanda.status == 'Aberta',
            Comanda.id != comanda.id,
        ).count()
        if outras_abertas == 0:
            mesa_origem.status = 'Livre'

        db.session.commit()
        return comanda

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
