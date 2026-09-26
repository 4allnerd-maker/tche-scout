"""Estatisticas de scout: classificacao, perfil dos times, gols por minuto, atletas.
Nada de mercado/odds — so leitura estatistica do que aconteceu em campo."""

from __future__ import annotations

import pandas as pd

FAIXAS = ["0-15", "16-30", "31-45+", "46-60", "61-75", "76-90+"]


def faixa_minuto(m, periodo=None) -> str | None:
    """Faixa de 15 min. Acrescimos do 1o tempo ficam em '31-45+', do 2o em '76-90+'."""
    if m is None or pd.isna(m):
        return None
    if periodo == 1 and m > 30:
        return FAIXAS[2]
    if periodo == 2 and m > 75:
        return FAIXAS[5]
    for limite, faixa in ((15, FAIXAS[0]), (30, FAIXAS[1]), (45, FAIXAS[2]), (60, FAIXAS[3]), (75, FAIXAS[4])):
        if m <= limite:
            return faixa
    return FAIXAS[5]


def _linhas_por_time(jogos: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por time por jogo (com placar), com mando, gols pro/contra e resultado."""
    j = jogos.dropna(subset=["gols_mandante", "gols_visitante"])
    if j.empty:
        return pd.DataFrame()
    m = pd.DataFrame({"jogo_id": j["jogo_id"], "time": j["time_mandante"], "adversario": j["time_visitante"],
                      "mando": "Casa", "gp": j["gols_mandante"], "gc": j["gols_visitante"],
                      "situacao": j["situacao"], "data": j["data"]})
    v = pd.DataFrame({"jogo_id": j["jogo_id"], "time": j["time_visitante"], "adversario": j["time_mandante"],
                      "mando": "Fora", "gp": j["gols_visitante"], "gc": j["gols_mandante"],
                      "situacao": j["situacao"], "data": j["data"]})
    t = pd.concat([m, v], ignore_index=True)
    t["gp"], t["gc"] = t["gp"].astype(int), t["gc"].astype(int)
    t["V"] = (t["gp"] > t["gc"]).astype(int)
    t["E"] = (t["gp"] == t["gc"]).astype(int)
    t["D"] = (t["gp"] < t["gc"]).astype(int)
    t["pontos"] = t["V"] * 3 + t["E"]
    return t


def classificacao(jogos: pd.DataFrame) -> pd.DataFrame:
    t = _linhas_por_time(jogos)
    if t.empty:
        return pd.DataFrame(columns=["Pos", "Time", "P", "J", "V", "E", "D", "GP", "GC", "SG", "%"])
    a = t.groupby("time").agg(J=("jogo_id", "count"), V=("V", "sum"), E=("E", "sum"), D=("D", "sum"),
                              GP=("gp", "sum"), GC=("gc", "sum"), P=("pontos", "sum"),
                              WO=("situacao", lambda s: int((s == "W.O.").sum()))).reset_index()
    a["SG"] = a["GP"] - a["GC"]
    a["%"] = (a["P"] / (a["J"] * 3) * 100).round(1)
    a = a.sort_values(["P", "V", "SG", "GP"], ascending=False).reset_index(drop=True)
    a.insert(0, "Pos", range(1, len(a) + 1))
    a = a.rename(columns={"time": "Time"})
    return a[["Pos", "Time", "P", "J", "V", "E", "D", "GP", "GC", "SG", "%", "WO"]]


def perfil_times(jogos: pd.DataFrame, cartoes: pd.DataFrame, gols: pd.DataFrame) -> pd.DataFrame:
    """Scout geral por time: medias de gols feitos/sofridos, mando, jogos sem sofrer/sem marcar, disciplina."""
    t = _linhas_por_time(jogos[jogos["situacao"] != "W.O."])
    if t.empty:
        return pd.DataFrame()
    g = t.groupby("time")
    p = g.agg(J=("jogo_id", "count"), GP=("gp", "sum"), GC=("gc", "sum"), V=("V", "sum"), E=("E", "sum"), D=("D", "sum"),
              sem_sofrer=("gc", lambda s: int((s == 0).sum())), sem_marcar=("gp", lambda s: int((s == 0).sum()))).reset_index()
    p["Gols pró/jogo"] = (p["GP"] / p["J"]).round(2)
    p["Gols contra/jogo"] = (p["GC"] / p["J"]).round(2)
    for mando, sufixo in (("Casa", "casa"), ("Fora", "fora")):
        s = t[t["mando"] == mando].groupby("time").agg(**{f"J {sufixo}": ("jogo_id", "count"),
                                                          f"GP {sufixo}": ("gp", "sum"), f"GC {sufixo}": ("gc", "sum")})
        p = p.merge(s, left_on="time", right_index=True, how="left")
        p[f"Pró/jogo ({sufixo})"] = (p[f"GP {sufixo}"] / p[f"J {sufixo}"]).round(2)
        p[f"Contra/jogo ({sufixo})"] = (p[f"GC {sufixo}"] / p[f"J {sufixo}"]).round(2)
    p["Min/gol feito"] = (p["J"] * 90 / p["GP"].where(p["GP"] != 0)).round(0)
    p["Min/gol sofrido"] = (p["J"] * 90 / p["GC"].where(p["GC"] != 0)).round(0)
    p["Jogos s/ sofrer"] = p["sem_sofrer"]
    p["Jogos s/ marcar"] = p["sem_marcar"]

    if not cartoes.empty:
        ids = set(jogos.loc[jogos["situacao"] != "W.O.", "jogo_id"])
        c = cartoes[cartoes["jogo_id"].isin(ids)].groupby(["equipe", "tipo"]).size().unstack(fill_value=0)
        c = c.rename(columns={"amarelo": "Amarelos", "vermelho": "Vermelhos"})
        p = p.merge(c, left_on="time", right_index=True, how="left")
    for col in ("Amarelos", "Vermelhos"):
        if col not in p.columns:
            p[col] = 0
        p[col] = p[col].fillna(0).astype(int)
    p["Amarelos/jogo"] = (p["Amarelos"] / p["J"]).round(2)
    return p.rename(columns={"time": "Time"}).sort_values("Gols pró/jogo", ascending=False).reset_index(drop=True)


def gols_por_faixa(gols: pd.DataFrame, jogos: pd.DataFrame, time: str | None = None) -> pd.DataFrame:
    """Gols feitos e sofridos por faixa de 15 min. Sem 'time' = todos os gols da selecao de jogos (liga)."""
    ids = set(jogos.loc[jogos["situacao"] != "W.O.", "jogo_id"])
    g = gols[gols["jogo_id"].isin(ids)].copy()
    if time:
        do_time = jogos[(jogos["time_mandante"] == time) | (jogos["time_visitante"] == time)]
        g = g[g["jogo_id"].isin(set(do_time["jogo_id"]))]
    g["faixa"] = [faixa_minuto(m, p) for m, p in zip(g["minuto"], g["periodo"])]
    g = g.dropna(subset=["faixa"])
    if time:
        feitos = g[g["equipe_creditada"] == time].groupby("faixa").size()
        sofridos = g[g["equipe_creditada"] != time].groupby("faixa").size()
    else:
        feitos = g.groupby("faixa").size()
        sofridos = feitos * 0
    out = pd.DataFrame({"Faixa": FAIXAS})
    out["Feitos"] = out["Faixa"].map(feitos).fillna(0).astype(int)
    out["Sofridos"] = out["Faixa"].map(sofridos).fillna(0).astype(int)
    return out


def artilharia(partidas: pd.DataFrame, top: int = 30) -> pd.DataFrame:
    a = partidas.groupby(["atleta_id", "nome", "equipe"]).agg(Gols=("gols", "sum"), Jogos=("jogou", "sum")).reset_index()
    a = a[a["Gols"] > 0].sort_values(["Gols", "Jogos"], ascending=[False, True]).head(top)
    return a.rename(columns={"nome": "Atleta", "equipe": "Time"})[["Atleta", "Time", "Gols", "Jogos"]]


def painel_atletas(p: pd.DataFrame) -> pd.DataFrame:
    """Scout basico por atleta a partir das linhas jogador-partida ja filtradas."""
    if p.empty:
        return pd.DataFrame()
    p = p.copy()
    p["banco"] = (~p["titular"]) & (~p["entrou"])
    ag = p.groupby("atleta_id").agg(
        Atleta=("nome", "last"), Time=("equipe", "last"),  # "last": time mais recente (a base vem em ordem de data)
        Times=("equipe", "nunique"), _gk=("goleiro", "mean"),
        Relacionado=("jogo_id", "count"), Jogos=("jogou", "sum"), Titular=("titular", "sum"),
        Entrou=("entrou", "sum"), Banco=("banco", "sum"), Substituído=("saiu", "sum"),
        Minutos=("minutos", "sum"), Gols=("gols", "sum"), GolsContra=("gols_contra", "sum"),
        Amarelos=("amarelos", "sum"), Vermelhos=("vermelhos", "sum"),
    ).reset_index()
    ag["Posição"] = ag["_gk"].gt(0.5).map({True: "Goleiro", False: "Linha"})
    ag = ag.drop(columns="_gk")
    for c in ("Jogos", "Titular", "Entrou", "Banco", "Substituído", "Gols", "GolsContra", "Amarelos", "Vermelhos"):
        ag[c] = ag[c].astype(int)
    ag["Minutos"] = ag["Minutos"].round(0).astype(int)
    ag["Min/gol"] = (ag["Minutos"] / ag["Gols"].where(ag["Gols"] != 0)).round(0)
    ag["Gols/jogo"] = (ag["Gols"] / ag["Jogos"].where(ag["Jogos"] != 0)).round(2)
    return ag.rename(columns={"GolsContra": "G.C."}).sort_values(["Gols", "Minutos"], ascending=False).reset_index(drop=True)
