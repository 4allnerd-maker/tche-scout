"""Motor de notas dos jogadores (estilo "menu de videogame").

Cada atributo é uma métrica por 90 minutos (ou uma porcentagem). A nota 30-99 de cada atributo é a posição
percentual do jogador entre os da MESMA função (Goleiro, Defensor, Meia, Atacante) em todas as ligas juntas,
considerando só quem tem MIN_MINUTOS ou mais. As categorias são a média dos atributos; o OVR é a média ponderada
das categorias (pesos por função). Tudo é relativo ao conjunto de dados carregado: não é uma nota absoluta.
"""

from __future__ import annotations

import pandas as pd

MIN_MINUTOS = 450
PESO_CARTAO_VERMELHO = 3  # cartão amarelo vale 1; vermelho vale 3 (amarelo + vermelho de segundo amarelo contam pelo CSV como 1 + 3)

# (código, rótulo, coluna do CSV, tipo, invertida)  tipo: "t90" = total/min*90 | "pct" = valor direto | "p90" = já por 90
ATRIBUTOS = {
    "gols_90": ("Gols/90", "goals_overall", "t90", False),
    "xg_90": ("xG/90", "xg_total_overall", "t90", False),
    "chutes_90": ("Chutes/90", "shots_total_overall", "t90", False),
    "chutes_alvo_pct": ("Chutes no alvo %", "_chutes_alvo_pct", "pct", False),
    "assist_90": ("Assistências/90", "assists_overall", "t90", False),
    "xa_90": ("xA/90", "xa_total_overall", "t90", False),
    "passes_chave_90": ("Passes-chave/90", "key_passes_total_overall", "t90", False),
    "chances_criadas_90": ("Chances criadas/90", "chances_created_total_overall", "t90", False),
    "passes_90": ("Passes/90", "passes_total_overall", "t90", False),
    "passes_pct": ("Passes certos %", "pass_completion_rate_overall", "pct", False),
    "passes_prog_90": ("Passes progressivos/90", "progressive_passes_total_overall", "t90", False),
    "passes_longos_90": ("Passes longos/90", "long_passes_total_overall", "t90", False),
    "dribles_90": ("Dribles certos/90", "dribbles_successful_total_overall", "t90", False),
    "dribles_pct": ("Dribles certos %", "dribbles_successful_percentage_overall", "pct", False),
    "faltas_sofridas_90": ("Faltas sofridas/90", "fouls_drawn_total_overall", "t90", False),
    "perdas_90": ("Perdas de bola/90", "dispossesed_total_overall", "t90", True),
    "desarmes_90": ("Desarmes/90", "tackles_total_overall", "t90", False),
    "interceptacoes_90": ("Interceptações/90", "interceptions_total_overall", "t90", False),
    "cortes_90": ("Cortes/90", "clearances_total_overall", "t90", False),
    "bloqueios_90": ("Bloqueios/90", "blocks_total_overall", "t90", False),
    "recuperacoes_90": ("Recuperações de bola/90", "possession_regained_total_overall", "t90", False),
    "duelos_pct": ("Duelos ganhos %", "duels_won_percentage_overall", "pct", False),
    "duelos_90": ("Duelos ganhos/90", "duels_won_total_overall", "t90", False),
    "aereos_90": ("Bolas aéreas ganhas/90", "aerial_duels_won_total_overall", "t90", False),
    "distancia_90": ("Distância percorrida/90 (km)", "distance_travelled_per_90_overall", "p90", False),
    "pressoes_90": ("Pressões/90", "pressures_total_overall", "t90", False),
    "defesas_90": ("Defesas/90", "saves_total_overall", "t90", False),
    "defesas_pct": ("Defesas %", "save_percentage_overall", "pct", False),
    "sem_sofrer_pct": ("Jogos sem sofrer gol %", "_sem_sofrer_pct", "pct", False),
    "sofridos_90": ("Gols sofridos/90", "conceded_overall", "t90", True),
    "participacao_gols_90": ("Gols + assistências/90", "_participacao", "t90", False),
    "cartoes_90": ("Cartões ponderados/90", "_cartoes", "t90", False),
    "faltas_90": ("Faltas cometidas/90", "fouls_committed_total_overall", "t90", False),
}

