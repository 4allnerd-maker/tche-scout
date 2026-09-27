"""Motor da aba Análise: métricas de scout de um time + insights em texto para os relatórios.
Sem nada de apostas: só leitura estatística do que aconteceu em campo."""

from __future__ import annotations

import numpy as np
import pandas as pd

from stats import FAIXAS, faixa_minuto

TIPOS_GOL = {"NR": "Normal", "PN": "Pênalti", "FT": "Falta", "CT": "Contra (do adversário)"}


# ---------------------------------------------------------------- base do time
def jogos_do_time(jogos: pd.DataFrame, time: str, mando: str = "Todos", ultimos: int = 0) -> pd.DataFrame:
    """Uma linha por jogo do time (só jogos com súmula; W.O. não entra nas médias)."""
    j = jogos[(jogos["situacao"] != "W.O.") & ((jogos["time_mandante"] == time) | (jogos["time_visitante"] == time))]
    j = j.dropna(subset=["gols_mandante", "gols_visitante"])
    if j.empty:
        return pd.DataFrame()
    casa = j["time_mandante"] == time
    d = pd.DataFrame({
        "jogo_id": j["jogo_id"], "data": j["data"], "competicao": j["competicao_nome"], "fase": j["fase_nome"],
        "rodada": j["rodada"], "mando": np.where(casa, "Casa", "Fora"),
        "adversario": np.where(casa, j["time_visitante"], j["time_mandante"]),
        "gp": np.where(casa, j["gols_mandante"], j["gols_visitante"]).astype(int),
        "gc": np.where(casa, j["gols_visitante"], j["gols_mandante"]).astype(int),
        "gp1": np.where(casa, j["gols_1t_mandante"], j["gols_1t_visitante"]),
        "gc1": np.where(casa, j["gols_1t_visitante"], j["gols_1t_mandante"]),
    }).sort_values("data").reset_index(drop=True)
    d["gp1"], d["gc1"] = pd.to_numeric(d["gp1"]), pd.to_numeric(d["gc1"])
    d["gp2"], d["gc2"] = d["gp"] - d["gp1"], d["gc"] - d["gc1"]
    d["res"] = np.where(d["gp"] > d["gc"], "V", np.where(d["gp"] == d["gc"], "E", "D"))
    d["pontos"] = d["res"].map({"V": 3, "E": 1, "D": 0})
    if mando != "Todos":
        d = d[d["mando"] == mando]
    if ultimos:
        d = d.tail(ultimos)
    return d.reset_index(drop=True)


def resumo(d: pd.DataFrame) -> dict:
    j = len(d)
    if j == 0:
        return {}
    return {
        "J": j, "V": int((d.res == "V").sum()), "E": int((d.res == "E").sum()), "D": int((d.res == "D").sum()),
        "P": int(d.pontos.sum()), "aprov": round(d.pontos.sum() / (3 * j) * 100, 1),
        "GP": int(d.gp.sum()), "GC": int(d.gc.sum()), "SG": int(d.gp.sum() - d.gc.sum()),
        "gp_j": round(d.gp.mean(), 2), "gc_j": round(d.gc.mean(), 2),
        "sem_sofrer": int((d.gc == 0).sum()), "sem_marcar": int((d.gp == 0).sum()),
        "pct_sem_sofrer": round((d.gc == 0).mean() * 100, 1),
    }


def gols_do_time(gols: pd.DataFrame, ids: set, time: str) -> pd.DataFrame:
    g = gols[gols["jogo_id"].isin(ids)].copy()
    if g.empty:
        return g
    g["lado"] = np.where(g["equipe_creditada"] == time, "Pró", "Contra")
    g["faixa"] = [faixa_minuto(m, p) for m, p in zip(g["minuto"], g["periodo"])]
    return g


def por_faixa(g: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"Faixa": FAIXAS})
    for lado, nome in (("Pró", "Feitos"), ("Contra", "Sofridos")):
        c = g[g["lado"] == lado].groupby("faixa").size() if not g.empty else pd.Series(dtype=int)
        out[nome] = out["Faixa"].map(c).fillna(0).astype(int)
    return out


