"""
Confere as sumulas de TODAS as competicoes de 2026 (profissional + feminino)
contra o indice de jogos da FGF e gera, em data/sumulas_2026/:

  <Competicao>/<data> - <Mandante> x <Visitante> (R<rodada>|<fase>).pdf
      copias legiveis das sumulas (as originais em data/raw/sumulas/{id}.pdf
      continuam intactas, pois o pipeline usa o ID como nome do arquivo)
  _conferencia.csv
      um registro por jogo do site: status, placar, arquivo, etc.

Antes: rode discover_all.py 2026 e download_sumulas.py.
Uso: python scraper/organizar_2026.py
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

from parse_sumula import parse_sumula_pdf

ANO = 2026
ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "raw" / "games_index.json"
RAW = ROOT / "data" / "raw" / "sumulas"
OUT = ROOT / "data" / "sumulas_2026"

# Ajustes manuais (chave: nome sem UF, minusculo)
SIGLAS = {
    "brasil de farroupilha": "Bra F",
    "gremio esportivo brasil saf": "Bra P",  # Brasil de Pelotas
    "grêmio esportivo brasil saf": "Bra P",
    "brasil de pelotas": "Bra P",
    "santa cruz": "Sta C",
    "união frederiquense": "Uni F",
    "passo fundo": "Pas F",
    "guarani-va": "Gua V",  # Guarani de Venancio Aires
    "guarany": "Gua B", "guarany fc": "Gua B",  # Guarany de Bage
    "brasil": "Bra P",
    "apafut": "Apa",
    "internacional sm": "Int SM",
    "clube 1992": "C1992",
    "s.e.r. cruz alta.": "SER CA",
    "ec flamengo de são pedro": "Fla SP",
    "monsoon fc": "Mon",
}
IGNORAR = {"de", "da", "do", "dos", "das", "e", "ec", "fc", "ee", "ad", "sc", "saf", "esporte", "clube", "esportivo"}


def limpa(nome: str) -> str:
    return re.sub(r"\s*/\s*[A-Z]{2}\s*$", "", nome).strip()


def sigla_base(nome: str) -> str:
    n = limpa(nome)
    if n.lower() in SIGLAS:
        return SIGLAS[n.lower()]
    palavras = [p for p in re.split(r"[\s\-]+", n) if p]
    uteis = [p for p in palavras if p.lower() not in IGNORAR] or palavras
    if len(uteis) == 1:
        return uteis[0][:3].capitalize()
    return f"{uteis[0][:3].capitalize()} {uteis[-1][0].upper()}"


def data_do_slug(slug: str) -> date:
    try:
        return datetime.strptime(slug[-10:], "%d-%m-%Y").date()
    except ValueError:
        return date.max  # jogo sem data definida no site


def seguro(nome: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "-", nome)


def main():
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    jogos = [e for e in idx.values() if e["ano"] == ANO]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    hoje = date.today()
    parsed_por_id, erros = {}, {}
    for e in jogos:
        sid = e.get("sumula_id")
        pdf = RAW / f"{sid}.pdf" if sid else None
        if pdf and pdf.exists() and pdf.read_bytes()[:4] == b"%PDF":
            try:
                d = parse_sumula_pdf(pdf)
                assert d["time_mandante"] and d["time_visitante"] and d["data"]
                assert d["resultado_final_mandante"] is not None
                assert len(d["jogadores"]) >= 10
                parsed_por_id[sid] = d
            except Exception as ex:
                erros[sid] = repr(ex)

    # siglas unicas por competicao (colisao -> usa 2 letras da ultima palavra)
    siglas = defaultdict(dict)
    times_por_comp = defaultdict(set)
    for e in jogos:
        d = parsed_por_id.get(e.get("sumula_id"))
        if d:
            times_por_comp[e["competicao_nome"]] |= {d["time_mandante"], d["time_visitante"]}
    for comp, times in times_por_comp.items():
        bases = defaultdict(list)
        for t in times:
            bases[sigla_base(t)].append(t)
        for b, ts in bases.items():
            explicitos = all(limpa(t).lower() in SIGLAS for t in ts)
            for k, t in enumerate(sorted(ts)):
                siglas[comp][t] = b if (len(ts) == 1 or explicitos) else f"{b}{k + 1}"

    linhas = []
    for e in sorted(jogos, key=lambda e: (e["competicao_nome"], data_do_slug(e["slug"]), e["slug"])):
        sid = e.get("sumula_id")
        linha = {"competicao": e["competicao_nome"], "fase": e["fase_nome"], "slug": e["slug"],
                 "data_site": "" if data_do_slug(e["slug"]) == date.max else data_do_slug(e["slug"]).isoformat(), "sumula_id": sid or "",
                 "mandante": "", "visitante": "", "rodada": "", "placar": "", "arquivo": "", "status": ""}
        d = parsed_por_id.get(sid)
        if d:
            dt = datetime.strptime(d["data"], "%d/%m/%Y").date().isoformat()
            m, v = siglas[e["competicao_nome"]][d["time_mandante"]], siglas[e["competicao_nome"]][d["time_visitante"]]
            marca = f"R{d['rodada']}" if str(d.get("rodada") or "").isdigit() and e["fase_nome"] in ("Classificatória", "1ª Fase", "2ª Fase")                 else e["fase_nome"]
            nome = seguro(f"{dt} - {m} x {v} ({marca}).pdf")
            pasta = OUT / seguro(e["competicao_nome"])
            pasta.mkdir(exist_ok=True)
            if (pasta / nome).exists():
                nome = nome.replace(".pdf", f" [{sid}].pdf")
            shutil.copy2(RAW / f"{sid}.pdf", pasta / nome)
            linha.update(mandante=d["time_mandante"], visitante=d["time_visitante"], rodada=d["rodada"],
                         arquivo=f"{seguro(e['competicao_nome'])}/{nome}", status="OK",
                         placar=f"{d['resultado_final_mandante']}x{d['resultado_final_visitante']}")
        elif sid in erros:
            linha["status"] = f"ERRO NO PDF: {erros[sid]}"
        elif sid:
            linha["status"] = "FALTA BAIXAR"
        elif data_do_slug(e["slug"]) >= hoje:
            linha["status"] = "JOGO AINDA NAO REALIZADO"
        else:
            linha["status"] = "SEM SUMULA NO SITE (verificar: reagendado/adiado?)"
        linhas.append(linha)

    with open(OUT / "_conferencia.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]), delimiter=";")
        w.writeheader()
        w.writerows(linhas)

    por_comp = defaultdict(Counter)
    for l in linhas:
        por_comp[l["competicao"]][l["status"]] += 1
    for c, cnt in por_comp.items():
        print(c, dict(cnt))
    print("\nSIGLAS:")
    for c, mp in siglas.items():
        print(" ", c, {limpa(k): v for k, v in mp.items()})


if __name__ == "__main__":
    main()
