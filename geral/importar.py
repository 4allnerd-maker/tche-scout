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


def jogadores(df: pd.DataFrame, liga_id: str, nome_liga: str, aviso: list[str]) -> list[dict]:
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
        reg = {"id": slug(f"{nome}-{r.get('birthday_GMT')}-{clube}"), "nome": str(nome).strip(), "posicao": pos,
               "nascimento": limpa(r.get("birthday_GMT")), "liga": nome_liga, "liga_id": liga_id,
               "temporada": int(r["season"])}
        for col, campo in JOGADOR.items():
            reg[campo] = limpa(r.get(col))
        reg["tem_avancadas"] = reg["xg"] is not None
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


def main() -> int:
    achados = lista_csv()
    if not achados:
        print(f"Nenhum CSV no padrão brazil-*-stats.csv em {CSV_DIR}")
        return 1
    for pasta in ("liga", "jogadores"):
        shutil.rmtree(OUT_DIR / pasta, ignore_errors=True)
        (OUT_DIR / pasta).mkdir(parents=True, exist_ok=True)
    indice, avisos = [], []
    for (liga_id, ano), arq in sorted(achados.items()):
        nome = LIGAS.get(liga_id, liga_id.replace("-", " ").title())
        chave = f"{liga_id}-{ano}"
        l = resumo(le(arq["league"])) if "league" in arq else {}
        ts = times(le(arq["teams"]), le(arq["teams2"]) if "teams2" in arq else pd.DataFrame()) if "teams" in arq else []
        js = jogos(le(arq["matches"])) if "matches" in arq else []
        jg = jogadores(le(arq["players"]), liga_id, nome, avisos) if "players" in arq else []
        (OUT_DIR / "liga" / f"{chave}.json").write_text(json.dumps(
            {"id": liga_id, "chave": chave, "nome": nome, "temporada": int(ano), "resumo": l, "times": ts, "jogos": js},
            ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        if jg:
            (OUT_DIR / "jogadores" / f"{chave}.json").write_text(json.dumps(jg, ensure_ascii=False, separators=(",", ":")),
                                                                  encoding="utf-8")
        indice.append({"chave": chave, "id": liga_id, "nome": nome, "temporada": int(ano), "times": len(ts),
                       "jogos": len([j for j in js if j["status"] == "realizado"]), "jogos_total": len(js),
                       "jogadores": len(jg), "progresso": l.get("progresso"), "status": l.get("status")})
        print(f"{chave:28} times={len(ts):3} jogos={len(js):4} jogadores={len(jg):4}")
    (OUT_DIR / "ligas.json").write_text(json.dumps(
        {"gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"), "fonte": "FootyStats", "ligas": indice},
        ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT_DIR / "jogadores.json").unlink(missing_ok=True)
    (OUT_DIR / "meta.json").unlink(missing_ok=True)
    print(f"\nOK: {len(indice)} liga(s)/temporada(s), {sum(i['jogadores'] for i in indice)} jogadores -> {OUT_DIR}")
    if avisos:
        print(f"\n{len(avisos)} linha(s) de jogador descartada(s):")
        for a in avisos[:12]:
            print("  -", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
