from flask import render_template, request, redirect, url_for, flash
from database import db
from models import Usuario
from routes.auth import login_requerido
from werkzeug.security import generate_password_hash

@login_requerido(cargo_necessario='admin')
def gerenciar_usuarios_view():
    if request.method == 'POST':
        nome_login = request.form.get('username')
        nome_real = request.form.get('nome_exibicao')
        senha_acesso = request.form.get('password')
        cargo_usuario = request.form.get('cargo')
        
        if nome_login and senha_acesso:
            senha_protegida = generate_password_hash(senha_acesso)
            
            novo_usuario = Usuario(
                username=nome_login,
                nome_exibicao=nome_real,
                senha=senha_protegida,
                cargo=cargo_usuario,
                ativo=True
            )
            
            try:
                db.session.add(novo_usuario)
                db.session.commit()
                flash(f"Usuário {nome_real} cadastrado com sucesso!")
            except Exception as e:
                db.session.rollback()
                flash("Erro ao cadastrar: Usuário já existe.")
            
            return redirect(url_for('admin.gerenciar_usuarios_view'))

    usuarios = Usuario.query.all()
    return render_template("admin_usuarios.html", usuarios=usuarios)

@login_requerido(cargo_necessario='admin')
def excluir_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Proteção: Não deixa o admin excluir a si próprio
    if usuario.username == 'adminprosa':
        flash("Ação negada: Você não pode excluir o administrador principal.")
        return redirect(url_for('admin.gerenciar_usuarios_view'))

    db.session.delete(usuario)
    db.session.commit()
    flash(f"Usuário {usuario.username} removido com sucesso.")
    return redirect(url_for('admin.gerenciar_usuarios_view'))

@login_requerido(cargo_necessario='admin')
def alternar_status_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Proteção: Admin principal sempre ativo
    if usuario.username == 'adminprosa':
        flash("Ação negada: O administrador principal não pode ser desativado.")
        return redirect(url_for('admin.gerenciar_usuarios_view'))

    usuario.ativo = not usuario.ativo
    db.session.commit()
    
    status = "ativado" if usuario.ativo else "desativado"
    flash(f"Usuário {usuario.username} foi {status}.")
    return redirect(url_for('admin.gerenciar_usuarios_view'))

@login_requerido(cargo_necessario='admin')
def mudar_senha_usuario(usuario_id):
    if request.method == 'POST':
        usuario = Usuario.query.get_or_404(usuario_id)
        nova_senha = request.form.get('nova_senha')
        
        if nova_senha:
            usuario.senha = generate_password_hash(nova_senha)
            db.session.commit()
            flash(f"Senha de {usuario.username} alterada com sucesso!")
        
    return redirect(url_for('admin.gerenciar_usuarios_view'))