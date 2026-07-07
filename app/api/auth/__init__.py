from flask import Blueprint
from app.api.auth.controller import login, primeiro_acesso, logout

auth_bp = Blueprint('auth', __name__)

auth_bp.add_url_rule('/login', view_func=login, methods=['GET', 'POST'])
auth_bp.add_url_rule('/primeiro-acesso', endpoint='primeiro_acesso', view_func=primeiro_acesso, methods=['GET', 'POST'])
auth_bp.add_url_rule('/logout', view_func=logout)
