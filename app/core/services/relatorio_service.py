from datetime import datetime, date
from sqlalchemy import func
from app.core.models import Usuario, Pedido, Mesa, Venda
from app.infrastructure.extensions import db


class RelatorioService:
    @staticmethod
    def dashboard(data_iso: str = None) -> dict:
        if data_iso:
            try:
                dia_alvo = datetime.strptime(data_iso, '%Y-%m-%d').date()
            except ValueError:
                dia_alvo = date.today()
        else:
            dia_alvo = date.today()

        vendas_total = db.session.query(func.sum(Venda.valor_total)).filter(
            func.date(Venda.data_fechamento) == dia_alvo
        ).scalar() or 0.0

        mesas_ativas = Mesa.query.filter_by(status='Ocupada').count()
        total_pedidos = Pedido.query.filter(
            func.date(Pedido.data) == dia_alvo,
            Pedido.status != 'Cancelado',
        ).count()

        total_encerradas = Venda.query.filter(func.date(Venda.data_fechamento) == dia_alvo).count()
        ticket_medio = vendas_total / total_encerradas if total_encerradas else 0.0

        permanencia_vendas = Venda.query.filter(func.date(Venda.data_fechamento) == dia_alvo).all()
        permanencia_media = 0
        if permanencia_vendas:
            permanencia_media = sum(v.tempo_permanencia() for v in permanencia_vendas) / len(permanencia_vendas)

        mais_vendidos = db.session.query(
            Pedido.item_nome, func.sum(Pedido.quantidade).label('total_qtd')
        ).filter(
            func.date(Pedido.data) == dia_alvo, Pedido.status != 'Cancelado'
        ).group_by(Pedido.item_nome).order_by(func.sum(Pedido.quantidade).desc()).limit(5).all()

        desempenho = db.session.query(
            Usuario.nome_exibicao, func.sum(Pedido.valor_total)
        ).join(Pedido, Usuario.id == Pedido.usuario_id).filter(
            func.date(Pedido.data) == dia_alvo, Pedido.status != 'Cancelado'
        ).group_by(Usuario.id).order_by(func.sum(Pedido.valor_total).desc()).all()

        return {
            "vendas_hoje": vendas_total,
            "mesas_ativas": mesas_ativas,
            "total_pedidos": total_pedidos,
            "ticket_medio": ticket_medio,
            "permanencia_media": int(permanencia_media),
            "data_atual": dia_alvo.strftime('%d/%m/%Y'),
            "data_iso": dia_alvo.isoformat(),
            "mais_vendidos": [{"nome": i[0], "quantidade": int(i[1])} for i in mais_vendidos],
            "desempenho_garcons": [{"nome": d[0], "total_vendas": d[1]} for d in desempenho],
        }

    @staticmethod
    def historico_vendas(data_filtro: str = None) -> dict:
        if not data_filtro:
            data_filtro = date.today().strftime('%Y-%m-%d')
        try:
            data_obj = datetime.strptime(data_filtro, '%Y-%m-%d').date()
        except ValueError:
            data_filtro = date.today().strftime('%Y-%m-%d')
            data_obj = date.today()
        vendas = Venda.query.filter(
            db.func.date(Venda.data_fechamento) == data_obj
        ).order_by(Venda.data_fechamento.desc()).all()
        return {
            "vendas": vendas,
            "faturamento_total": sum(v.valor_total for v in vendas),
            "data_selecionada": data_filtro,
        }
