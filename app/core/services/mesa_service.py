from datetime import datetime
from app.core.models import Mesa, Pedido, Venda, Usuario
from app.infrastructure.extensions import db


class MesaService:
    @staticmethod
    def abrir(mesa_id: int, usuario_id: int) -> tuple:
        """Retorna (mesa, foi_aberta). foi_aberta é False se já estava ocupada."""
        mesa = Mesa.query.get_or_404(mesa_id)
        if mesa.status != 'Livre':
            return mesa, False
        mesa.status = 'Ocupada'
        mesa.data_abertura = datetime.now()
        mesa.aberta_por_id = usuario_id
        db.session.commit()
        return mesa, True

    @staticmethod
    def finalizar(mesa_id: int, usuario_id: int) -> dict:
        """Retorna {'mesa_numero': str, 'total': float}."""
        mesa = Mesa.query.get_or_404(mesa_id)
        mesa_numero = mesa.numero  # captura antes da limpeza
        itens = Pedido.query.filter(
            Pedido.mesa_id == mesa.id,
            Pedido.status != 'Cancelado',
            Pedido.status != 'Finalizado',
            Pedido.data >= mesa.data_abertura,
        ).all()

        total = 0.0
        if itens:
            total = mesa.calcular_total()
            usuario_abriu = Usuario.query.get(mesa.aberta_por_id)
            nome_abriu = usuario_abriu.nome_exibicao if usuario_abriu else "Sistema"
            resumo = ", ".join(f"{i.quantidade}x {i.item_nome}" for i in itens)
            db.session.add(Venda(
                mesa_numero=mesa_numero,
                data_abertura=mesa.data_abertura or datetime.now(),
                data_fechamento=datetime.now(),
                valor_total=total,
                aberta_por_nome=nome_abriu,
                fechada_por_id=usuario_id,
                observacoes=resumo,
            ))
            for item in itens:
                item.status = 'Finalizado'

        mesa.status = 'Livre'
        mesa.data_abertura = None
        mesa.aberta_por_id = None
        db.session.commit()
        return {'mesa_numero': mesa_numero, 'total': total}

    @staticmethod
    def ajustar_salao(nova_quantidade: int) -> str:
        mesas_atuais = Mesa.query.all()
        total_atual = len(mesas_atuais)
        if nova_quantidade > total_atual:
            for i in range(total_atual + 1, nova_quantidade + 1):
                db.session.add(Mesa(numero=str(i).zfill(2), status='Livre'))
            db.session.commit()
            return f"Salão expandido para {nova_quantidade} mesas."
        if nova_quantidade < total_atual:
            mesas_remover = Mesa.query.filter(Mesa.id > nova_quantidade).all()
            if not all(m.status == 'Livre' for m in mesas_remover):
                raise ValueError("Não é possível remover mesas ocupadas!")
            for m in mesas_remover:
                db.session.delete(m)
            db.session.commit()
            return f"Salão reduzido para {nova_quantidade} mesas."
        return "Nenhuma alteração necessária."
