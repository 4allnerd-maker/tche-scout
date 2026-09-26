"""
Descobre todos os jogos das competicoes profissionais da FGF (Gauchao, Serie
A2 / Divisao de Acesso, Serie B, Copa FGF, Recopa Gaucha) para os anos
informados, resolve o ID da sumula de cada jogo e grava um indice em
data/raw/games_index.json.

Uso:
    python scraper/discover_all.py [ano1 ano2 ...]
    (default: 2024 2025 2026)

Reexecutar e seguro: jogos ja presentes no indice com sumula_id resolvido
nao sao consultados de novo (a nao ser que --force seja passado).
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

from fgf_client import COMPETICOES_PROFISSIONAL, COMPETICOES_FEMININO, discover_phases, discover_games_in_page, discover_sumula

INDEX_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "games_index.json"


def slug_from_url(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def load_index() -> dict:
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return {}


def save_index(index: dict) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("anos", nargs="*", type=int, default=[2024, 2025, 2026])
    ap.add_argument("--force", action="store_true", help="reconsulta jogos ja resolvidos")
    args = ap.parse_args()

    index = load_index()
    total_novos = 0

    todas = [("profissional", i, n) for i, n in COMPETICOES_PROFISSIONAL.items()] +             [("feminino", i, n) for i, n in COMPETICOES_FEMININO.items()]
    for categoria, comp_id, comp_nome in todas:
        for ano in args.anos:
            print(f"[{comp_nome} {ano}] descobrindo fases...", flush=True)
            try:
                fases = discover_phases(comp_id, ano, categoria)
            except Exception as e:
                print(f"  ERRO ao descobrir fases: {e}")
                continue

            for fase in fases:
                try:
                    jogo_urls = discover_games_in_page(fase["url"])
                except Exception as e:
                    print(f"  ERRO na fase {fase['fase_nome']}: {e}")
                    continue
                print(f"  fase '{fase['fase_nome']}': {len(jogo_urls)} jogos")

                for jogo_url in jogo_urls:
                    slug = slug_from_url(jogo_url)
                    entry = index.get(slug)
                    if entry and entry.get("sumula_id") and not args.force:
                        continue
                    entry = {
                        "slug": slug,
                        "jogo_url": jogo_url,
                        "categoria": categoria,
                        "competicao_id": comp_id,
                        "competicao_nome": comp_nome,
                        "ano": ano,
                        "fase_id": fase["fase_id"],
                        "fase_nome": fase["fase_nome"],
                        "sumula_id": None,
                        "sumula_url": None,
                    }
                    try:
                        sumula_id, sumula_url = discover_sumula(jogo_url)
                    except Exception as e:
                        print(f"    ERRO em {slug}: {e}")
                        sumula_id, sumula_url = None, None
                    entry["sumula_id"] = sumula_id
                    entry["sumula_url"] = sumula_url
                    index[slug] = entry
                    if sumula_id:
                        total_novos += 1
                    save_index(index)  # grava incrementalmente (script pode ser interrompido)

    # Entradas antigas do indice sem sumula que nao aparecem mais nas paginas de
    # fase (jogo remarcado/removido da listagem): tenta resolver direto pela pagina do jogo.
    for entry in index.values():
        if entry["ano"] in args.anos and not entry.get("sumula_id"):
            try:
                sid, surl = discover_sumula(entry["jogo_url"])
            except Exception as e:
                print(f"    ERRO em {entry['slug']}: {e}")
                continue
            if sid:
                entry["sumula_id"], entry["sumula_url"] = sid, surl
                total_novos += 1
    save_index(index)

    resolvidos = sum(1 for e in index.values() if e.get("sumula_id"))
    print(f"\nTotal no indice: {len(index)} jogos | com sumula resolvida: {resolvidos} "
          f"(novos nesta rodada: {total_novos})")


if __name__ == "__main__":
    main()
