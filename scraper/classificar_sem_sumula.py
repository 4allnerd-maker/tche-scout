"""
Classifica os jogos do indice que NAO tem sumula, lendo a propria pagina do jogo
no site da FGF, e grava o resultado no games_index.json:

  situacao: "WO"            jogo cancelado com placar 3x0 / 0x3 (W.O.: um time nao
                            compareceu e o adversario recebe a vitoria por 3x0)
            "CANCELADO"     jogo cancelado sem placar (ex.: time desistiu)
            "SEM_SUMULA"    jogo realizado, placar no site, mas sem PDF de sumula
            "A_REALIZAR"    jogo futuro / sem data definida
            "SEM_DADOS"     pagina sem dados (ex.: jogo remarcado, registro antigo)
  mandante, visitante, placar_mandante, placar_visitante (quando o site informa)

Uso: python scraper/classificar_sem_sumula.py
Rode depois de discover_all.py (que pode recriar entradas sem sumula).
"""

from __future__ import annotations

import re
import json
from datetime import date, datetime

from fgf_client import get
from discover_all import load_index, save_index


def _texto(html: str) -> str:
    html = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def _data_slug(slug: str):
    try:
        return datetime.strptime(slug[-10:], "%d-%m-%Y").date()
    except ValueError:
        return None


def _data_do_jogo(entry: dict, texto: str) -> str | None:
    """dd/mm/aaaa: do endereco do jogo ou, se truncado, da ultima 'Alteracao valida' da pagina."""
    d = _data_slug(entry["slug"])
    if d:
        return d.strftime("%d/%m/%Y")
    m = re.search(r"Alterada para Data\s+\d{2}/\d{2}/\d{4}\s+(\d{2}/\d{2}/\d{4})", texto)
    return m.group(1) if m else None


def _times_do_texto(seg: str):
    """A pagina repete o confronto no fim do cabecalho: 'A 2 X 1 B A 2 X 1 B' ou 'A X B A X B'."""
    m = re.search(r"(\S.*?) (\d+) X (\d+) (\S.*?) \1 \2 X \3 \4$", seg.strip())
    if m:
        return m.group(1), m.group(4)
    m = re.search(r"(\S.*?) X (\S.*?) \1 X \2$", seg.strip())
    return (m.group(1), m.group(2)) if m else None


def classificar(entry: dict) -> dict:
    t = _texto(get(entry["jogo_url"]))
    i = t.find("JOGO:")
    j = t.find("Arbitragem", i)
    seg = t[i:j] if i >= 0 and j > i else ""
    cancelado = "Jogo cancelado" in seg
    out = {"data": _data_do_jogo(entry, t), "situacao": None, "mandante": None, "visitante": None,
           "placar_mandante": None, "placar_visitante": None}

    if cancelado:
        # "...Jogo cancelado Jogo cancelado A 3 X 0 B A 3 X 0 B"  (texto duplicado)
        corpo = seg.split("Jogo cancelado")[-1].strip()
        m = re.match(r"(.+?)\s+(\d+)\s+X\s+(\d+)\s+(.+)", corpo)
        if m:
            a, ga, gb, resto = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
            b = resto.split(f" {a} ")[0].strip()
            out.update(mandante=a, visitante=b, placar_mandante=ga, placar_visitante=gb)
            out["situacao"] = "WO" if sorted((ga, gb)) == [0, 3] else "CANCELADO"
        else:
            m = re.match(r"(.+?)\s+X\s+(.+)", corpo)
            if m:
                a, resto = m.group(1), m.group(2)
                out.update(mandante=a, visitante=resto.split(f" {a} ")[0].strip())
            out["situacao"] = "CANCELADO"
        return out

    if not seg or re.search(r"FASE\s*-\s*-", seg):
        out["situacao"] = "SEM_DADOS"
        return out

    d = _data_slug(entry["slug"])
    a_b = _times_do_texto(seg)
    if a_b:
        out["mandante"], out["visitante"] = a_b
    h = re.search(r"(?:Seg|Ter|Qua|Qui|Sex|Sab|Dom), \d{2}/\d{2} (\d{2}:\d{2})", seg)
    out["hora"] = h.group(1) if h else None
    fase_up = re.escape(str(entry.get("fase_nome", "")).upper())
    est = re.search(r"FASE\s+" + fase_up + r"\s+(?P<est>.+?)\s+(?:Seg|Ter|Qua|Qui|Sex|Sab|Dom), \d{2}/\d{2}", seg) if fase_up else None
    if not est:
        est = re.search(r"(?:^|\s)(?P<est>[^,]+?)\s+(?:Seg|Ter|Qua|Qui|Sex|Sab|Dom), \d{2}/\d{2}", seg)
    out["estadio"] = est.group("est").strip() if est else None
    placares = re.findall(r"(\d+)\s+X\s+(\d+)", seg)
    if placares and (d is None or d < date.today()):
        ga, gb = placares[-1]
        out.update(placar_mandante=int(ga), placar_visitante=int(gb), situacao="SEM_SUMULA")
    else:
        out["situacao"] = "A_REALIZAR"
    return out


def main():
    index = load_index()
    pend = [e for e in index.values() if not e.get("sumula_id")]
    print(f"Jogos sem sumula: {len(pend)}")
    for e in pend:
        e.update(classificar(e))
    save_index(index)

    from collections import Counter
    print(Counter((e["ano"], e["situacao"]) for e in pend))
    for e in pend:
        if e["situacao"] in ("WO", "CANCELADO"):
            print(f"  {e['situacao']:9} {e['ano']} {e['competicao_nome']}: {e['mandante']} "
                  f"{e['placar_mandante']} x {e['placar_visitante']} {e['visitante']}")


if __name__ == "__main__":
    main()
