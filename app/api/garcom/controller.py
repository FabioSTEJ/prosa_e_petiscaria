from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, request
from app.api.decorators import login_requerido
from app.core.models import Mesa, Pedido, Produto, Comanda
from app.core.services.mesa_service import MesaService
from app.core.services.pedido_service import PedidoService
from app.core.services.comanda_service import ComandaService


@login_requerido(cargo_necessario='garcom')
def home_garcom():
    return render_template("garcom/home.html")


def _agrupar_mesas_unidas(mesas_secao):
    """Agrupa mesas unidas (mesmo grupo_id) em clusters adjacentes dentro de
    uma seção do mapa (Ocupadas ou Disponíveis), pra elas aparecerem juntas
    no grid em vez de espalhadas pela ordem numérica pura.

    Cada mesa unida "puxa" as outras do seu grupo pra perto de si: o cluster
    inteiro assume a posição do menor número de mesa do grupo, e dentro dele
    as mesas continuam ordenadas por número. Mesas sem grupo mantêm a
    posição numérica normal, intercaladas entre os clusters — exatamente
    onde a mesa de menor número do grupo apareceria de qualquer forma.

    Retorna uma lista de dicts {'mesas': [...], 'agrupada': bool} — cada um
    vira, no template, um card solto (bloco de 1 mesa não agrupada) ou um
    cluster visual com N cards (mesas unidas).
    """
    numeros_do_grupo = {}
    for mesa in mesas_secao:
        if mesa.grupo_id:
            numeros_do_grupo.setdefault(mesa.grupo_id, []).append(mesa.numero)
    menor_numero_do_grupo = {
        grupo_id: min(numeros) for grupo_id, numeros in numeros_do_grupo.items()
    }

    mesas_ordenadas = sorted(
        mesas_secao,
        key=lambda m: (menor_numero_do_grupo.get(m.grupo_id, m.numero), m.numero),
    )

    blocos = []
    indice_por_grupo = {}
    for mesa in mesas_ordenadas:
        if mesa.grupo_id and mesa.grupo_id in indice_por_grupo:
            blocos[indice_por_grupo[mesa.grupo_id]]['mesas'].append(mesa)
            continue
        bloco = {'mesas': [mesa], 'agrupada': bool(mesa.grupo_id)}
        if mesa.grupo_id:
            indice_por_grupo[mesa.grupo_id] = len(blocos)
        blocos.append(bloco)

    for bloco in blocos:
        if bloco['agrupada']:
            _agregar_bloco(bloco)
    return blocos


_PRIORIDADE_ALERTA = {'pronto': 3, 'preparo': 2, 'pendente': 1, None: 0}


def _agregar_bloco(bloco):
    """Preenche um bloco de mesas unidas com os valores somados/combinados
    que o card único do grupo mostra: soma do consumo, maior prioridade de
    alerta entre as mesas do grupo, soma de comandas abertas, e a mesa de
    menor número como destino do link (qualquer uma do grupo mostra as
    mesmas comandas, já que elas são compartilhadas no nível do grupo)."""
    mesas = sorted(bloco['mesas'], key=lambda m: m.numero)
    bloco['numeros'] = [m.numero for m in mesas]
    bloco['mesa_link_id'] = mesas[0].id
    bloco['total_atual'] = sum(m.total_atual for m in mesas)
    bloco['quantidade_comandas_abertas'] = sum(m.quantidade_comandas_abertas for m in mesas)
    bloco['alerta_tipo'] = max(
        (m.alerta_tipo for m in mesas), key=lambda a: _PRIORIDADE_ALERTA[a], default=None,
    )


