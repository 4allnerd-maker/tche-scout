"""Notícias do Tchê Scout: posts escritos manualmente (transferências, artigos) + resumos de rodada
gerados automaticamente a partir dos dados. Os posts manuais ficam em data/manual/noticias.json,
versionado no repositório — para publicar um novo, peça para o administrador incluir/atualizar o arquivo."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ARQUIVO = Path(__file__).resolve().parent / "data" / "manual" / "noticias.json"
CATEGORIAS = ["Resultados", "Transferências", "Artigo", "Convocação", "Bastidores"]
ICONE_CAT = {"Resultados": "🏆", "Transferências": "🔁", "Artigo": "📝", "Convocação": "📣", "Bastidores": "🎙️"}


def posts_manuais() -> list[dict]:
    if not ARQUIVO.exists():
        return []
    try:
        posts = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    for p in posts:
        p["auto"] = False
    return posts


def _recap_rodada(jogos: pd.DataFrame, comp: str, ano: int, rodada) -> dict | None:
    r = jogos[(jogos["competicao_nome"] == comp) & (jogos["ano"] == ano) & (jogos["rodada"] == rodada)]
    r = r.dropna(subset=["gols_mandante", "gols_visitante"])
    if r.empty:
        return None
    r = r.sort_values("data")
    linhas = "\n".join(f"- **{x.time_mandante} {int(x.gols_mandante)} x {int(x.gols_visitante)} {x.time_visitante}**"
                       + (" _(W.O.)_" if x.situacao == "W.O." else "") for x in r.itertuples())
    gols_total = int((r["gols_mandante"] + r["gols_visitante"]).sum())
    maior = r.assign(dif=(r["gols_mandante"] - r["gols_visitante"]).abs()).sort_values("dif", ascending=False).iloc[0]
    data_post = r["data"].max()
    titulo = f"{comp} {ano}: os resultados da rodada {rodada}"
    resumo = f"{len(r)} jogos, {gols_total} gols. Maior goleada: {maior.time_mandante} {int(maior.gols_mandante)} x {int(maior.gols_visitante)} {maior.time_visitante}."
    corpo = f"Confira os resultados da rodada {rodada} do {comp} {ano}:\n\n{linhas}\n\nAo todo, {gols_total} gols em {len(r)} jogos nesta rodada."
    return {"id": f"recap-{comp}-{ano}-{rodada}".replace(" ", "-").lower(), "data": data_post.strftime("%Y-%m-%d"),
            "categoria": "Resultados", "titulo": titulo, "resumo": resumo, "corpo": corpo, "autor": "Tchê Scout",
            "tags": [comp, str(ano), f"Rodada {rodada}"], "auto": True, "comp": comp, "ano": ano, "rodada": rodada}


def gerar_recaps(jogos: pd.DataFrame, max_posts: int = 12) -> list[dict]:
    """Um post por rodada numerada das competições masculinas principais, mais recentes primeiro."""
    if jogos.empty:
        return []
    alvo = jogos[jogos["categoria"] == "Masculino"].dropna(subset=["rodada"])
    alvo = alvo[alvo["rodada"].astype(str).str.isdigit()]
    if alvo.empty:
        return []
    ultimo_ano = int(alvo["ano"].max())
    alvo = alvo[alvo["ano"] == ultimo_ano]
    combos = alvo[["competicao_nome", "ano", "rodada"]].drop_duplicates()
    combos["rodada_n"] = combos["rodada"].astype(int)
    combos = combos.sort_values(["ano", "rodada_n"], ascending=[False, False])
    posts = []
    for _, c in combos.iterrows():
        p = _recap_rodada(jogos, c["competicao_nome"], c["ano"], c["rodada"])
        if p:
            posts.append(p)
        if len(posts) >= max_posts:
            break
    return posts


def feed(jogos: pd.DataFrame | None = None, max_auto: int = 12) -> pd.DataFrame:
    posts = posts_manuais() + (gerar_recaps(jogos, max_auto) if jogos is not None else [])
    if not posts:
        return pd.DataFrame(columns=["id", "data", "categoria", "titulo", "resumo", "corpo", "autor", "tags", "auto"])
    df = pd.DataFrame(posts)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["tags"] = df["tags"].apply(lambda t: t if isinstance(t, list) else [])
    return df.sort_values("data", ascending=False).reset_index(drop=True)
