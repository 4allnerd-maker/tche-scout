"""Colunas das duas visões de dados do jogador.

VCA (Valor Coletivo Agregado, visão "dados brutos"): totais e porcentagens da temporada.
ETA (Eficiência Tática Adaptativa, visão "por 90 minutos"): taxas por 90 minutos, com a posição do atleta entre os da mesma função.
AIE (Análise de Impacto Estratégico) é o ranking e a ficha estilo videogame (geral/skills.py).

Cada item: (grupo, rótulo, coluna do CSV, tipo, raro)
  tipo: "int" | "dec" | "pct" (valor já em %)    raro: True = zero é normal (cartão vermelho, hat-trick...); não vira "sem dado".
"""

from __future__ import annotations

import pandas as pd

PESO_VERMELHO = 3

VCA = [
    ("Geral", "Jogos", "appearances_overall", "int", False),
    ("Geral", "Jogos como titular", "games_started", "int", False),
    ("Geral", "Entrou no decorrer", "games_subbed_in", "int", False),
    ("Geral", "Substituído", "games_subbed_out", "int", False),
    ("Geral", "Minutos jogados", "minutes_played_overall", "int", False),
    ("Geral", "Nota média (fonte)", "average_rating_overall", "dec", False),
    ("Geral", "Jogador do jogo", "man_of_the_match_total_overall", "int", True),
    ("Ataque", "Gols", "goals_overall", "int", True),
    ("Ataque", "Gols de pênalti", "penalty_goals", "int", True),
    ("Ataque", "Pênaltis cobrados", "pens_taken_total_overall", "int", True),
    ("Ataque", "Pênaltis perdidos", "penalty_misses", "int", True),
    ("Ataque", "xG (gols esperados)", "xg_total_overall", "dec", False),
    ("Ataque", "xG sem pênaltis", "npxg_total_overall", "dec", False),
    ("Ataque", "Chutes", "shots_total_overall", "int", False),
    ("Ataque", "Chutes no alvo", "shots_on_target_total_overall", "int", False),
    ("Ataque", "Chutes para fora", "shots_off_target_total_overall", "int", False),
    ("Ataque", "Precisão dos chutes %", "shot_accuraccy_percentage_overall", "pct", False),
    ("Ataque", "Conversão dos chutes %", "shot_conversion_rate_overall", "pct", True),
    ("Ataque", "Bolas na trave", "hit_woodwork_total_overall", "int", True),
    ("Ataque", "Hat-tricks", "hattricks_total_overall", "int", True),
    ("Ataque", "Impedimentos", "offsides_total_overall", "int", True),
    ("Criação", "Assistências", "assists_overall", "int", True),
    ("Criação", "xA (assistências esperadas)", "xa_total_overall", "dec", False),
    ("Criação", "Passes-chave", "key_passes_total_overall", "int", False),
    ("Criação", "Chances criadas", "chances_created_total_overall", "int", False),
    ("Criação", "Cruzamentos", "crosses_total_overall", "int", False),
    ("Criação", "Cruzamentos certos", "accurate_crosses_total_overall", "int", False),
    ("Criação", "Cruzamentos certos %", "cross_completion_rate_overall", "pct", False),
    ("Criação", "Passes em profundidade", "through_passes_total_overall", "int", False),
    ("Passe", "Passes", "passes_total_overall", "int", False),
    ("Passe", "Passes certos", "passes_completed_total_overall", "int", False),
    ("Passe", "Passes certos %", "pass_completion_rate_overall", "pct", False),
    ("Passe", "Passes progressivos", "progressive_passes_total_overall", "int", False),
    ("Passe", "Passes longos", "long_passes_total_overall", "int", False),
    ("Passe", "Passes curtos", "short_passes_total_overall", "int", False),
    ("Drible e posse", "Dribles", "dribbles_total_overall", "int", False),
    ("Drible e posse", "Dribles certos", "dribbles_successful_total_overall", "int", False),
    ("Drible e posse", "Dribles certos %", "dribbles_successful_percentage_overall", "pct", False),
    ("Drible e posse", "Perdas de bola", "dispossesed_total_overall", "int", False),
    ("Drible e posse", "Faltas sofridas", "fouls_drawn_total_overall", "int", False),
    ("Drible e posse", "Pênaltis sofridos (a favor)", "penalties_won_total_overall", "int", True),
    ("Drible e posse", "Distância percorrida (km)", "distance_travelled_total_overall", "dec", False),
    ("Defesa", "Desarmes", "tackles_total_overall", "int", False),
    ("Defesa", "Desarmes certos", "tackles_successful_total_overall", "int", False),
    ("Defesa", "Interceptações", "interceptions_total_overall", "int", False),
    ("Defesa", "Cortes", "clearances_total_overall", "int", False),
    ("Defesa", "Bloqueios", "blocks_total_overall", "int", False),
    ("Defesa", "Recuperações de bola", "possession_regained_total_overall", "int", False),
    ("Defesa", "Pressões", "pressures_total_overall", "int", False),
    ("Defesa", "Dribles sofridos", "dribbled_past_total_overall", "int", False),
    ("Duelos", "Duelos", "duels_total_overall", "int", False),
    ("Duelos", "Duelos ganhos", "duels_won_total_overall", "int", False),
    ("Duelos", "Duelos ganhos %", "duels_won_percentage_overall", "pct", False),
    ("Duelos", "Bolas aéreas disputadas", "aerial_duels_total_overall", "int", False),
    ("Duelos", "Bolas aéreas ganhas", "aerial_duels_won_total_overall", "int", False),
    ("Duelos", "Bolas aéreas ganhas %", "aerial_duels_won_percentage_overall", "pct", False),
    ("Disciplina", "Faltas cometidas", "fouls_committed_total_overall", "int", False),
    ("Disciplina", "Cartões amarelos", "yellow_cards_overall", "int", True),
    ("Disciplina", "Cartões vermelhos", "red_cards_overall", "int", True),
    ("Disciplina", "Pênaltis cometidos", "pen_committed_total_overall", "int", True),
    ("Goleiro", "Defesas", "saves_total_overall", "int", False),
    ("Goleiro", "Defesas %", "save_percentage_overall", "pct", False),
    ("Goleiro", "Chutes enfrentados", "shots_faced_total_overall", "int", False),
    ("Goleiro", "Gols sofridos", "conceded_overall", "int", True),
    ("Goleiro", "Jogos sem sofrer gol", "clean_sheets_overall", "int", True),
    ("Goleiro", "Defesas dentro da área", "inside_box_saves_total_overall", "int", False),
    ("Goleiro", "Pênaltis defendidos", "pens_saved_total_overall", "int", True),
    ("Goleiro", "Socos", "punches_total_overall", "int", True),
]