@login_requerido(cargo_necessario='garcom')
def painel_garcom():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    for mesa in mesas:
        mesa.alerta_tipo = None
        mesa.total_atual = 0.0
        mesa.quantidade_comandas_abertas = 0
        if mesa.status == 'Ocupada':
            pedidos_cozinha = Pedido.query.join(Comanda).filter(
                Comanda.mesa_id == mesa.id,
                Comanda.status == 'Aberta',
                Pedido.status.in_(['Pendente', 'Em Preparo', 'Pronto']),
            ).all()
            if any(p.status == 'Pronto' for p in pedidos_cozinha):
                mesa.alerta_tipo = 'pronto'
            elif any(p.status == 'Em Preparo' for p in pedidos_cozinha):
                mesa.alerta_tipo = 'preparo'
            elif any(p.status == 'Pendente' for p in pedidos_cozinha):
                mesa.alerta_tipo = 'pendente'
            mesa.total_atual = mesa.calcular_total()
            mesa.quantidade_comandas_abertas = Comanda.query.filter_by(
                mesa_id=mesa.id, status='Aberta',
            ).count()

    ocupadas = [m for m in mesas if m.status == 'Ocupada']
    livres = [m for m in mesas if m.status == 'Livre' and m.ativa]

    ocupadas_blocos = _agrupar_mesas_unidas(ocupadas)
    livres_blocos = _agrupar_mesas_unidas(livres)

    return render_template(
        "garcom/painel.html",
        ocupadas_blocos=ocupadas_blocos,
        livres_blocos=livres_blocos,
        total_ocupadas=len(ocupadas),
        total_livres=len(livres),
    )


@login_requerido(cargo_necessario='garcom')
def detalhe_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    mesas_grupo = [mesa]
    if mesa.grupo_id:
        mesas_grupo = Mesa.query.filter_by(grupo_id=mesa.grupo_id).order_by(Mesa.numero).all()
    comandas = ComandaService.listar_abertas_por_mesa(mesa_id)
    if not comandas:
        quantidade_comandas = Comanda.query.filter_by(mesa_id=mesa.id).count()
        sugestao_nome = f"Comanda {quantidade_comandas + 1}"
        return render_template("garcom/abrir_comanda.html", mesa=mesa, sugestao_nome=sugestao_nome)
    return render_template("garcom/comandas_mesa.html",
                           mesa=mesa, mesas_grupo=mesas_grupo, comandas=comandas)


@login_requerido(cargo_necessario='garcom')
def abrir_comanda(mesa_id):
    try:
        nome = request.form.get('nome', '')
        comanda = ComandaService.abrir(mesa_id, session.get('usuario_id'), nome)
        flash(f"{comanda.nome} aberta com sucesso!")
        return redirect(url_for('garcom.detalhe_comanda', comanda_id=comanda.id))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('garcom.painel_garcom'))


@login_requerido(cargo_necessario='garcom')
def detalhe_comanda(comanda_id):
    comanda = Comanda.query.get_or_404(comanda_id)
    itens_pedido = Pedido.query.filter(
        Pedido.comanda_id == comanda.id,
        Pedido.status != 'Cancelado',
        Pedido.status != 'Finalizado',
    ).all()
    produtos = Produto.query.filter_by(disponivel=True).order_by(Produto.categoria, Produto.nome).all()
    return render_template("garcom/detalhe_comanda.html",
                           comanda=comanda, itens=itens_pedido,
                           total=comanda.calcular_total(), produtos=produtos)


@login_requerido(cargo_necessario='garcom')
def lancar_item(comanda_id):
    if request.method == 'POST':
        produto_id = request.form.get('produto_id')
        observacao = request.form.get('observacao', '')
        try:
            quantidade = int(request.form.get('quantidade', 1))
            pedido = PedidoService.lancar(comanda_id, produto_id, quantidade, session.get('usuario_id'), observacao)
            flash(f"{pedido.item_nome} adicionado!")
        except ValueError as e:
            flash(str(e) or "Quantidade inválida.", "danger")
    return redirect(url_for('garcom.detalhe_comanda', comanda_id=comanda_id))