CATEGORIAS = {  # código: (rótulo, [atributos])
    "finalizacao": ("Finalização", ["gols_90", "xg_90", "chutes_90", "chutes_alvo_pct"]),
    "criacao": ("Criação", ["assist_90", "xa_90", "passes_chave_90", "chances_criadas_90"]),
    "passe": ("Passe", ["passes_90", "passes_pct", "passes_prog_90", "passes_longos_90"]),
    "drible": ("Drible e posse", ["dribles_90", "dribles_pct", "faltas_sofridas_90", "perdas_90"]),
    "defesa": ("Defesa", ["desarmes_90", "interceptacoes_90", "cortes_90", "bloqueios_90", "recuperacoes_90"]),
    "duelos": ("Duelos e físico", ["duelos_pct", "duelos_90", "aereos_90", "distancia_90", "pressoes_90"]),
    "goleiro": ("Goleiro", ["defesas_pct", "sem_sofrer_pct", "sofridos_90"]),
    "agressividade": ("Agressividade", ["faltas_90", "cartoes_90"]),
}
CAT_POR_FUNCAO = {
    "Goleiro": ["goleiro", "passe"],
    "Defensor": ["finalizacao", "criacao", "passe", "drible", "defesa", "duelos"],
    "Meia": ["finalizacao", "criacao", "passe", "drible", "defesa", "duelos"],
    "Atacante": ["finalizacao", "criacao", "passe", "drible", "defesa", "duelos"],
}
PESOS = {  # pesos do OVR por função (somam 1)
    "Goleiro": {"goleiro": .75, "passe": .25},
    "Defensor": {"finalizacao": .02, "criacao": .08, "passe": .20, "drible": .08, "defesa": .34, "duelos": .28},
    "Meia": {"finalizacao": .12, "criacao": .26, "passe": .22, "drible": .18, "defesa": .10, "duelos": .12},
    "Atacante": {"finalizacao": .34, "criacao": .16, "passe": .06, "drible": .20, "defesa": .04, "duelos": .20},
}
ATRIBUTOS_COLETA_VARIAVEL = ["passes_prog_90", "passes_longos_90", "distancia_90", "pressoes_90", "recuperacoes_90", "chances_criadas_90",
                             "bloqueios_90", "cortes_90", "interceptacoes_90", "desarmes_90", "duelos_90", "aereos_90", "dribles_90",
                             "passes_chave_90"]
INDICES = {  # índices combinados, calculados direto dos atributos (valem para qualquer função): código: (rótulo, [atributos])
    "ofensividade": ("Ofensividade", ["gols_90", "xg_90", "chutes_90", "participacao_gols_90", "assist_90", "xa_90",
                                      "chances_criadas_90", "passes_chave_90", "passes_pct", "passes_prog_90"]),
    "defensividade": ("Defensividade", ["desarmes_90", "interceptacoes_90", "cortes_90", "bloqueios_90", "recuperacoes_90",
                                        "duelos_pct", "duelos_90", "aereos_90", "pressoes_90"]),
    "construcao": ("Construção", ["passes_90", "passes_pct", "passes_prog_90", "passes_longos_90", "dribles_90", "dribles_pct", "perdas_90"]),
    "agressividade": ("Agressividade", ["faltas_90", "cartoes_90"]),  # alto = mais faltas e cartões (não é "melhor")
}
INDICES_GOLEIRO = ["construcao", "agressividade"]


def classe(liga_id: str) -> str:
    """Classe da competição: A = Série A, Copa do Brasil e Supercopa; B/C = Séries B/C; D = Série D, estaduais e demais."""
    return {"serie-a": "A", "copa-do-brasil": "A", "supercopa-do-brasil": "A", "serie-b": "B", "serie-c": "C"}.get(liga_id, "D")


def metricas(r: pd.Series, minutos: float) -> dict[str, float | None]:
    """Valores brutos (por 90 ou %) de cada atributo, a partir de uma linha do CSV de jogadores."""
    def g(col):
        v = r.get(col)
        return None if v is None or pd.isna(v) else float(v)

    jogos = g("appearances_overall") or 0
    chutes, alvo = g("shots_total_overall"), g("shots_on_target_total_overall")
    derivadas = {
        "_chutes_alvo_pct": (100 * alvo / chutes) if chutes and alvo is not None and chutes >= 5 else None,
        "_sem_sofrer_pct": (100 * (g("clean_sheets_overall") or 0) / jogos) if jogos else None,
        "_cartoes": (g("yellow_cards_overall") or 0) + PESO_CARTAO_VERMELHO * (g("red_cards_overall") or 0),
        "_participacao": (g("goals_overall") or 0) + (g("assists_overall") or 0),
    }
    saida = {}
    for cod, (_, col, tipo, _inv) in ATRIBUTOS.items():
        v = derivadas[col] if col in derivadas else g(col)
        if v is None:
            saida[cod] = None
        elif tipo == "t90":
            saida[cod] = round(v * 90 / minutos, 3) if minutos >= 90 else None
        else:
            saida[cod] = round(v, 2)
    return saida


