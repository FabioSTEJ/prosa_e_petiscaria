"""
Migração: torna usuario_id (pedido) e fechada_por_id (venda) nullable.

SQLite não suporta ALTER COLUMN, então recriamos as tabelas preservando os dados.
Execute: python scripts/migrar_nullable.py
"""
import shutil
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'comandas.db')
BACKUP_PATH = DB_PATH + '.backup'

def main():
    if not os.path.exists(DB_PATH):
        print("Banco não encontrado. Nada a migrar.")
        sys.exit(0)

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup criado em: {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    cur = conn.cursor()

    # ── Migrar tabela pedido ───────────────────────────────────────────────
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='pedido'")
    row = cur.fetchone()
    if row and 'usuario_id' in row[0]:
        print("Migrando tabela 'pedido'...")
        cur.executescript("""
            CREATE TABLE pedido_new (
                id              INTEGER PRIMARY KEY,
                mesa_id         INTEGER NOT NULL REFERENCES mesa(id),
                usuario_id      INTEGER REFERENCES usuario(id),
                item_nome       VARCHAR(100) NOT NULL,
                quantidade      INTEGER DEFAULT 1,
                valor_unitario  FLOAT NOT NULL,
                valor_total     FLOAT NOT NULL,
                data            DATETIME,
                status          VARCHAR(20) DEFAULT 'Pendente'
            );
            INSERT INTO pedido_new
                SELECT id, mesa_id, usuario_id, item_nome, quantidade,
                       valor_unitario, valor_total, data, status
                FROM pedido;
            DROP TABLE pedido;
            ALTER TABLE pedido_new RENAME TO pedido;
        """)
        print("  pedido: OK")

    # ── Migrar tabela venda ────────────────────────────────────────────────
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='venda'")
    row = cur.fetchone()
    if row and 'fechada_por_id' in row[0]:
        print("Migrando tabela 'venda'...")
        cur.executescript("""
            CREATE TABLE venda_new (
                id                  INTEGER PRIMARY KEY,
                mesa_numero         VARCHAR(10) NOT NULL,
                data_abertura       DATETIME NOT NULL,
                data_fechamento     DATETIME,
                valor_total         FLOAT NOT NULL,
                aberta_por_nome     VARCHAR(100),
                fechada_por_id      INTEGER REFERENCES usuario(id),
                observacoes         TEXT
            );
            INSERT INTO venda_new
                SELECT id, mesa_numero, data_abertura, data_fechamento,
                       valor_total, aberta_por_nome, fechada_por_id, observacoes
                FROM venda;
            DROP TABLE venda;
            ALTER TABLE venda_new RENAME TO venda;
        """)
        print("  venda: OK")

    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    print("Migração concluída. Reinicie o servidor.")

if __name__ == '__main__':
    main()
