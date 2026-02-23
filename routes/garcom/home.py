from flask import render_template
from routes.auth import login_requerido

@login_requerido(cargo_necessario='garcom')
def home_garcom():
    """
    Função responsável por exibir a página de boas-vindas do Garçom.
    Esta página substitui o mapa de mesas como página inicial.
    """
    return render_template("garcom_home.html")