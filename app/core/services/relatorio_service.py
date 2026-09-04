from collections import defaultdict
from datetime import datetime, date
from sqlalchemy import func
from app.core.models import Usuario, Pedido, Mesa, Venda
from app.infrastructure.extensions import db


class RelatorioService:
    @staticmethod
    def _parse_data_br(valor):
        if not valor:
            return None
        try:
            return datetime.strptime(valor, '%d/%m/%Y').date()
        except ValueError:
            return None

    @staticmethod
    def dashboard(data_inicio: str = None, data_fim: str = None) -> dict:
        dia_inicio = RelatorioService._parse_data_br(data_inicio) or date.today()
        dia_fim = RelatorioService._parse_data_br(data_fim) or dia_inicio
        if dia_fim < dia_inicio:
            dia_inicio, dia_fim = dia_fim, dia_inicio

        vendas_total = db.session.query(func.sum(Venda.valor_total)).filter(
            func.date(Venda.data_fechamento).between(dia_inicio, dia_fim)
        ).scalar() or 0.0

        mesas_ativas = Mesa.query.filter_by(status='Ocupada').count()
        total_pedidos = Pedido.query.filter(
            func.date(Pedido.data).between(dia_inicio, dia_fim),
            Pedido.status != 'Cancelado',
        ).count()

        total_encerradas = Venda.query.filter(
            func.date(Venda.data_fechamento).between(dia_inicio, dia_fim)
        ).count()
        ticket_medio = vendas_total / total_encerradas if total_encerradas else 0.0

        permanencia_vendas = Venda.query.filter(
            func.date(Venda.data_fechamento).between(dia_inicio, dia_fim)
        ).all()
        permanencia_media = 0
        if permanencia_vendas:
            permanencia_media = sum(v.tempo_permanencia() for v in permanencia_vendas) / len(permanencia_vendas)

        mais_vendidos = db.session.query(
            Pedido.item_nome, func.sum(Pedido.quantidade).label('total_qtd')
        ).filter(
            func.date(Pedido.data).between(dia_inicio, dia_fim), Pedido.status != 'Cancelado'
        ).group_by(Pedido.item_nome).order_by(func.sum(Pedido.quantidade).desc()).limit(5).all()

        desempenho = db.session.query(
            Usuario.nome_exibicao, func.sum(Pedido.valor_total)
        ).join(Pedido, Usuario.id == Pedido.usuario_id).filter(
            func.date(Pedido.data).between(dia_inicio, dia_fim), Pedido.status != 'Cancelado'
        ).group_by(Usuario.id).order_by(func.sum(Pedido.valor_total).desc()).all()

        if dia_inicio == dia_fim:
            data_atual = dia_inicio.strftime('%d/%m/%Y')
        else:
            data_atual = f"{dia_inicio.strftime('%d/%m/%Y')} a {dia_fim.strftime('%d/%m/%Y')}"

        return {
            "vendas_hoje": vendas_total,
            "mesas_ativas": mesas_ativas,
            "total_pedidos": total_pedidos,
            "ticket_medio": ticket_medio,
            "permanencia_media": int(permanencia_media),
            "data_atual": data_atual,
            "data_iso": dia_inicio.isoformat(),
            "data_inicio_br": dia_inicio.strftime('%d/%m/%Y'),
            "data_fim_br": dia_fim.strftime('%d/%m/%Y'),
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
            "linhas": RelatorioService._agrupar_vendas_por_grupo_mesa(vendas),
        }

    @staticmethod
    def _agrupar_vendas_por_grupo_mesa(vendas: list) -> list:
        """Agrupa vendas de mesas unidas (grupo) em uma única linha para o histórico."""
        vendas_por_grupo = defaultdict(list)
        for v in vendas:
            if v.grupo_mesa_id:
                vendas_por_grupo[v.grupo_mesa_id].append(v)

        # só tratamos como "grupo" quando 2+ vendas do mesmo grupo caíram no
        # filtro do dia; uma única venda com grupo_mesa_id não-nulo mas sem
        # "irmãs" no período é só uma venda avulsa comum pra fins de exibição.
        grupos_multiplos = {gid: vs for gid, vs in vendas_por_grupo.items() if len(vs) > 1}
        ids_em_grupo = {v.id for vs in grupos_multiplos.values() for v in vs}

        linhas = []
        for v in vendas:
            if v.id in ids_em_grupo:
                continue
            linhas.append({'tipo': 'individual', 'venda': v})

        for sub_vendas in grupos_multiplos.values():
            mesas_label = '+'.join(sorted({sv.mesa_numero for sv in sub_vendas}))
            atendentes = {sv.aberta_por_nome for sv in sub_vendas if sv.aberta_por_nome}
            atendente_label = next(iter(atendentes)) if len(atendentes) == 1 else 'Vários'
            linhas.append({
                'tipo': 'grupo',
                'mesas_label': mesas_label,
                'atendente_label': atendente_label,
                'total': sum(sv.valor_total for sv in sub_vendas),
                'data_abertura': min(sv.data_abertura for sv in sub_vendas),
                'data_fechamento': max(sv.data_fechamento for sv in sub_vendas),
                'sub_vendas': [
                    {
                        'comanda_nome': sv.comanda_nome or f'Mesa {sv.mesa_numero}',
                        'mesa_numero': sv.mesa_numero,
                        'observacoes': sv.observacoes,
                        'valor_total': sv.valor_total,
                    }
                    for sv in sub_vendas
                ],
            })

        linhas.sort(
            key=lambda l: l['venda'].data_fechamento if l['tipo'] == 'individual' else l['data_fechamento'],
            reverse=True,
        )
        return linhas
