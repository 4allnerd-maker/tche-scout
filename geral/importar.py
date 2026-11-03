"""Módulo Geral: lê os CSVs do FootyStats (Premium) em dados_geral/csv/ e gera os JSONs do site em site/dados/.

Nome esperado (padrão do download): brazil-{liga}-{tipo}-{ano}-to-{ano}-stats.csv
Tipos lidos: league (resumo da liga), matches (jogos), teams + teams2 (times), players (jogadores).
Campos de odds/apostas dos CSVs são ignorados de propósito (o Tchê Scout não trata de apostas).

Saídas:
  site/dados/ligas.json                    índice das ligas/temporadas
  site/dados/liga/{liga}-{ano}.json        resumo + times + jogos da liga
  site/dados/jogadores/{liga}-{ano}.json   jogadores da liga (quando o CSV de jogadores existe)

Uso: python geral/importar.py
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

import colunas
import skills

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "dados_geral" / "csv"
OUT_DIR = ROOT / "site" / "dados"

def posicao(txt) -> str | None:
    """Padroniza as posições do FootyStats (Forward, Centre Back, Defensive Midfield...) em 4 grupos."""
    t = str(txt).lower()
    if "coach" in t or t == "nan":
        return None
    if "goal" in t:
        return "Goleiro"
    if "midfield" in t:
        return "Meia"
    if "back" in t or "defend" in t:
        return "Defensor"
    if "forward" in t or "wing" in t or "striker" in t:
        return "Atacante"
    return None

LIGAS = {
    "serie-a": "Brasileirão Série A", "serie-b": "Brasileirão Série B", "serie-c": "Brasileirão Série C",
    "serie-d": "Brasileirão Série D", "copa-do-brasil": "Copa do Brasil", "supercopa-do-brasil": "Supercopa do Brasil",
    "gaucho-1": "Gauchão", "gaucho-2": "Gauchão Série A2", "gaucho-3": "Gauchão Série B",
    "paulista-a1": "Paulistão A1", "paulista-a2": "Paulistão A2", "carioca-1": "Carioca", "mineiro-1": "Mineiro",
    "paranaense-1": "Paranaense", "catarinense-1": "Catarinense", "baiano-1": "Baiano", "pernambucano-1": "Pernambucano",
    "cearense-1": "Cearense", "goiano-1": "Goiano", "acreano": "Acreano", "alagoano": "Alagoano",
    "amapaense": "Amapaense", "amazonense": "Amazonense", "brasiliense": "Brasiliense", "maranhense": "Maranhense",
    "matogrossense": "Mato-Grossense", "piauiense": "Piauiense", "sergipano": "Sergipano",
}

JOGADOR = {
    "age": "idade", "nationality": "nacionalidade", "Current Club": "clube", "appearances_overall": "jogos",
    "games_started": "titular", "minutes_played_overall": "min", "goals_overall": "gols",
    "assists_overall": "assist", "penalty_goals": "gols_penalti", "yellow_cards_overall": "amarelos",
    "red_cards_overall": "vermelhos", "clean_sheets_overall": "jogos_sem_sofrer", "conceded_overall": "gols_sofridos",
    "xg_total_overall": "xg", "xa_total_overall": "xa", "npxg_total_overall": "npxg",
    "shots_total_overall": "chutes", "shots_on_target_total_overall": "chutes_alvo",
    "passes_total_overall": "passes", "pass_completion_rate_overall": "passes_pct",
    "key_passes_total_overall": "passes_chave", "chances_created_total_overall": "chances_criadas",
    "dribbles_successful_total_overall": "dribles", "tackles_total_overall": "desarmes",
    "interceptions_total_overall": "interceptacoes", "clearances_total_overall": "cortes",
    "duels_won_total_overall": "duelos_ganhos", "duels_won_percentage_overall": "duelos_pct",
    "aerial_duels_won_total_overall": "aereos_ganhos", "fouls_committed_total_overall": "faltas",
    "fouls_drawn_total_overall": "faltas_sofridas", "saves_total_overall": "defesas",
    "save_percentage_overall": "defesas_pct", "average_rating_overall": "nota", "shirt_number": "camisa",
}

TIME = {
    "team_name": "nome_oficial", "league_position": "pos", "matches_played": "j", "wins": "v", "draws": "e",
    "losses": "d", "goals_scored": "gp", "goals_conceded": "gc", "goal_difference": "sg",
    "points_per_game": "ppg", "xg_for_avg_overall": "xg_pro", "xg_against_avg_overall": "xg_contra",
    "average_possession": "posse", "corners_per_match": "escanteios_jogo", "cards_per_match": "cartoes_jogo",
    "clean_sheets": "sem_sofrer", "fouls": "faltas", "shots": "chutes", "shots_on_target": "chutes_alvo",
}
FAIXAS10 = ["0_to_10", "11_to_20", "21_to_30", "31_to_40", "41_to_50", "51_to_60", "61_to_70", "71_to_80", "81_to_90"]


def slug(txt: str) -> str:
    t = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def limpa(v):
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    if isinstance(v, float):
        return round(v, 2)
    return v.item() if hasattr(v, "item") else v


def lista_csv() -> dict[tuple[str, str], dict[str, Path]]:
    achados: dict[tuple[str, str], dict[str, Path]] = {}
    for csv in sorted(CSV_DIR.glob("*.csv")):
        m = re.match(r"^brazil-(?P<liga>.+)-(?P<tipo>league|matches|players|teams2|teams)-(?P<ini>\d{4})-to-(?P<fim>\d{4})-stats",
                     csv.name)
        if m:
            achados.setdefault((m["liga"], m["fim"]), {})[m["tipo"]] = csv
    return achados


def le(csv: Path) -> pd.DataFrame:
    return pd.read_csv(csv, low_memory=False) if csv.stat().st_size > 5 else pd.DataFrame()


TIMES_CSV = ROOT / "geral" / "times_peso.csv"
APELIDOS_CSV = ROOT / "geral" / "apelidos.csv"
PARTICULAS = {"de", "da", "do", "dos", "das", "e", "di", "del", "van", "von", "la", "le"}


def chave_jogador(nome, nascimento) -> str:
    """Identifica o atleta independente do clube (quem troca de time mantém o mesmo apelido)."""
    return slug(f"{nome}-{nascimento}")


def nome_curto_auto(nome: str) -> str:
    """Sugestão automática: primeiro nome + último sobrenome. Apelidos reais vão em geral/apelidos.csv."""
    palavras = [p for p in str(nome).split() if p.lower() not in PARTICULAS]
    if len(palavras) <= 1:
        return palavras[0] if palavras else str(nome)
    return f"{palavras[0]} {palavras[-1]}"


def le_apelidos() -> dict[str, str]:
    if not APELIDOS_CSV.exists():
        return {}
    df = pd.read_csv(APELIDOS_CSV, sep=";", encoding="utf-8-sig", dtype=str).fillna("")
    return {r["chave"]: r["apelido"].strip() for _, r in df.iterrows() if r["apelido"].strip()}


def grava_apelidos(candidatos: dict[str, dict], existentes: dict[str, str]) -> int:
    """Reescreve geral/apelidos.csv: atletas com 450+ minutos (ou já com apelido), preservando o que foi preenchido."""
    linhas = [c for c in candidatos.values() if c["min"] >= 450 or c["chave"] in existentes]
    linhas.sort(key=lambda c: -c["min"])
    df = pd.DataFrame([{"chave": c["chave"], "nome_completo": c["nome"], "clube": c["clube"], "liga": c["liga"],
                        "minutos": int(c["min"]), "sugestao_automatica": nome_curto_auto(c["nome"]),
                        "apelido": existentes.get(c["chave"], "")} for c in linhas])
    df.to_csv(APELIDOS_CSV, sep=";", index=False, encoding="utf-8-sig")
    return len(df)


def jogadores(df: pd.DataFrame, liga_id: str, nome_liga: str, aviso: list[str], apelidos: dict[str, str]) -> list[dict]:
    saida = []
    for _, r in df.iterrows():
        nome, pos = r.get("full_name"), posicao(r.get("position"))
        clube = r.get("Current Club")
        if pd.isna(nome) or not str(nome).strip():
            aviso.append(f"{liga_id}: linha sem nome ({clube})")
            continue
        if pos is None:
            aviso.append(f"{liga_id}: {nome} — posição '{r.get('position')}' fora do padrão")
            continue
        jogos = r["appearances_overall"] if pd.notna(r.get("appearances_overall")) else 0
        gols = r["goals_overall"] if pd.notna(r.get("goals_overall")) else 0
        if jogos > 0 and gols > 5 * jogos:
            aviso.append(f"{liga_id}: {nome} — {gols} gols em {jogos} jogo(s), dado inconsistente")
            continue
        if pd.notna(r.get("minutes_played_overall")) and r["minutes_played_overall"] < 0:
            aviso.append(f"{liga_id}: {nome} — minutos negativos na fonte, dado inconsistente")
            continue
        reg = {"id": slug(f"{nome}-{r.get('birthday_GMT')}-{clube}"), "nome": str(nome).strip(), "posicao": pos,
               "nascimento": limpa(r.get("birthday_GMT")), "liga": nome_liga, "liga_id": liga_id,
               "temporada": int(r["season"])}
        reg["chave"] = chave_jogador(nome, r.get("birthday_GMT"))
        reg["apelido"] = apelidos.get(reg["chave"])
        reg["nome_curto"] = reg["apelido"] or nome_curto_auto(reg["nome"])
        for col, campo in JOGADOR.items():
            reg[campo] = limpa(r.get(col))
        reg["tem_avancadas"] = reg["xg"] is not None
        reg["_m"] = skills.metricas(r, reg["min"] or 0)
        reg["_vca"], reg["_eta"] = colunas.montar(r, reg["min"] or 0)
        min_ = reg["min"] or 0
        for campo in ("gols", "assist", "xg", "xa", "chutes", "desarmes", "passes_chave"):
            v = reg.get(campo)
            reg[f"{campo}_90"] = round(v * 90 / min_, 2) if (v is not None and min_ >= 90) else None
        saida.append(reg)
    return saida


def times(t: pd.DataFrame, t2: pd.DataFrame) -> list[dict]:
    if t.empty:
        return []
    if not t2.empty:
        extra = t2[["team_name", "shots_per_match_overall", "shots_on_target_per_match_overall",
                    "average_attendance_overall"]]
        t = t.merge(extra, on="team_name", how="left")
    saida = []
    for _, r in t.iterrows():
        reg = {"nome": r["common_name"] if pd.notna(r.get("common_name")) else r["team_name"]}
        for col, campo in TIME.items():
            reg[campo] = limpa(r.get(col))
        reg["pts"] = int((reg["v"] or 0) * 3 + (reg["e"] or 0))
        if reg["pos"] is not None:
            reg["pos"] = int(reg["pos"]) or None
        reg["chutes_jogo"] = limpa(r.get("shots_per_match_overall"))
        reg["chutes_alvo_jogo"] = limpa(r.get("shots_on_target_per_match_overall"))
        reg["publico_medio"] = limpa(r.get("average_attendance_overall"))
        reg["gols_pro_faixa"] = [limpa(r.get(f"goals_scored_min_{f}")) or 0 for f in FAIXAS10]
        reg["gols_contra_faixa"] = [limpa(r.get(f"goals_conceded_min_{f}")) or 0 for f in FAIXAS10]
        saida.append(reg)
    return saida


def jogos(m: pd.DataFrame) -> list[dict]:
    if m.empty:
        return []
    saida = []
    for _, r in m.iterrows():
        feito = r.get("status") == "complete"
        quando = pd.to_datetime(r.get("timestamp"), unit="s", errors="coerce")
        if pd.notna(quando):
            quando = quando - pd.Timedelta(hours=3)  # GMT -> Brasília
        g = lambda c: limpa(r.get(c)) if feito else None  # noqa: E731
        saida.append({
            "data": quando.strftime("%Y-%m-%d %H:%M") if pd.notna(quando) else None,
            "rodada": limpa(r.get("Game Week")), "status": {"complete": "realizado", "suspended": "suspenso"}.get(r.get("status"), "agendado"),
            "casa": r["home_team_name"], "fora": r["away_team_name"],
            "gols_casa": g("home_team_goal_count"), "gols_fora": g("away_team_goal_count"),
            "ht_casa": g("home_team_goal_count_half_time"), "ht_fora": g("away_team_goal_count_half_time"),
            "xg_casa": g("team_a_xg"), "xg_fora": g("team_b_xg"),
            "chutes_casa": g("home_team_shots"), "chutes_fora": g("away_team_shots"),
            "posse_casa": g("home_team_possession"), "posse_fora": g("away_team_possession"),
            "escanteios_casa": g("home_team_corner_count"), "escanteios_fora": g("away_team_corner_count"),
            "amarelos_casa": g("home_team_yellow_cards"), "amarelos_fora": g("away_team_yellow_cards"),
            "vermelhos_casa": g("home_team_red_cards"), "vermelhos_fora": g("away_team_red_cards"),
            "arbitro": limpa(r.get("referee")), "estadio": limpa(r.get("stadium_name")),
            "publico": g("attendance"),
        })
    saida.sort(key=lambda j: (j["data"] or "9"))
    return saida


def resumo(l: pd.DataFrame) -> dict:
    if l.empty:
        return {}
    r = l.iloc[0]
    faixas = [("0-15", "0_to_15"), ("16-30", "16_to_30"), ("31-45", "31_to_45"), ("46-60", "46_to_60"),
              ("61-75", "61_to_75"), ("76-90", "76_to_90")]
    return {
        "status": limpa(r.get("status")), "n_clubes": limpa(r.get("number_of_clubs")),
        "jogos_total": limpa(r.get("total_matches")), "jogos_feitos": limpa(r.get("matches_completed")),
        "rodada": limpa(r.get("game_week")), "rodadas_total": limpa(r.get("total_game_week")),
        "progresso": limpa(r.get("progress")), "media_gols": limpa(r.get("average_goals_per_match")),
        "gols_casa": limpa(r.get("average_scored_home_team")), "gols_fora": limpa(r.get("average_scored_away_team")),
        "ambos_marcam_pct": limpa(r.get("btts_percentage")), "sem_sofrer_pct": limpa(r.get("clean_sheets_percentage")),
        "vantagem_casa_pct": limpa(r.get("home_advantage_percentage")),
        "escanteios_jogo": limpa(r.get("average_corners_per_match")), "cartoes_jogo": limpa(r.get("average_cards_per_match")),
        "xg_jogo": limpa(r.get("xg_avg_per_match")),
        "faixas": [{"faixa": a, "gols": limpa(r.get(f"goals_min_{b}")) or 0} for a, b in faixas],
    }


def le_times_peso() -> dict[str, dict]:
    """geral/times_peso.csv: colunas editáveis por clube (classe_manual, temporadas_serie_a, peso_clube 0-100, observacao)."""
    if not TIMES_CSV.exists():
        return {}
    df = pd.read_csv(TIMES_CSV, sep=";", encoding="utf-8-sig", dtype=str).fillna("")
    saida = {}
    for _, r in df.iterrows():
        num = lambda v: float(v.replace(",", ".")) if v.strip() else None  # noqa: E731
        saida[r["time"]] = {"classe_manual": r["classe_manual"].strip().upper() or None,
                            "temporadas_serie_a": num(r["temporadas_serie_a"]), "peso_clube": num(r["peso_clube"])}
    return saida


def grava_times_peso(classes: dict[str, str], ligas: dict[str, list], existentes: dict[str, dict]) -> int:
    ant = pd.read_csv(TIMES_CSV, sep=";", encoding="utf-8-sig", dtype=str).fillna("").set_index("time").to_dict("index")         if TIMES_CSV.exists() else {}
    linhas = [{"time": t, "classe_automatica": classes.get(t, "D"), "ligas_em_2026": " | ".join(ligas.get(t, [])),
               "classe_manual": ant.get(t, {}).get("classe_manual", ""),
               "temporadas_serie_a": ant.get(t, {}).get("temporadas_serie_a", ""),
               "peso_clube": ant.get(t, {}).get("peso_clube", ""), "observacao": ant.get(t, {}).get("observacao", "")}
              for t in sorted(set(classes) | set(ligas))]
    pd.DataFrame(linhas).to_csv(TIMES_CSV, sep=";", index=False, encoding="utf-8-sig")
    return len(linhas)


MIN_JOGOS_TIME = 5  # com menos jogos do time na competição, o papel não é calculado (amostra curta demais)
FAIXAS_PAPEL = [(75, "Titular absoluto"), (55, "Titular"), (35, "Rodízio"), (15, "Reserva"), (0, "Elenco")]


def papel_no_time(jogadores_liga: list[dict], times_liga: list[dict]) -> None:
    """Papel do jogador no time pela participação nos MINUTOS do time na competição (jogos do time x 90)."""
    jogos_time = {t["nome"]: t["j"] for t in times_liga if t.get("j")}
    for j in jogadores_liga:
        tj = jogos_time.get(j["clube"])
        j["jogos_time"], j["pct_minutos"], j["pct_titular"], j["papel"] = tj, None, None, None
        if not tj or tj < MIN_JOGOS_TIME or j["min"] is None:
            continue
        pct = max(0.0, min(100.0, 100 * j["min"] / (tj * 90)))
        j["pct_minutos"] = round(pct)
        if j.get("titular") is not None:
            j["pct_titular"] = round(min(100.0, 100 * j["titular"] / tj))
        j["papel"] = next(nome for corte, nome in FAIXAS_PAPEL if pct >= corte)


def classes_dos_times(liga_json: dict) -> dict[str, str]:
    """Classe do time = a melhor série nacional em que aparece (A, B, C ou D); estaduais e demais = D."""
    ordem = {"serie-a": "A", "serie-b": "B", "serie-c": "C", "serie-d": "D"}
    classes: dict[str, str] = {}
    for liga_id in ("serie-d", "serie-c", "serie-b", "serie-a"):  # a última a escrever (a melhor) vence
        for d in liga_json.values():
            if d["id"] == liga_id:
                for t in d["times"]:
                    classes[t["nome"]] = ordem[liga_id]
    return classes


def times_globais(liga_json: dict, classes: dict[str, str]) -> dict:
    """Perfil de cada time em TODAS as competições juntas, separado pela classe do adversário (A/B/C/D)."""
    acc: dict[str, dict[str, dict]] = {}
    ligas: dict[str, set] = {}
    for d in liga_json.values():
        for j in d["jogos"]:
            if j["status"] != "realizado" or j["gols_casa"] is None:
                continue
            for lado, outro in (("casa", "fora"), ("fora", "casa")):
                nome, adv = j[lado], j[outro]
                ligas.setdefault(nome, set()).add(d["nome"])
                a = acc.setdefault(nome, {}).setdefault(classes.get(adv, "D"), {
                    "j": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0, "xgp": [], "xgc": [], "chutes": [], "chutes_sofridos": [], "posse": []})
                gp, gc = j[f"gols_{lado}"], j[f"gols_{outro}"]
                a["j"] += 1; a["gp"] += gp; a["gc"] += gc
                a["v" if gp > gc else ("e" if gp == gc else "d")] += 1
                for campo, chave in (("xgp", f"xg_{lado}"), ("xgc", f"xg_{outro}"), ("chutes", f"chutes_{lado}"),
                                     ("chutes_sofridos", f"chutes_{outro}"), ("posse", f"posse_{lado}")):
                    if j.get(chave) is not None:
                        a[campo].append(j[chave])
    saida = {}
    for nome, por_classe in acc.items():
        vs = {}
        for c, a in por_classe.items():
            m = lambda xs: round(sum(xs) / len(xs), 2) if xs else None  # noqa: E731
            vs[c] = {"j": a["j"], "v": a["v"], "e": a["e"], "d": a["d"], "gp": a["gp"], "gc": a["gc"],
                     "pts": a["v"] * 3 + a["e"], "aproveitamento": round(100 * (a["v"] * 3 + a["e"]) / (3 * a["j"])),
                     "xg_pro": m(a["xgp"]), "xg_contra": m(a["xgc"]), "chutes": m(a["chutes"]),
                     "chutes_sofridos": m(a["chutes_sofridos"]), "posse": m(a["posse"])}
        saida[nome] = {"classe": classes.get(nome, "D"), "ligas": sorted(ligas.get(nome, [])), "vs": vs}
    return saida


def main() -> int:
    achados = lista_csv()
    if not achados:
        print(f"Nenhum CSV no padrão brazil-*-stats.csv em {CSV_DIR}")
        return 1
    for pasta in ("liga", "jogadores"):
        shutil.rmtree(OUT_DIR / pasta, ignore_errors=True)
        (OUT_DIR / pasta).mkdir(parents=True, exist_ok=True)
    indice, avisos, candidatos, apelidos, por_liga, liga_json = [], [], {}, le_apelidos(), {}, {}
    for (liga_id, ano), arq in sorted(achados.items()):
        nome = LIGAS.get(liga_id, liga_id.replace("-", " ").title())
        chave = f"{liga_id}-{ano}"
        l = resumo(le(arq["league"])) if "league" in arq else {}
        ts = times(le(arq["teams"]), le(arq["teams2"]) if "teams2" in arq else pd.DataFrame()) if "teams" in arq else []
        js = jogos(le(arq["matches"])) if "matches" in arq else []
        jg = jogadores(le(arq["players"]), liga_id, nome, avisos, apelidos) if "players" in arq else []
        for j in jg:
            c = candidatos.setdefault(j["chave"], {"chave": j["chave"], "nome": j["nome"], "clube": j["clube"],
                                                   "liga": j["liga"], "min": 0})
            if (j["min"] or 0) > c["min"]:
                c.update(clube=j["clube"], liga=j["liga"], min=j["min"] or 0)
        liga_json[chave] = {"id": liga_id, "chave": chave, "nome": nome, "temporada": int(ano), "resumo": l, "times": ts, "jogos": js}
        por_liga[chave] = jg
        indice.append({"chave": chave, "id": liga_id, "nome": nome, "temporada": int(ano), "times": len(ts),
                       "jogos": len([j for j in js if j["status"] == "realizado"]), "jogos_total": len(js),
                       "jogadores": len(jg), "progresso": l.get("progresso"), "status": l.get("status")})
        print(f"{chave:28} times={len(ts):3} jogos={len(js):4} jogadores={len(jg):4}")
    pesos = le_times_peso()
    classes = classes_dos_times(liga_json)
    for t, v in pesos.items():
        if v["classe_manual"] in ("A", "B", "C", "D"):
            classes[t] = v["classe_manual"]
    for d in liga_json.values():
        for t in d["times"]:
            t["classe"] = classes.get(t["nome"], "D")
        for j in d["jogos"]:
            j["classe_casa"], j["classe_fora"] = classes.get(j["casa"], "D"), classes.get(j["fora"], "D")
        (OUT_DIR / "liga" / f"{d['chave']}.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    globais = times_globais(liga_json, classes)
    for t, g in globais.items():
        g["temporadas_serie_a"], g["peso_clube"] = pesos.get(t, {}).get("temporadas_serie_a"), pesos.get(t, {}).get("peso_clube")
    (OUT_DIR / "times.json").write_text(json.dumps(globais, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Times: {grava_times_peso(classes, {t: g['ligas'] for t, g in globais.items()}, pesos)} em {TIMES_CSV.name} "
          f"({sum(1 for v in pesos.values() if v['peso_clube'] is not None)} com peso preenchido)")
    for chave, jg in por_liga.items():
        papel_no_time(jg, liga_json[chave]["times"])
    todos = [j for jg in por_liga.values() for j in jg]
    colunas.finalizar(todos)  # visões VCA (brutos) e ETA (por 90) + posição ETA
    skills.avalia(todos)  # notas, OVR, índices e rankings: calculados com todas as ligas juntas
    for chave, jg in por_liga.items():
        if jg:
            (OUT_DIR / "jogadores" / f"{chave}.json").write_text(json.dumps(jg, ensure_ascii=False, separators=(",", ":")),
                                                                  encoding="utf-8")
    (OUT_DIR / "colunas.json").write_text(json.dumps(colunas.descricao(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    avaliados = [j for j in todos if j["ovr"] is not None]
    (OUT_DIR / "ranking.json").write_text(json.dumps(
        {"min_minutos": skills.MIN_MINUTOS, "categorias": {k: v[0] for k, v in skills.CATEGORIAS.items()},
         "indices": {k: v[0] for k, v in skills.INDICES.items()}, "atributos": {k: v[0] for k, v in skills.ATRIBUTOS.items()},
         "jogadores": avaliados}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Notas: {len(avaliados)} jogadores com {skills.MIN_MINUTOS}+ minutos receberam OVR")
    (OUT_DIR / "ligas.json").write_text(json.dumps(
        {"gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"), "fonte": "FootyStats", "ligas": indice},
        ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT_DIR / "jogadores.json").unlink(missing_ok=True)
    (OUT_DIR / "meta.json").unlink(missing_ok=True)
    print(f"\nApelidos: {grava_apelidos(candidatos, apelidos)} atletas em {APELIDOS_CSV.name} "
          f"({len(apelidos)} com apelido preenchido)")
    print(f"\nOK: {len(indice)} liga(s)/temporada(s), {sum(i['jogadores'] for i in indice)} jogadores -> {OUT_DIR}")
    if avisos:
        print(f"\n{len(avisos)} linha(s) de jogador descartada(s):")
        for a in avisos[:12]:
            print("  -", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
