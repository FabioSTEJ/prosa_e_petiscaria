"""
Migracao: separa Comanda de Mesa (uniao de mesas + contas divididas).

Cria as tabelas 'grupo_mesa' e 'comanda', adiciona 'mesa.grupo_id',
'pedido.comanda_id' e 'venda.comanda_nome'. Faz backfill: para cada mesa
'Ocupada' hoje, cria 1 Comanda ('Comanda 1') ancorada nela, copiando
data_abertura/aberta_por_id, e associa a essa comanda os pedidos da sessao
atual da mesa (mesma inferencia por janela de data que o codigo legado usa:
mesa_id igual, data >= mesa.data_abertura, status fora de
Cancelado/Finalizado). Pedidos historicos ficam com comanda_id NULL — isso e
aceitavel, Venda ja e desnormalizada e nao depende disso.

SQLite nao suporta a maioria dos ALTER TABLE, mas suporta ADD COLUMN e
CREATE TABLE diretamente, sem precisar recriar nenhuma tabela existente.

Execute: python scripts/migrar_comandas.py
"""
import shutil
import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'comandas.db')
BACKUP_PATH = DB_PATH + '.backup.migrar_comandas'


def _coluna_existe(cur, tabela, coluna):
    cur.execute(f"PRAGMA table_info({tabela})")
    return coluna in [linha[1] for linha in cur.fetchall()]


def _tabela_existe(cur, tabela):
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabela,)
    )
    return cur.fetchone() is not None


def main():
    if not os.path.exists(DB_PATH):
        print("Banco não encontrado. Nada a migrar.")
        sys.exit(0)

    conn = sqlite3.connect(DB_PATH, timeout=10)
    cur = conn.cursor()

    grupo_mesa_falta = not _tabela_existe(cur, 'grupo_mesa')
    mesa_grupo_id_falta = not _coluna_existe(cur, 'mesa', 'grupo_id')
    comanda_falta = not _tabela_existe(cur, 'comanda')
    pedido_comanda_id_falta = not _coluna_existe(cur, 'pedido', 'comanda_id')
    venda_comanda_nome_falta = not _coluna_existe(cur, 'venda', 'comanda_nome')

    precisa_migrar = any([
        grupo_mesa_falta,
        mesa_grupo_id_falta,
        comanda_falta,
        pedido_comanda_id_falta,
        venda_comanda_nome_falta,
    ])

    if not precisa_migrar:
        print("Nada a migrar.")
        conn.close()
        return

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup criado em: {BACKUP_PATH}")

    if grupo_mesa_falta:
        cur.execute(
            """
            CREATE TABLE grupo_mesa (
                id INTEGER PRIMARY KEY,
                criado_em DATETIME,
                criado_por_id INTEGER,
                FOREIGN KEY(criado_por_id) REFERENCES usuario(id)
            )
            """
        )
        print("Tabela 'grupo_mesa' criada.")
    else:
        print("Tabela 'grupo_mesa' já existe. Pulando.")

    if mesa_grupo_id_falta:
        cur.execute(
            "ALTER TABLE mesa ADD COLUMN grupo_id INTEGER REFERENCES grupo_mesa(id)"
        )
        print("Coluna 'grupo_id' adicionada em 'mesa'.")
    else:
        print("Coluna 'grupo_id' já existe em 'mesa'. Pulando.")

    if comanda_falta:
        cur.execute(
            """
            CREATE TABLE comanda (
                id INTEGER PRIMARY KEY,
                mesa_id INTEGER NOT NULL,
                nome VARCHAR(80) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'Aberta',
                data_abertura DATETIME NOT NULL,
                data_fechamento DATETIME,
                aberta_por_id INTEGER,
                FOREIGN KEY(mesa_id) REFERENCES mesa(id),
                FOREIGN KEY(aberta_por_id) REFERENCES usuario(id)
            )
            """
        )
        print("Tabela 'comanda' criada.")
    else:
        print("Tabela 'comanda' já existe. Pulando.")

    if pedido_comanda_id_falta:
        cur.execute(
            "ALTER TABLE pedido ADD COLUMN comanda_id INTEGER REFERENCES comanda(id)"
        )
        print("Coluna 'comanda_id' adicionada em 'pedido'.")
    else:
        print("Coluna 'comanda_id' já existe em 'pedido'. Pulando.")

    if venda_comanda_nome_falta:
        cur.execute("ALTER TABLE venda ADD COLUMN comanda_nome VARCHAR(80)")
        print("Coluna 'comanda_nome' adicionada em 'venda'.")
    else:
        print("Coluna 'comanda_nome' já existe em 'venda'. Pulando.")

    conn.commit()

    # Backfill: só roda se 'comanda_id' acabou de ser criada nesta execução,
    # para não duplicar comandas em reexecuções futuras.
    if pedido_comanda_id_falta:
        print("\nIniciando backfill de comandas a partir de mesas ocupadas...")
        cur.execute(
            "SELECT id, data_abertura, aberta_por_id FROM mesa WHERE status = 'Ocupada'"
        )
        mesas_ocupadas = cur.fetchall()
        print(f"{len(mesas_ocupadas)} mesa(s) ocupada(s) encontrada(s).")

        for mesa_id, data_abertura, aberta_por_id in mesas_ocupadas:
            data_abertura_efetiva = data_abertura or datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S.%f'
            )
            cur.execute(
                """
                INSERT INTO comanda (mesa_id, nome, status, data_abertura, data_fechamento, aberta_por_id)
                VALUES (?, ?, 'Aberta', ?, NULL, ?)
                """,
                (mesa_id, 'Comanda 1', data_abertura_efetiva, aberta_por_id),
            )
            comanda_id = cur.lastrowid

            if data_abertura:
                cur.execute(
                    """
                    UPDATE pedido
                    SET comanda_id = ?
                    WHERE mesa_id = ?
                      AND data >= ?
                      AND status NOT IN ('Cancelado', 'Finalizado')
                    """,
                    (comanda_id, mesa_id, data_abertura),
                )
            else:
                cur.execute(
                    """
                    UPDATE pedido
                    SET comanda_id = ?
                    WHERE mesa_id = ?
                      AND status NOT IN ('Cancelado', 'Finalizado')
                    """,
                    (comanda_id, mesa_id),
                )
            print(
                f"  Mesa {mesa_id}: comanda {comanda_id} criada, "
                f"{cur.rowcount} pedido(s) associado(s)."
            )

        conn.commit()
        print("Backfill concluído.")
    else:
        print("Coluna 'comanda_id' já existia antes desta execução. Backfill não repetido.")

    conn.close()
    print("\nMigração concluída.")
    print("Reinicie o servidor.")


if __name__ == '__main__':
    main()
