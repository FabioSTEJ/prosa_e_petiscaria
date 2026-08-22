"""
Migração: adiciona a coluna 'precisa_preparo' (BOOLEAN, default 1) nas
tabelas produto e pedido.

Permite marcar produtos que não passam pela cozinha (ex.: cerveja, bebidas
prontas) — o garçom lança, pega e entrega direto, sem gerar fila no painel
da cozinha. SQLite suporta ALTER TABLE ... ADD COLUMN com valor padrão
constante diretamente, sem precisar recriar a tabela.

Execute: python scripts/migrar_precisa_preparo.py
"""
import shutil
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'comandas.db')
BACKUP_PATH = DB_PATH + '.backup.migrar_precisa_preparo'


def _adicionar_coluna_se_faltando(cur, tabela):
    cur.execute(f"PRAGMA table_info({tabela})")
    colunas = [linha[1] for linha in cur.fetchall()]
    if 'precisa_preparo' in colunas:
        print(f"Coluna 'precisa_preparo' já existe em '{tabela}'. Pulando.")
        return False
    cur.execute(f"ALTER TABLE {tabela} ADD COLUMN precisa_preparo BOOLEAN DEFAULT 1 NOT NULL")
    print(f"Coluna 'precisa_preparo' adicionada em '{tabela}'.")
    return True


def main():
    if not os.path.exists(DB_PATH):
        print("Banco não encontrado. Nada a migrar.")
        sys.exit(0)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(produto)")
    produto_falta = 'precisa_preparo' not in [l[1] for l in cur.fetchall()]
    cur.execute("PRAGMA table_info(pedido)")
    pedido_falta = 'precisa_preparo' not in [l[1] for l in cur.fetchall()]

    if not produto_falta and not pedido_falta:
        print("Nada a migrar.")
        conn.close()
        return

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup criado em: {BACKUP_PATH}")

    _adicionar_coluna_se_faltando(cur, 'produto')
    _adicionar_coluna_se_faltando(cur, 'pedido')

    conn.commit()
    conn.close()
    print("Migração concluída: todos os produtos/pedidos existentes ficaram marcados como 'precisa_preparo = True'.")
    print("Reinicie o servidor.")


if __name__ == '__main__':
    main()