def avalia(linhas: list[dict]) -> None:
    """Calcula notas, OVR, índices e rankings; escreve em cada linha: classe, notas, ovr, indices, ranks, valores."""
    df = pd.DataFrame([{**l["_m"], "pos": l["posicao"], "liga": l["liga_id"], "min": l["min"] or 0} for l in linhas])
    elegivel = df["min"] >= MIN_MINUTOS
    # A fonte preenche com ZERO o que não coleta numa liga: atributo com quase só zeros na liga vira "sem dado".
    zerados = set()
    for liga, g in df[elegivel].groupby("liga"):
        for cod in ATRIBUTOS_COLETA_VARIAVEL:
            s = g[cod].dropna()
            if len(s) >= 20 and (s != 0).mean() < 0.25:
                zerados.add((liga, cod))
    for liga, cod in zerados:
        mask = df["liga"] == liga
        df.loc[mask, cod] = float("nan")
        for i in df.index[mask]:
            linhas[i]["_m"][cod] = None
    notas = pd.DataFrame(index=df.index, columns=list(ATRIBUTOS), dtype=float)
    for pos, grupo in df[elegivel].groupby("pos"):
        for cod, (_, _, _, inv) in ATRIBUTOS.items():
            s = grupo[cod]
            if s.notna().sum() < 20:
                continue
            pct = s.rank(pct=True, ascending=not inv)
            notas.loc[grupo.index, cod] = 30 + 69 * pct.where(s.notna())
    for i, l in enumerate(linhas):
        l["classe"] = classe(l["liga_id"])
        l["valores"] = {k: v for k, v in l.pop("_m").items() if v is not None}
        if not elegivel.iloc[i]:
            l.update(ovr=None, notas=None, indices=None, ranks=None)
            continue
        n_attr = {k: round(v) for k, v in notas.iloc[i].items() if pd.notna(v)}
        cats = {}
        for c in CAT_POR_FUNCAO[l["posicao"]] + ["agressividade"]:
            vals = [n_attr[a] for a in CATEGORIAS[c][1] if a in n_attr]
            if len(vals) * 2 >= len(CATEGORIAS[c][1]):
                cats[c] = round(sum(vals) / len(vals))
        pesos = {c: w for c, w in PESOS[l["posicao"]].items() if c in cats}
        l["ovr"] = round(sum(cats[c] * w for c, w in pesos.items()) / sum(pesos.values())) if pesos else None
        ind = {}
        for cod, (_, attrs) in INDICES.items():
            if l["posicao"] == "Goleiro" and cod not in INDICES_GOLEIRO:
                continue
            vs = [n_attr[a] for a in attrs if a in n_attr]
            if len(vs) * 2 >= len(attrs):
                ind[cod] = round(sum(vs) / len(vs))
        l["notas"] = {"atributos": n_attr, "categorias": cats}
        l["indices"] = ind
    ovr = pd.Series([l["ovr"] for l in linhas], dtype=float)
    meta = pd.DataFrame({"ovr": ovr, "pos": df["pos"], "liga": df["liga"], "classe": [l["classe"] for l in linhas]})
    ok = meta["ovr"].notna()
    r_geral = meta[ok]["ovr"].rank(ascending=False, method="min")
    r_pos = meta[ok].groupby("pos")["ovr"].rank(ascending=False, method="min")
    r_liga = meta[ok].groupby("liga")["ovr"].rank(ascending=False, method="min")
    n_pos = meta[ok].groupby("pos")["ovr"].transform("size")
    n_liga = meta[ok].groupby("liga")["ovr"].transform("size")
    r_classe = meta[ok].groupby("classe")["ovr"].rank(ascending=False, method="min")
    n_classe = meta[ok].groupby("classe")["ovr"].transform("size")
    for i in meta[ok].index:
        linhas[i]["ranks"] = {"geral": int(r_geral[i]), "n_geral": int(ok.sum()), "posicao": int(r_pos[i]), "n_posicao": int(n_pos[i]),
                              "liga": int(r_liga[i]), "n_liga": int(n_liga[i]),
                              "classe": int(r_classe[i]), "n_classe": int(n_classe[i])}
