"""Métricas de arbitragem a partir das súmulas: disciplina, pênaltis, acréscimos e viés de mando.
Sem juízo de valor: são números descritivos, sempre com o tamanho da amostra."""

from __future__ import annotations

import numpy as np
import pandas as pd

from stats import FAIXAS, faixa_minuto


def base_por_jogo(jogos: pd.DataFrame, cartoes: pd.DataFrame, gols: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por jogo com árbitro e contagens de cartões, pênaltis e gols."""
    j = jogos[(jogos["situacao"] == "Realizado") & jogos["arbitro"].notna()].copy()
    if j.empty:
        return j
    c = cartoes[cartoes["jogo_id"].isin(set(j["jogo_id"]))]
    ca = c[c["tipo"] == "amarelo"].groupby("jogo_id").size()
    cv = c[c["tipo"] == "vermelho"].groupby("jogo_id").size()
    j["amarelos"] = j["jogo_id"].map(ca).fillna(0).astype(int)
    j["vermelhos"] = j["jogo_id"].map(cv).fillna(0).astype(int)
    # amarelos do mandante x visitante
    cj = c[c["tipo"] == "amarelo"].merge(j[["jogo_id", "time_mandante"]], on="jogo_id")
    cj["mandante"] = cj["equipe"] == cj["time_mandante"]
    am_m = cj[cj["mandante"]].groupby("jogo_id").size()
    j["amarelos_mandante"] = j["jogo_id"].map(am_m).fillna(0).astype(int)
    j["amarelos_visitante"] = j["amarelos"] - j["amarelos_mandante"]
    g = gols[gols["jogo_id"].isin(set(j["jogo_id"]))]
    pen = g[g["tipo"] == "PN"].groupby("jogo_id").size()
    j["penaltis_convertidos"] = j["jogo_id"].map(pen).fillna(0).astype(int)
    j["gols_total"] = (j["gols_mandante"] + j["gols_visitante"]).astype(int)
    j["res_mandante"] = np.where(j["gols_mandante"] > j["gols_visitante"], "V",
                                 np.where(j["gols_mandante"] == j["gols_visitante"], "E", "D"))
    return j


def tabela_arbitros(base: pd.DataFrame, minimo: int = 1) -> pd.DataFrame:
    if base.empty:
        return pd.DataFrame()
    g = base.groupby("arbitro")
    t = g.agg(Jogos=("jogo_id", "count"), Vínculo=("arbitro_vinculo", lambda s: s.mode().iloc[0] if s.notna().any() else ""),
              Amarelos=("amarelos", "sum"), Vermelhos=("vermelhos", "sum"), Gols=("gols_total", "sum"),
              Pênaltis=("penaltis_convertidos", "sum"),
              am_m=("amarelos_mandante", "sum"), am_v=("amarelos_visitante", "sum"),
              ac1=("acrescimo_1t", "mean"), ac2=("acrescimo_2t", "mean"),
              vit_m=("res_mandante", lambda s: (s == "V").mean() * 100),
              var=("tem_var", "mean")).reset_index()
    t["Amarelos/jogo"] = (t["Amarelos"] / t["Jogos"]).round(2)
    t["Vermelhos/jogo"] = (t["Vermelhos"] / t["Jogos"]).round(2)
    t["Cartões/jogo"] = ((t["Amarelos"] + t["Vermelhos"]) / t["Jogos"]).round(2)
    t["Gols/jogo"] = (t["Gols"] / t["Jogos"]).round(2)
    t["Pênaltis conv./jogo"] = (t["Pênaltis"] / t["Jogos"]).round(2)
    t["Amarelos mandante/jogo"] = (t["am_m"] / t["Jogos"]).round(2)
    t["Amarelos visitante/jogo"] = (t["am_v"] / t["Jogos"]).round(2)
    t["Acréscimo 1ºT (min)"] = t["ac1"].round(1)
    t["Acréscimo 2ºT (min)"] = t["ac2"].round(1)
    t["Vitória mandante (%)"] = t["vit_m"].round(0)
    t["Jogos com VAR (%)"] = (t["var"] * 100).round(0)
    t = t[t["Jogos"] >= minimo].rename(columns={"arbitro": "Árbitro"})
    cols = ["Árbitro", "Vínculo", "Jogos", "Amarelos/jogo", "Vermelhos/jogo", "Cartões/jogo", "Amarelos", "Vermelhos",
            "Pênaltis conv./jogo", "Gols/jogo", "Acréscimo 1ºT (min)", "Acréscimo 2ºT (min)", "Amarelos mandante/jogo",
            "Amarelos visitante/jogo", "Vitória mandante (%)", "Jogos com VAR (%)"]
    return t[cols].sort_values("Jogos", ascending=False).reset_index(drop=True)


def insights_arbitragem(base: pd.DataFrame, tab: pd.DataFrame) -> list[str]:
    if base.empty or tab.empty:
        return []
    out = []
    n_j, n_a = len(base), base["arbitro"].nunique()
    am, vm = base["amarelos"].mean(), base["vermelhos"].mean()
    out.append(f"**Panorama:** {n_j} jogos apitados por {n_a} árbitros — média de {am:.2f} amarelos e {vm:.2f} vermelhos por jogo.")
    if len(tab) >= 3:
        rig = tab.sort_values("Cartões/jogo", ascending=False).iloc[0]
        bra = tab.sort_values("Cartões/jogo").iloc[0]
        out.append(f"**Mais rigoroso:** {rig['Árbitro']} ({rig['Cartões/jogo']} cartões por jogo em {rig['Jogos']} jogos). "
                   f"**Mais brando:** {bra['Árbitro']} ({bra['Cartões/jogo']} em {bra['Jogos']} jogos).")
        ver = tab.sort_values("Vermelhos", ascending=False).iloc[0]
        if ver["Vermelhos"] > 0:
            out.append(f"**Mais expulsões:** {ver['Árbitro']} aplicou {int(ver['Vermelhos'])} vermelhos em {ver['Jogos']} jogos.")
        acr = tab.dropna(subset=["Acréscimo 2ºT (min)"]).sort_values("Acréscimo 2ºT (min)", ascending=False)
        if not acr.empty:
            a = acr.iloc[0]
            out.append(f"**Maior acréscimo no 2º tempo:** {a['Árbitro']} (média de {a['Acréscimo 2ºT (min)']} min); "
                       f"média geral: {base['acrescimo_2t'].mean():.1f} min.")
    casa, fora = base["amarelos_mandante"].mean(), base["amarelos_visitante"].mean()
    dif = fora - casa
    if abs(dif) >= 0.2:
        lado = "visitantes" if dif > 0 else "mandantes"
        out.append(f"**Mando:** em média, {lado} recebem mais amarelos ({fora:.2f} visitante × {casa:.2f} mandante por jogo).")
    else:
        out.append(f"**Mando:** amarelos equilibrados entre mandante ({casa:.2f}) e visitante ({fora:.2f}) por jogo.")
    var = base["tem_var"].mean() * 100
    if var > 0:
        out.append(f"**VAR:** presente em {var:.0f}% dos jogos da seleção.")
    return out


def cartoes_por_faixa(cartoes: pd.DataFrame, ids: set) -> pd.DataFrame:
    c = cartoes[cartoes["jogo_id"].isin(ids)].copy()
    out = pd.DataFrame({"Faixa": FAIXAS})
    if c.empty:
        out["Amarelos"] = 0
        out["Vermelhos"] = 0
        return out
    c["faixa"] = [faixa_minuto(m, p) for m, p in zip(c["minuto"], c["periodo"])]
    for tipo, nome in (("amarelo", "Amarelos"), ("vermelho", "Vermelhos")):
        x = c[c["tipo"] == tipo].groupby("faixa").size()
        out[nome] = out["Faixa"].map(x).fillna(0).astype(int)
    return out


def equipes_de_arbitragem(base: pd.DataFrame) -> pd.DataFrame:
    """Contagem de jogos por pessoa em cada função (assistentes, quarto árbitro, VAR)."""
    linhas = []
    for campo, papel in (("assistente1", "Assistente"), ("assistente2", "Assistente"), ("quarto_arbitro", "Quarto árbitro"),
                         ("var", "VAR"), ("avar", "AVAR")):
        if campo in base:
            s = base[campo].dropna().value_counts()
            linhas += [{"Nome": n, "Função": papel, "Jogos": int(c)} for n, c in s.items()]
    if not linhas:
        return pd.DataFrame(columns=["Nome", "Função", "Jogos"])
    d = pd.DataFrame(linhas).groupby(["Nome", "Função"], as_index=False)["Jogos"].sum()
    return d.sort_values("Jogos", ascending=False).reset_index(drop=True)
