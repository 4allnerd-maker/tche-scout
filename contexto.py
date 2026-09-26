"""Reúne os números de um time (os mesmos da aba Análise) em um dicionário pronto para cards e relatório em PDF."""

from __future__ import annotations

import pandas as pd

import analise as an


def _limpa(t: str) -> str:
    return t.replace("**", "")


def contexto_time(time, jogos_sel, gols, cartoes, partidas, subs, comps, ano, mando="Todos", ultimos=0):
    d = an.jogos_do_time(jogos_sel, time, mando, int(ultimos))
    if d.empty:
        return None
    ids = set(d["jogo_id"])
    g = an.gols_do_time(gols, ids, time)
    ct = an.cartoes_do_time(cartoes, ids, time)
    el = an.elenco(partidas, ids, time)
    st_ = subs[subs["jogo_id"].isin(ids) & (subs["equipe"] == time)] if not subs.empty else subs
    liga = an.metricas_liga(jogos_sel, cartoes, mando)
    prim = an.primeiro_gol(d, g) if not g.empty else pd.DataFrame()
    quadro = an.quadro_intervalo(d)
    r = an.resumo(d)
    ins = [_limpa(t) for t in an.insights(time, d, g, ct, el, liga, prim, quadro, st_)]

    faixas = an.por_faixa(g) if not g.empty else pd.DataFrame({"Faixa": an.FAIXAS, "Feitos": 0, "Sofridos": 0})
    tempos = an.por_tempo(g) if not g.empty else pd.DataFrame({"Tempo": ["1º tempo", "2º tempo"], "Feitos": 0, "Sofridos": 0})

    cf = d.groupby("mando").agg(Jogos=("jogo_id", "count"), V=("res", lambda s: (s == "V").sum()), E=("res", lambda s: (s == "E").sum()),
                                D=("res", lambda s: (s == "D").sum()), GP=("gp", "sum"), GC=("gc", "sum"), Pts=("pontos", "sum")).reset_index()
    cf["Pró/jogo"] = (cf["GP"] / cf["Jogos"]).round(2)
    cf["Contra/jogo"] = (cf["GC"] / cf["Jogos"]).round(2)
    cf["Aprov. (%)"] = (cf["Pts"] / (cf["Jogos"] * 3) * 100).round(1)
    cf = cf.rename(columns={"mando": "Mando"})[["Mando", "Jogos", "V", "E", "D", "GP", "GC", "Pró/jogo", "Contra/jogo"]]

    ps = pd.DataFrame()
    if not prim.empty:
        linhas = []
        for rot, chave in (("Marca primeiro", "Pró"), ("Sofre primeiro", "Contra"), ("Sem gols", "Sem gols")):
            x = prim[prim["primeiro"] == chave]
            linhas.append({"Situação": rot, "Jogos": len(x), "Vitórias": int((x.res == "V").sum()), "Empates": int((x.res == "E").sum()),
                           "Derrotas": int((x.res == "D").sum())})
        ps = pd.DataFrame(linhas)

    elenco_top = el.head(16)[["Atleta", "Jogos", "Titular", "Entrou", "Minutos", "Gols", "Amarelos", "Vermelhos"]] if not el.empty else el

    am = int((ct["tipo"] == "amarelo").sum()) if not ct.empty else 0
    vm = int((ct["tipo"] == "vermelho").sum()) if not ct.empty else 0
    dir_ = int((ct.get("detalhe", pd.Series(dtype=str)) == "Cartão Vermelho Direto").sum()) if not ct.empty else 0
    cart = {"amarelos": am, "vermelhos": vm, "amarelos_jogo": am / r["J"], "diretos": dir_, "segundo_amarelo": vm - dir_}

    jj = d.sort_values("data", ascending=False).copy()
    jj["Data"] = jj["data"].dt.strftime("%d/%m/%y")
    jj["Placar"] = jj["gp"].astype(str) + " x " + jj["gc"].astype(str)
    jogos_pdf = pd.DataFrame({"Data": jj["Data"], "Mando": jj["mando"], "Rodada": jj["rodada"].fillna("").astype(str),
                              "Adversário": jj["adversario"], "GP": jj["gp"], "GC": jj["gc"],
                              "GP 1ºT": jj["gp1"].map(lambda v: "" if pd.isna(v) else int(v)),
                              "GC 1ºT": jj["gc1"].map(lambda v: "" if pd.isna(v) else int(v)), "Res.": jj["res"]})
    return {"time": time, "d": d, "g": g, "r": r, "forma": list(d["res"]), "insights": ins, "faixas": faixas, "tempos": tempos,
            "primeiro": ps, "quadro": quadro, "casa_fora": cf, "elenco": elenco_top, "cartoes": cart, "jogos": jogos_pdf,
            "comps": comps, "ano": ano, "recorte": mando + (f" · últimos {int(ultimos)} jogos" if ultimos else ""),
            "liga": liga, "elenco_full": el}