def por_tempo(g: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({"Tempo": ["1º tempo", "2º tempo"], "p": [1, 2]})
    for lado, nome in (("Pró", "Feitos"), ("Contra", "Sofridos")):
        c = g[g["lado"] == lado].groupby("periodo").size() if not g.empty else pd.Series(dtype=int)
        out[nome] = out["p"].map(c).fillna(0).astype(int)
    return out.drop(columns="p")


def primeiro_gol(d: pd.DataFrame, g: pd.DataFrame) -> pd.DataFrame:
    """Quem abriu o placar em cada jogo e como o jogo terminou."""
    linhas = []
    for _, r in d.iterrows():
        gj = g[(g["jogo_id"] == r["jogo_id"])].dropna(subset=["minuto"]).sort_values("minuto")
        if gj.empty:
            linhas.append({"jogo_id": r["jogo_id"], "primeiro": "Sem gols" if r.gp + r.gc == 0 else "?", "minuto": np.nan, "res": r["res"]})
        else:
            p = gj.iloc[0]
            linhas.append({"jogo_id": r["jogo_id"], "primeiro": p["lado"], "minuto": p["minuto"], "res": r["res"]})
    return pd.DataFrame(linhas)


def quadro_intervalo(d: pd.DataFrame) -> pd.DataFrame:
    """Situação ao intervalo × resultado final."""
    x = d.dropna(subset=["gp1", "gc1"]).copy()
    if x.empty:
        return pd.DataFrame()
    x["Ao intervalo"] = np.where(x.gp1 > x.gc1, "Vencendo", np.where(x.gp1 == x.gc1, "Empatando", "Perdendo"))
    t = x.groupby(["Ao intervalo", "res"]).size().unstack(fill_value=0).reindex(columns=["V", "E", "D"], fill_value=0)
    t = t.reindex(["Vencendo", "Empatando", "Perdendo"]).fillna(0).astype(int)
    t["Jogos"] = t.sum(axis=1)
    t.columns = ["Vitórias", "Empates", "Derrotas", "Jogos"]
    return t.reset_index()


def dist_gols_por_jogo(d: pd.DataFrame) -> pd.DataFrame:
    def cat(s):
        return s.clip(upper=3).map({0: "0", 1: "1", 2: "2", 3: "3+"})
    a = cat(d.gp).value_counts().reindex(["0", "1", "2", "3+"], fill_value=0)
    b = cat(d.gc).value_counts().reindex(["0", "1", "2", "3+"], fill_value=0)
    return pd.DataFrame({"Gols no jogo": ["0", "1", "2", "3+"], "Feitos": a.values, "Sofridos": b.values})


def tipos_de_gol(g: pd.DataFrame) -> pd.DataFrame:
    pro = g[g["lado"] == "Pró"]
    if pro.empty:
        return pd.DataFrame(columns=["Tipo", "Gols"])
    t = pro["tipo"].map(TIPOS_GOL).fillna(pro["tipo"]).value_counts().reset_index()
    t.columns = ["Tipo", "Gols"]
    return t


# ---------------------------------------------------------------- disciplina / elenco
def cartoes_do_time(cartoes: pd.DataFrame, ids: set, time: str) -> pd.DataFrame:
    c = cartoes[cartoes["jogo_id"].isin(ids) & (cartoes["equipe"] == time)].copy()
    if not c.empty:
        c["faixa"] = [faixa_minuto(m, p) for m, p in zip(c["minuto"], c["periodo"])]
    return c


def elenco(partidas: pd.DataFrame, ids: set, time: str) -> pd.DataFrame:
    p = partidas[partidas["jogo_id"].isin(ids) & (partidas["equipe"] == time)]
    if p.empty:
        return pd.DataFrame()
    a = p.groupby("atleta_id").agg(
        Atleta=("nome", "last"), Jogos=("jogou", "sum"), Titular=("titular", "sum"), Entrou=("entrou", "sum"),
        Minutos=("minutos", "sum"), Gols=("gols", "sum"), Amarelos=("amarelos", "sum"), Vermelhos=("vermelhos", "sum"),
        Goleiro=("goleiro", "mean")).reset_index()
    a["Posição"] = np.where(a["Goleiro"] > 0.5, "Goleiro", "Linha")
    for c in ("Jogos", "Titular", "Entrou", "Minutos", "Gols", "Amarelos", "Vermelhos"):
        a[c] = a[c].round(0).astype(int)
    return a.drop(columns=["Goleiro"]).sort_values("Minutos", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- comparação com o campeonato
def metricas_liga(jogos: pd.DataFrame, cartoes: pd.DataFrame, mando: str = "Todos") -> pd.DataFrame:
    """Métricas-chave de todos os times da seleção (para ranking, médias e radar)."""
    ids_cartao = cartoes.groupby(["jogo_id", "equipe"]).size() if not cartoes.empty else pd.Series(dtype=int)
    times = sorted(set(jogos["time_mandante"]) | set(jogos["time_visitante"]))
    linhas = []
    for t in times:
        d = jogos_do_time(jogos, t, mando)
        if d.empty:
            continue
        r = resumo(d)
        amar = cartoes[(cartoes["equipe"] == t) & (cartoes["jogo_id"].isin(set(d["jogo_id"]))) & (cartoes["tipo"] == "amarelo")] \
            if not cartoes.empty else pd.DataFrame()
        linhas.append({"Time": t, "J": r["J"], "Aproveitamento": r["aprov"], "Gols pró/jogo": r["gp_j"],
                       "Gols contra/jogo": r["gc_j"], "Jogos sem sofrer (%)": r["pct_sem_sofrer"],
                       "Amarelos/jogo": round(len(amar) / r["J"], 2)})
    return pd.DataFrame(linhas)


def radar_valores(liga: pd.DataFrame, time: str) -> dict[str, float]:
    """Perfil 0-100 do time frente ao campeonato (100 = melhor da seleção em cada eixo)."""
    def norm(col, inverso=False):
        s = liga.set_index("Time")[col]
        lo, hi = s.min(), s.max()
        if hi == lo:
            return s * 0 + 50
        n = (s - lo) / (hi - lo) * 100
        return 100 - n if inverso else n
    df = pd.DataFrame({
        "Ataque": norm("Gols pró/jogo"), "Defesa": norm("Gols contra/jogo", True),
        "Aproveitamento": norm("Aproveitamento"), "Solidez": norm("Jogos sem sofrer (%)"),
        "Disciplina": norm("Amarelos/jogo", True)})
    return {"time": df.loc[time].round(0).to_dict() if time in df.index else {}, "media": df.mean().round(0).to_dict()}


# ---------------------------------------------------------------- insights em texto
def _pct(a, b):
    return round(a / b * 100) if b else 0


def insights(time: str, d: pd.DataFrame, g: pd.DataFrame, cartoes_t: pd.DataFrame, elenco_t: pd.DataFrame,
             liga: pd.DataFrame, primeiro: pd.DataFrame, quadro: pd.DataFrame, subs: pd.DataFrame,
             cont: dict | None = None) -> list[str]:
    r = resumo(d)
    if not r:
        return []
    out = []
    out.append(f"**Campanha:** {r['V']}V {r['E']}E {r['D']}D em {r['J']} jogos — {r['P']} pontos "
               f"({r['aprov']}% de aproveitamento), saldo {r['SG']:+d}.")
    if not liga.empty and time in set(liga["Time"]):
        L = liga.set_index("Time")
        n = len(L)
        pos_atk = int(L["Gols pró/jogo"].rank(ascending=False, method="min")[time])
        pos_def = int(L["Gols contra/jogo"].rank(ascending=True, method="min")[time])
        out.append(f"**Ataque:** {r['gp_j']} gols por jogo — {pos_atk}º de {n} times "
                   f"(média da seleção: {L['Gols pró/jogo'].mean():.2f}).")
        out.append(f"**Defesa:** {r['gc_j']} gols sofridos por jogo — {pos_def}º melhor de {n} "
                   f"(média da seleção: {L['Gols contra/jogo'].mean():.2f}); não sofreu gols em {r['sem_sofrer']} jogos "
                   f"({r['pct_sem_sofrer']}%).")
    else:
        out.append(f"**Ataque/defesa:** {r['gp_j']} gols feitos e {r['gc_j']} sofridos por jogo; "
                   f"sem sofrer gols em {r['sem_sofrer']} de {r['J']} jogos.")

    casa, fora = d[d.mando == "Casa"], d[d.mando == "Fora"]
    if len(casa) >= 2 and len(fora) >= 2:
        ac, af = casa.pontos.sum() / (3 * len(casa)) * 100, fora.pontos.sum() / (3 * len(fora)) * 100
        out.append(f"**Mando:** em casa marca {casa.gp.mean():.2f} e sofre {casa.gc.mean():.2f} por jogo "
                   f"({ac:.0f}% de aproveitamento); fora marca {fora.gp.mean():.2f} e sofre {fora.gc.mean():.2f} "
                   f"({af:.0f}%).")

    pro, contra = g[g["lado"] == "Pró"] if not g.empty else g, g[g["lado"] == "Contra"] if not g.empty else g
    if len(pro) >= 4:
        p2 = _pct((pro["periodo"] == 2).sum(), len(pro))
        f = pro["faixa"].value_counts()
        out.append(f"**Quando marca:** {100 - p2}% dos gols saem no 1º tempo e {p2}% no 2º; faixa mais produtiva: "
                   f"**{f.index[0]} min** ({f.iloc[0]} de {len(pro)} gols).")
        ult = _pct(pro["faixa"].isin(["61-75", "76-90+"]).sum(), len(pro))
        out.append(f"Marca {ult}% dos gols na meia hora final (a partir dos 61 min).")
    elif len(pro):
        out.append("**Quando marca:** amostra pequena (menos de 4 gols) — evite conclusões sobre minutagem.")
    if len(contra) >= 4:
        c2 = _pct((contra["periodo"] == 2).sum(), len(contra))
        f = contra["faixa"].value_counts()
        out.append(f"**Quando sofre:** {100 - c2}% dos gols sofridos no 1º tempo e {c2}% no 2º; faixa mais vulnerável: "
                   f"**{f.index[0]} min** ({f.iloc[0]} de {len(contra)}).")
        ini = _pct((contra["minuto"] <= 15).sum(), len(contra))
        if ini >= 25:
            out.append(f"Atenção: {ini}% dos gols sofridos acontecem nos primeiros 15 minutos.")

    if not primeiro.empty:
        marc = primeiro[primeiro["primeiro"] == "Pró"]
        sof = primeiro[primeiro["primeiro"] == "Contra"]
        if len(marc):
            out.append(f"**Abre o placar** em {len(marc)} de {r['J']} jogos ({_pct(len(marc), r['J'])}%) e vence "
                       f"{_pct((marc.res == 'V').sum(), len(marc))}% deles.")
        if len(sof):
            out.append(f"Quando **sofre primeiro** ({len(sof)} jogos), pontua em {_pct((sof.res != 'D').sum(), len(sof))}% "
                       f"e vence {_pct((sof.res == 'V').sum(), len(sof))}%.")
        m = primeiro["minuto"].dropna()
        if len(m) >= 4:
            out.append(f"Minuto médio do 1º gol do jogo: {m.mean():.0f}'.")

    if not quadro.empty:
        q = quadro.set_index("Ao intervalo")
        if q.loc["Perdendo", "Jogos"] >= 2:
            pe = q.loc["Perdendo"]
            out.append(f"**Reação:** perdendo no intervalo ({pe['Jogos']} jogos), empatou/venceu em "
                       f"{pe['Vitórias'] + pe['Empates']}.")
        if q.loc["Vencendo", "Jogos"] >= 2:
            ve = q.loc["Vencendo"]
            out.append(f"**Controle:** vencendo no intervalo ({ve['Jogos']} jogos), manteve a vitória em {ve['Vitórias']}.")

    if not cartoes_t.empty:
        am = int((cartoes_t["tipo"] == "amarelo").sum())
        vm = int((cartoes_t["tipo"] == "vermelho").sum())
        out.append(f"**Disciplina:** {am} amarelos ({am / r['J']:.2f}/jogo) e {vm} vermelhos.")
    if not elenco_t.empty and r["GP"]:
        top = elenco_t.sort_values("Gols", ascending=False).iloc[0]
        if top["Gols"] > 0:
            out.append(f"**Referência ofensiva:** {top['Atleta']} marcou {top['Gols']} dos {r['GP']} gols do time "
                       f"({_pct(top['Gols'], r['GP'])}%).")
        de_banco = int(elenco_t[elenco_t["Titular"] == 0]["Gols"].sum())
        if de_banco:
            out.append(f"Gols de atletas que começaram no banco: {de_banco} ({_pct(de_banco, r['GP'])}%).")
    if not subs.empty:
        out.append(f"**Substituições:** média de {len(subs) / r['J']:.1f} por jogo; a 1ª troca costuma acontecer aos "
                   f"{subs.groupby('jogo_id')['minuto'].min().mean():.0f}'.")
    if cont:
        out.append(f"**Continuidade do onze:** mantém em média {cont['media_mantidos']} dos 11 titulares de um jogo para o outro "
                   f"(em {cont['pct_ate_2']}% dos jogos muda no máximo 2 atletas; onze idêntico em {cont['pct_igual']}%).")
    ult5 = d.tail(5)
    out.append("**Últimos 5 jogos:** " + " ".join(ult5["res"]) + f" — {ult5.gp.sum()} gols feitos e {ult5.gc.sum()} sofridos.")
    return out


# ---------------------------------------------------------------- continuidade do onze (dado real, sem convenção)
def continuidade_onze(partidas: pd.DataFrame, d: pd.DataFrame, time: str) -> pd.DataFrame:
    """Titulares mantidos e novos em relação ao jogo anterior do time (d em ordem cronológica)."""
    tit = partidas[(partidas["equipe"] == time) & (partidas["titular"]) & (partidas["jogo_id"].isin(set(d["jogo_id"])))]
    sets = {jid: set(g["atleta_id"]) for jid, g in tit.groupby("jogo_id")}
    linhas, prev = [], None
    for r in d.itertuples():
        s = sets.get(r.jogo_id)
        if not s:
            continue
        if prev is not None:
            linhas.append({"jogo_id": r.jogo_id, "Data": r.data, "Adversário": r.adversario,
                           "Titulares mantidos": len(s & prev), "Titulares novos": len(s - prev)})
        prev = s
    return pd.DataFrame(linhas)


def resumo_continuidade(c: pd.DataFrame) -> dict:
    if c.empty:
        return {}
    return {"media_mantidos": round(c["Titulares mantidos"].mean(), 1), "media_novos": round(c["Titulares novos"].mean(), 1),
            "jogos": len(c), "pct_ate_2": round((c["Titulares novos"] <= 2).mean() * 100),
            "pct_igual": round((c["Titulares novos"] == 0).mean() * 100)}
