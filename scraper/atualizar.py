"""
Atualiza tudo de uma vez (é o que o robo do GitHub Actions roda):
  1. descobre jogos novos no site da FGF        (discover_all.py)
  2. baixa as sumulas novas                     (download_sumulas.py)
  3. classifica jogos sem sumula (W.O. etc.)    (classificar_sem_sumula.py)
  4. reprocessa os datasets                     (build_dataset.py)

Uso: python scraper/atualizar.py [ano ...]     (padrao: ano atual)
"""

import subprocess
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def rodar(script: str, *args: str) -> None:
    print(f"\n=== {script} {' '.join(args)}", flush=True)
    subprocess.run([sys.executable, str(AQUI / script), *args], check=True, cwd=AQUI)


def main():
    anos = sys.argv[1:] or [str(date.today().year)]
    rodar("discover_all.py", *anos)
    rodar("download_sumulas.py")
    rodar("classificar_sem_sumula.py")
    rodar("build_dataset.py")


if __name__ == "__main__":
    main()