@login_requerido(cargo_necessario='admin')
def excluir_item(comanda_id, pedido_id):
    PedidoService.excluir(pedido_id)
    flash("Item removido com sucesso.")
    return redirect(url_for('garcom.detalhe_comanda', comanda_id=comanda_id))


@login_requerido(cargo_necessario='admin')
def finalizar_comanda(comanda_id):
    try:
        resultado = ComandaService.finalizar(comanda_id, session.get('usuario_id'))
        if resultado['total'] > 0:
            flash(
                f"{resultado['comanda_nome']} (Mesa {resultado['mesa_numero']}) fechada! "
                f"Total: R$ {resultado['total']:.2f}"
            )
        else:
            flash(f"{resultado['comanda_nome']} (Mesa {resultado['mesa_numero']}) estava vazia.")
        return redirect(url_for('garcom.painel_garcom'))
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('garcom.detalhe_comanda', comanda_id=comanda_id))


@login_requerido(cargo_necessario='garcom')
def tela_unir_mesas():
    mesas = Mesa.query.filter_by(ativa=True).order_by(Mesa.numero).all()
    return render_template("garcom/unir_mesas.html", mesas=mesas)


@login_requerido(cargo_necessario='garcom')
def unir_mesas():
    mesa_ids = request.form.getlist('mesa_ids')
    try:
        MesaService.unir(mesa_ids, session.get('usuario_id'))
        flash("Mesas unidas com sucesso!")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('garcom.painel_garcom'))


@login_requerido(cargo_necessario='garcom')
def desunir_mesa(mesa_id):
    MesaService.desunir_mesa(mesa_id)
    flash("Mesa desunida do grupo.")
    return redirect(url_for('garcom.painel_garcom'))


@login_requerido(cargo_necessario='garcom')
def pedidos_prontos_view():
    # Ordenado por mesa primeiro pra dar pra agrupar os cards por mesa no
    # template; dentro da mesma mesa, mais antigo primeiro.
    pedidos = Pedido.query.join(Comanda).join(Mesa).filter(
        Pedido.status == 'Pronto'
    ).order_by(Mesa.numero, Pedido.data.asc()).all()

    # Mesas unidas viram um bloco único (ex.: "Mesa 01, 02, 04"), e dentro
    # desse bloco os itens são sub-agrupados por comanda — uma mesa unida
    # pode ter várias comandas simultâneas. Isso não dá pra fazer só com
    # `groupby` do Jinja (chave de agrupamento depende de outras mesas do
    # mesmo grupo, não de uma coluna direta), então monta a estrutura aqui.
    numeros_por_grupo = {}
    for mesa in Mesa.query.filter(Mesa.grupo_id.isnot(None)).order_by(Mesa.numero).all():
        numeros_por_grupo.setdefault(mesa.grupo_id, []).append(mesa.numero)

    blocos = []
    indice_por_chave = {}
    for pedido in pedidos:
        mesa = pedido.comanda_rel.mesa_rel
        chave = tuple(numeros_por_grupo[mesa.grupo_id]) if mesa.grupo_id else (mesa.numero,)
        if chave not in indice_por_chave:
            indice_por_chave[chave] = len(blocos)
            blocos.append({'numeros_mesa': chave, 'comandas': {}})
        bloco = blocos[indice_por_chave[chave]]
        bloco['comandas'].setdefault(pedido.comanda_rel, []).append(pedido)

    for bloco in blocos:
        bloco['comandas'] = [
            {'comanda': comanda, 'pedidos': itens}
            for comanda, itens in bloco['comandas'].items()
        ]

    return render_template("garcom/pedidos_prontos.html", blocos=blocos, now=datetime.now())


@login_requerido(cargo_necessario='garcom')
def entregar_pedido(pedido_id):
    try:
        PedidoService.mudar_status(pedido_id, 'Entregue')
        flash("Item marcado como entregue!")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('garcom.pedidos_prontos_view'))
