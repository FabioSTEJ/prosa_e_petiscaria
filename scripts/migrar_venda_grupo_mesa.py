"""
Migração: adiciona a coluna 'grupo_mesa_id' (INTEGER, nullable) na tabela venda.

Guarda um snapshot informativo do GrupoMesa.id vigente no momento em que a
comanda foi fechada, permitindo agrupar no Histórico de Vendas as vendas que
pertenciam ao mesmo grupo de mesas unidas — mesmo depois que o GrupoMesa
original tiver sido excluído (ver MesaService.desunir_mesa). Por isso a
coluna é opcional (sem NOT NULL, sem valor default) e SQLite suporta
ALTER TABLE ... ADD COLUMN diretamente, sem precisar recriar a tabela.

Execute: python scripts/migrar_venda_grupo_mesa.py
"""
import shutil
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'comandas.db')
BACKUP_PATH = DB_PATH + '.backup.migrar_venda_grupo_mesa'


def main():
    if not os.path.exists(DB_PATH):
        print("Banco não encontrado. Nada a migrar.")
        sys.exit(0)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(venda)")
    colunas = [linha[1] for linha in cur.fetchall()]
    if 'grupo_mesa_id' in colunas:
        print("Coluna 'grupo_mesa_id' já existe. Nada a migrar.")
        conn.close()
        return

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup criado em: {BACKUP_PATH}")

    cur.execute("ALTER TABLE venda ADD COLUMN grupo_mesa_id INTEGER")
    conn.commit()
    conn.close()
    print("Migração concluída: coluna 'grupo_mesa_id' adicionada à tabela venda (nula para vendas existentes).")
    print("Reinicie o servidor.")


if __name__ == '__main__':
    main()
