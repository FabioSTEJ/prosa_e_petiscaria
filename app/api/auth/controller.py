from flask import render_template, request, redirect, url_for, flash, session
from app.core.models import Usuario
from app.core.services.auth_service import AuthService

_DESTINO_POR_CARGO = {
    'admin': 'admin.dashboard_view',
    'cozinha': 'admin.painel_cozinha',
}


def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        usuario = AuthService.autenticar(username, password)
        if usuario:
            session.update({
                'usuario_id': usuario.id,
                'username': usuario.username,
                'nome_real': usuario.nome_exibicao or usuario.username,
                'cargo': usuario.cargo,
            })
            if usuario.primeiro_acesso:
                return redirect(url_for('auth.primeiro_acesso'))
            destino = _DESTINO_POR_CARGO.get(usuario.cargo, 'garcom.home_garcom')
            return redirect(url_for(destino))
        flash("Usuário/Senha inválidos ou conta inativa!")
    return render_template("auth/login.html")


def primeiro_acesso():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    usuario = Usuario.query.get(session['usuario_id'])
    if usuario is None:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha', '')
        confirmar = request.form.get('confirmar_senha', '')
        if nova_senha != confirmar:
            flash("As senhas não coincidem!")
        elif len(nova_senha) < 6:
            flash("A senha deve ter no mínimo 6 caracteres.")
        else:
            AuthService.trocar_senha(usuario, nova_senha)
            flash("Senha atualizada com sucesso! Bem-vindo ao sistema.")
            destino = _DESTINO_POR_CARGO.get(usuario.cargo, 'garcom.home_garcom')
            return redirect(url_for(destino))
    return render_template("auth/primeiro_acesso.html")


def logout():
    session.clear()
    return redirect(url_for('auth.login'))
