from datetime import datetime
from sqlalchemy import case
from flask import render_template, request, redirect, url_for, flash
from app.api.decorators import login_requerido
from app.core.models import Usuario, Produto, Mesa, Pedido
from app.infrastructure.extensions import db
from app.core.services.auth_service import AuthService
from app.core.services.cardapio_service import CardapioService
from app.core.services.mesa_service import MesaService
from app.core.services.pedido_service import PedidoService
from app.core.services.relatorio_service import RelatorioService


@login_requerido(cargo_necessario='admin')
def dashboard_view():
    dados = RelatorioService.dashboard(
        request.args.get('data_inicio'), request.args.get('data_fim'),
    )
    return render_template('admin/dashboard.html', **dados)


@login_requerido(cargo_necessario='admin')
def historico_vendas_view():
    dados = RelatorioService.historico_vendas(request.args.get('data_venda'))
    return render_template('admin/vendas.html', **dados)


@login_requerido(cargo_necessario='cozinha')
def painel_cozinha():
    prioridade_status = case(
        (Pedido.status == 'Pendente', 0),
        (Pedido.status == 'Em Preparo', 1),
        (Pedido.status == 'Pronto', 2),
        else_=3,
    )
    pedidos_ativos = Pedido.query.filter(
        Pedido.status.in_(['Pendente', 'Em Preparo', 'Pronto']),
        Pedido.precisa_preparo == True,
    ).order_by(prioridade_status, Pedido.data.asc()).all()
    return render_template('admin/cozinha.html', pedidos=pedidos_ativos, now=datetime.now())


@login_requerido(cargo_necessario='cozinha')
def mudar_status(pedido_id, novo_status):
    try:
        pedido = PedidoService.mudar_status(pedido_id, novo_status)
        comanda = pedido.comanda_rel
        numero_mesa = comanda.mesa_rel.numero
        if novo_status == 'Cancelado':
            flash(f"Item {pedido.item_nome} da Mesa {numero_mesa} / {comanda.nome} CANCELADO.", "warning")
        elif novo_status == 'Entregue':
            flash(f"Item entregue na Mesa {numero_mesa} / {comanda.nome}.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('admin.painel_cozinha'))


@login_requerido(cargo_necessario='admin')
def gerenciar_usuarios_view():
    if request.method == 'POST':
        try:
            AuthService.criar_usuario(
                username=request.form.get('username'),
                nome_exibicao=request.form.get('nome_exibicao'),
                senha=request.form.get('password'),
                cargo=request.form.get('cargo'),
            )
            flash(f"Usuário {request.form.get('nome_exibicao')} cadastrado com sucesso!")
        except Exception:
            db.session.rollback()
            flash("Erro ao cadastrar: Usuário já existe.")
        return redirect(url_for('admin.gerenciar_usuarios_view'))
    return render_template("admin/usuarios.html", usuarios=Usuario.query.all())


@login_requerido(cargo_necessario='admin')
def excluir_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if usuario.username == 'admin':
        flash("Ação negada: Não é possível excluir o administrador principal.")
        return redirect(url_for('admin.gerenciar_usuarios_view'))
    AuthService.excluir_usuario(usuario)
    flash(f"Usuário {usuario.username} removido.")
    return redirect(url_for('admin.gerenciar_usuarios_view'))


@login_requerido(cargo_necessario='admin')
def alternar_status_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if usuario.username == 'admin':
        flash("Ação negada: O administrador principal não pode ser desativado.")
        return redirect(url_for('admin.gerenciar_usuarios_view'))
    ativo = AuthService.alternar_status(usuario_id)
    flash(f"Usuário {usuario.username} {'ativado' if ativo else 'desativado'}.")
    return redirect(url_for('admin.gerenciar_usuarios_view'))


@login_requerido(cargo_necessario='admin')
def mudar_senha_usuario(usuario_id):
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        if nova_senha:
            AuthService.resetar_senha(usuario_id, nova_senha)
            usuario = Usuario.query.get(usuario_id)
            flash(f"Senha de {usuario.username} redefinida. O usuário deverá trocá-la no próximo acesso.")
    return redirect(url_for('admin.gerenciar_usuarios_view'))


@login_requerido(cargo_necessario='admin')
def gerenciar_cardapio_view():
    if request.method == 'POST':
        nome = request.form.get('nome', '')
        preco_raw = request.form.get('preco', '')
        categoria = request.form.get('categoria', '')
        id_produto = request.form.get('id_produto', '')
        precisa_preparo = request.form.get('precisa_preparo', 'sim') == 'sim'
        if nome and preco_raw:
            try:
                preco = float(preco_raw)
                if id_produto:
                    CardapioService.atualizar(int(id_produto), nome, preco, categoria, precisa_preparo)
                    flash(f"Produto '{nome}' atualizado!")
                else:
                    CardapioService.adicionar(nome, preco, categoria, precisa_preparo)
                    flash(f"Produto '{nome}' adicionado!")
            except ValueError:
                flash("Preço inválido!")
        return redirect(url_for('admin.gerenciar_cardapio_view'))
    ativos = Produto.query.filter_by(disponivel=True).order_by(Produto.categoria, Produto.nome).all()
    inativos = Produto.query.filter_by(disponivel=False).order_by(Produto.categoria, Produto.nome).all()
    return render_template("admin/cardapio.html", produtos=ativos, produtos_inativos=inativos)


@login_requerido(cargo_necessario='admin')
def deletar_produto_view(produto_id):
    CardapioService.remover(produto_id)
    flash("Produto desativado do cardápio. O histórico de vendas foi preservado.")
    return redirect(url_for('admin.gerenciar_cardapio_view'))


@login_requerido(cargo_necessario='admin')
def reativar_produto_view(produto_id):
    produto = CardapioService.reativar(produto_id)
    flash(f"Produto '{produto.nome}' reativado no cardápio!")
    return redirect(url_for('admin.gerenciar_cardapio_view'))


@login_requerido(cargo_necessario='admin')
def gerenciar_mesas_view():
    if request.method == 'POST':
        try:
            msg = MesaService.ajustar_salao(int(request.form.get('quantidade', 0)))
            flash(msg)
        except (ValueError, TypeError) as e:
            flash(str(e))
        return redirect(url_for('admin.gerenciar_mesas_view'))
    mesas = Mesa.query.order_by(Mesa.numero).all()
    consumos = {m.id: m.calcular_total() for m in mesas}
    grupos = {}
    for mesa in mesas:
        if mesa.grupo_id:
            grupos.setdefault(mesa.grupo_id, []).append(mesa.numero)
    return render_template("admin/mesas.html", mesas=mesas, consumos=consumos, grupos=grupos)


@login_requerido(cargo_necessario='admin')
def alternar_ativa_mesa(mesa_id):
    try:
        ativa = MesaService.alternar_ativa(mesa_id)
        mesa = Mesa.query.get(mesa_id)
        flash(f"Mesa {mesa.numero} {'ativada' if ativa else 'desativada'}.")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for('admin.gerenciar_mesas_view'))
