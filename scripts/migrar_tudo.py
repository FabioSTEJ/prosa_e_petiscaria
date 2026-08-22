"""
Roda todos os scripts de migracao (scripts/migrar_*.py) em sequencia.

Cada migracao individual e idempotente: verifica antes se ja foi aplicada e,
se sim, nao faz nada. Por isso e seguro rodar este script sempre que a
aplicacao for atualizada, mesmo que nenhuma migracao nova exista — as ja
aplicadas simplesmente sao puladas.

Uso (sempre antes de subir uma versao nova em producao):
  python scripts/migrar_tudo.py

Se uma migracao falhar, a execucao para imediatamente (fail-fast): migracoes
mais novas podem depender do schema deixado pelas anteriores.
"""
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime

PASTA_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ESTE_ARQUIVO = os.path.abspath(__file__)
DB_PATH = os.path.join(PASTA_SCRIPTS, '..', 'data', 'comandas.db')


def _backup_geral():
    if not os.path.exists(DB_PATH):
        return
    carimbo = datetime.now().strftime('%Y%m%d_%H%M%S')
    destino = f"{DB_PATH}.backup.antes_de_atualizar_{carimbo}"
    shutil.copy2(DB_PATH, destino)
    print(f"Backup geral (antes de qualquer migracao) criado em: {destino}\n")


def main():
    candidatos = sorted(glob.glob(os.path.join(PASTA_SCRIPTS, 'migrar_*.py')))
    migracoes = [c for c in candidatos if os.path.abspath(c) != ESTE_ARQUIVO]

    if not migracoes:
        print("Nenhum script de migracao encontrado em scripts/.")
        return

    _backup_geral()
    print(f"Encontradas {len(migracoes)} migracao(oes). Executando em ordem alfabetica:\n")

    for caminho in migracoes:
        nome = os.path.basename(caminho)
        print(f"--- {nome} ---")
        resultado = subprocess.run([sys.executable, caminho])
        if resultado.returncode != 0:
            print(f"\nFALHOU: {nome} terminou com codigo {resultado.returncode}. Parando.")
            sys.exit(1)
        print()

    print("Todas as migracoes foram executadas (aplicadas ou puladas por ja existirem).")


if __name__ == '__main__':
    main()
