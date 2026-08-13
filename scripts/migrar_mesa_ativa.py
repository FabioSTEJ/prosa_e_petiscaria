"""
Migração: adiciona a coluna 'ativa' (BOOLEAN, default 1) na tabela mesa.

Permite desativar uma mesa específica (ex.: quebrada, em manutenção) sem
mexer na numeração nem no total de mesas do salão. SQLite suporta
ALTER TABLE ... ADD COLUMN com valor padrão constante diretamente, sem
precisar recriar a tabela.

Execute: python scripts/migrar_mesa_ativa.py
"""
import shutil
import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'comandas.db')
BACKUP_PATH = DB_PATH + '.backup'


def main():
    if not os.path.exists(DB_PATH):
        print("Banco não encontrado. Nada a migrar.")
        sys.exit(0)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(mesa)")
    colunas = [linha[1] for linha in cur.fetchall()]
    if 'ativa' in colunas:
        print("Coluna 'ativa' já existe. Nada a migrar.")
        conn.close()
        return

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backup criado em: {BACKUP_PATH}")

    cur.execute("ALTER TABLE mesa ADD COLUMN ativa BOOLEAN DEFAULT 1 NOT NULL")
    conn.commit()
    conn.close()
    print("Migração concluída: todas as mesas existentes ficaram marcadas como ativas.")
    print("Reinicie o servidor.")


if __name__ == '__main__':
    main()
