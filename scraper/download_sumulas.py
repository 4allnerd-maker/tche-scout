"""
Baixa os PDFs das sumulas listadas em data/raw/games_index.json (gerado por
discover_all.py) para data/raw/sumulas/{sumula_id}.pdf.

Uso:
    python scraper/download_sumulas.py
"""

from __future__ import annotations

import json
from pathlib import Path

from fgf_client import download_sumula

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "data" / "raw" / "games_index.json"
SUMULAS_DIR = ROOT / "data" / "raw" / "sumulas"


def main():
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    SUMULAS_DIR.mkdir(parents=True, exist_ok=True)

    pendentes = [e for e in index.values() if e.get("sumula_id")]
    ja_tenho = 0
    baixados = 0
    falhas = []

    print(f"Sumulas com id resolvido: {len(pendentes)}")
    for entry in pendentes:
        sid = entry["sumula_id"]
        dest = SUMULAS_DIR / f"{sid}.pdf"
        if dest.exists() and dest.stat().st_size > 0:
            ja_tenho += 1
            continue
        try:
            ok = download_sumula(sid, str(dest), sumula_url=entry.get("sumula_url"))
        except Exception as e:
            ok = False
            print(f"  ERRO {sid}: {e}")
        if ok:
            baixados += 1
            if baixados % 25 == 0:
                print(f"  ... {baixados} baixados")
        else:
            falhas.append(sid)

    print(f"\nJa existiam: {ja_tenho} | Baixados agora: {baixados} | Falhas: {len(falhas)}")
    if falhas:
        print("IDs com falha:", falhas[:30], "..." if len(falhas) > 30 else "")


if __name__ == "__main__":
    main()