# ETA: (grupo, rótulo, coluna-TOTAL do CSV (vira "por 90"), tipo, raro, neg)   neg=True: quanto menor, melhor
# Colunas especiais: "_part" = gols + assistências; "_cart" = cartões ponderados; "min_*" = minutos por evento (não é por 90)
ETA = [
    ("Ataque", "Gols/90", "goals_overall", "dec", True, False),
    ("Ataque", "xG/90", "xg_total_overall", "dec", False, False),
    ("Ataque", "xG sem pênaltis/90", "npxg_total_overall", "dec", False, False),
    ("Ataque", "Gols + assistências/90", "_part", "dec", True, False),
    ("Ataque", "Chutes/90", "shots_total_overall", "dec", False, False),
    ("Ataque", "Chutes no alvo/90", "shots_on_target_total_overall", "dec", False, False),
    ("Criação", "Assistências/90", "assists_overall", "dec", True, False),
    ("Criação", "xA/90", "xa_total_overall", "dec", False, False),
    ("Criação", "Passes-chave/90", "key_passes_total_overall", "dec", False, False),
    ("Criação", "Chances criadas/90", "chances_created_total_overall", "dec", False, False),
    ("Criação", "Cruzamentos/90", "crosses_total_overall", "dec", False, False),
    ("Criação", "Passes em profundidade/90", "through_passes_total_overall", "dec", False, False),
    ("Passe", "Passes/90", "passes_total_overall", "dec", False, False),
    ("Passe", "Passes certos/90", "passes_completed_total_overall", "dec", False, False),
    ("Passe", "Passes progressivos/90", "progressive_passes_total_overall", "dec", False, False),
    ("Passe", "Passes longos/90", "long_passes_total_overall", "dec", False, False),
    ("Passe", "Passes curtos/90", "short_passes_total_overall", "dec", False, False),
    ("Drible e posse", "Dribles/90", "dribbles_total_overall", "dec", False, False),
    ("Drible e posse", "Dribles certos/90", "dribbles_successful_total_overall", "dec", False, False),
    ("Drible e posse", "Faltas sofridas/90", "fouls_drawn_total_overall", "dec", False, False),
    ("Drible e posse", "Perdas de bola/90", "dispossesed_total_overall", "dec", False, True),
    ("Drible e posse", "Distância percorrida/90 (km)", "distance_travelled_total_overall", "dec", False, False),
    ("Defesa", "Desarmes/90", "tackles_total_overall", "dec", False, False),
    ("Defesa", "Desarmes certos/90", "tackles_successful_total_overall", "dec", False, False),
    ("Defesa", "Interceptações/90", "interceptions_total_overall", "dec", False, False),
    ("Defesa", "Cortes/90", "clearances_total_overall", "dec", False, False),
    ("Defesa", "Bloqueios/90", "blocks_total_overall", "dec", False, False),
    ("Defesa", "Recuperações de bola/90", "possession_regained_total_overall", "dec", False, False),
    ("Defesa", "Pressões/90", "pressures_total_overall", "dec", False, False),
    ("Defesa", "Dribles sofridos/90", "dribbled_past_total_overall", "dec", False, True),
    ("Duelos", "Duelos/90", "duels_total_overall", "dec", False, False),
    ("Duelos", "Duelos ganhos/90", "duels_won_total_overall", "dec", False, False),
    ("Duelos", "Bolas aéreas ganhas/90", "aerial_duels_won_total_overall", "dec", False, False),
    ("Disciplina", "Faltas cometidas/90", "fouls_committed_total_overall", "dec", False, True),
    ("Disciplina", "Cartões ponderados/90 (amarelo 1, vermelho 3)", "_cart", "dec", True, True),
    ("Goleiro", "Defesas/90", "saves_total_overall", "dec", False, False),
    ("Goleiro", "Chutes enfrentados/90", "shots_faced_total_overall", "dec", False, False),
    ("Goleiro", "Gols sofridos/90", "conceded_overall", "dec", True, True),
    ("Ritmo", "Minutos por gol", "min_per_goal_overall", "dec", True, False),
    ("Ritmo", "Minutos por assistência", "min_per_assist_overall", "dec", True, False),
    ("Ritmo", "Minutos por cartão", "min_per_card_overall", "dec", True, False),
    ("Ritmo", "Minutos por jogo", "min_per_match", "dec", False, False),
]


