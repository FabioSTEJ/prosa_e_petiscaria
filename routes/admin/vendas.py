from flask import render_template
from database import db
from models import Venda, Pedido  # Importamos Pedido para buscar os itens relacionados
from routes.auth import login_requerido

@login_requerido(cargo_necessario='admin')
def historico_vendas_view():
    # Buscamos todas as vendas da mais recente para a mais antiga
    vendas = Venda.query.order_by(Venda.data_fechamento.desc()).all()
    
    # Calculamos o faturamento total acumulado
    faturamento_total = sum(v.valor_total for v in vendas)
    
    # DICA: Se você quiser ver os itens exatos, podemos passar uma lógica 
    # que busca pedidos finalizados no mesmo período da venda, 
    # mas por enquanto vamos focar na exibição dos dados da tabela Venda.
    
    return render_template("admin_vendas.html", 
                           vendas=vendas, 
                           faturamento_total=faturamento_total)