def _num(r, col):
    v = r.get(col)
    return None if v is None or pd.isna(v) else float(v)


def montar(r: pd.Series, minutos: float) -> tuple[list, list]:
    """Valores das visões VCA (totais) e ETA (por 90) de um atleta, na ordem das listas VCA e ETA."""
    vca = []
    for _, _, col, tipo, _ in VCA:
        v = _num(r, col)
        vca.append(None if v is None else (round(v) if tipo == "int" else round(v, 2)))
    eta = []
    part = (_num(r, "goals_overall") or 0) + (_num(r, "assists_overall") or 0)
    cart = (_num(r, "yellow_cards_overall") or 0) + PESO_VERMELHO * (_num(r, "red_cards_overall") or 0)
    for _, _, col, _, _, _ in ETA:
        if col.startswith("min_per"):
            v = _num(r, col)
            eta.append(None if v is None or v <= 0 else round(v, 1))
            continue
        if minutos is None or minutos < 90:
            eta.append(None)
            continue
        if col == "distance_travelled_total_overall":      # a fonte já traz a distância por 90
            v = _num(r, "distance_travelled_per_90_overall")
            eta.append(None if v is None else round(v, 2))
            continue
        total = part if col == "_part" else cart if col == "_cart" else _num(r, col)
        eta.append(None if total is None else round(total * 90 / minutos, 2))
    return vca, eta


def finalizar(linhas: list[dict]) -> None:
    """Zera como "sem dado" o que a fonte não coleta na liga (vem tudo 0) e calcula a posição ETA entre os da mesma função."""
    df_v = pd.DataFrame([l["_vca"] for l in linhas], columns=range(len(VCA)))
    df_e = pd.DataFrame([l["_eta"] for l in linhas], columns=range(len(ETA)), dtype=float)
    meta = pd.DataFrame({"liga": [l["liga_id"] for l in linhas], "pos": [l["posicao"] for l in linhas],
                         "ok": [(l["min"] or 0) >= 450 for l in linhas]})
    for liga, g in meta[meta["ok"]].groupby("liga"):
        for i, item in enumerate(VCA):
            s = df_v.loc[g.index, i].dropna()
            if not item[4] and len(s) >= 20 and (s != 0).mean() < 0.10:
                df_v.loc[meta["liga"] == liga, i] = None
        for i, item in enumerate(ETA):
            s = df_e.loc[g.index, i].dropna()
            if not item[4] and len(s) >= 20 and (s != 0).mean() < 0.10:
                df_e.loc[meta["liga"] == liga, i] = None
    pct = pd.DataFrame(index=df_e.index, columns=range(len(ETA)), dtype=float)
    for pos, g in meta[meta["ok"]].groupby("pos"):
        for i, item in enumerate(ETA):
            if item[1].startswith("Minutos"):
                continue
            s = df_e.loc[g.index, i]
            if s.notna().sum() >= 20:
                pct.loc[g.index, i] = (30 + 69 * s.rank(pct=True, ascending=not item[5]).where(s.notna()))
    for k, l in enumerate(linhas):
        l["vca"] = [None if pd.isna(x) else x for x in df_v.loc[k].tolist()]
        l["eta"] = [None if pd.isna(x) else x for x in df_e.loc[k].tolist()]
        l["eta_pct"] = [None if pd.isna(x) else int(round(x)) for x in pct.loc[k].tolist()] if meta.loc[k, "ok"] else None
        del l["_vca"], l["_eta"]


def descricao() -> dict:
    return {
        "vca": [{"grupo": g, "rotulo": r, "tipo": t} for g, r, _, t, _ in VCA],
        "eta": [{"grupo": g, "rotulo": r, "tipo": t, "menos_melhor": n} for g, r, _, t, _, n in ETA],
    }
