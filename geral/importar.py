"""Módulo Geral: lê os CSVs do FootyStats (Premium) em dados_geral/csv/ e gera os JSONs do site em site/dados/.

Nome esperado do arquivo (padrão do próprio download): {pais}-{liga}-players-{ano}-to-{ano}-stats.csv
Hoje só os arquivos de jogadores ("-players-") são processados; os demais tipos são listados e ignorados.

Uso: python geral/importar.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "dados_geral" / "csv"
OUT_DIR = ROOT / "site" / "dados"

POSICAO = {"Goalkeeper": "Goleiro", "Defender": "Defensor", "Midfielder": "Meia", "Central Midfield": "Meia",
           "Forward": "Atacante", "Left Wing": "Atacante", "Right Wing": "Atacante"}

LIGAS = {
    "serie-a": "Brasileirão Série A", "serie-b": "Brasileirão Série B", "serie-c": "Brasileirão Série C",
    "serie-d": "Brasileirão Série D", "copa-do-brasil": "Copa do Brasil", "gaucho-1": "Gauchão",
    "gaucho-2": "Gauchão Série A2", "gaucho-3": "Gauchão Série B", "paulista-a1": "Paulistão A1",
    "carioca-1": "Carioca", "mineiro-1": "Mineiro", "paranaense-1": "Paranaense", "catarinense-1": "Catarinense",
    "baiano-1": "Baiano", "pernambucano-1": "Pernambucano", "cearense-1": "Cearense", "goiano-1": "Goiano",
}

# coluna do CSV -> campo no JSON (só o que o site usa; o CSV tem ~270 colunas)
CAMPOS = {
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


def slug(txt: str) -> str:
    t = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def limpa(v):
    if pd.isna(v):
        return None
    if isinstance(v, float):
        return round(v, 2)
    return v.item() if hasattr(v, "item") else v


def liga_do_arquivo(nome: str) -> tuple[str, str] | None:
    m = re.match(r"^(?P<pais>[a-z]+)-(?P<liga>.+)-players-(?P<ini>\d{4})-to-(?P<fim>\d{4})-stats", nome)
    if not m:
        return None
    chave = m["liga"]
    return chave, LIGAS.get(chave, chave.replace("-", " ").title())


def processa(csv: Path, descartes: list[str]) -> list[dict]:
    achou = liga_do_arquivo(csv.stem.split(" (")[0])
    if not achou:
        return []
    chave, nome_liga = achou
    df = pd.read_csv(csv, low_memory=False)
    saida = []
    for _, r in df.iterrows():
        nome = r.get("full_name")
        pos = POSICAO.get(r.get("position"))
        if pd.isna(nome) or not str(nome).strip():
            descartes.append(f"{csv.name}: linha sem nome ({r.get('Current Club')})")
            continue
        if pos is None:
            descartes.append(f"{csv.name}: {nome} — posição '{r.get('position')}' fora do padrão")
            continue
        jogos = r.get("appearances_overall") if pd.notna(r.get("appearances_overall")) else 0
        gols = r.get("goals_overall") if pd.notna(r.get("goals_overall")) else 0
        if jogos > 0 and gols > 5 * jogos:
            descartes.append(f"{csv.name}: {nome} — {gols} gols em {jogos} jogo(s), dado inconsistente")
            continue
        reg = {"id": slug(f"{nome}-{r.get('birthday_GMT')}"), "nome": str(nome).strip(), "posicao": pos,
               "nascimento": limpa(r.get("birthday_GMT")), "liga": nome_liga, "liga_id": chave,
               "temporada": int(r["season"])}
        for col, campo in CAMPOS.items():
            reg[campo] = limpa(r.get(col))
        reg["tem_avancadas"] = reg["xg"] is not None
        min_ = reg["min"] or 0
        for campo in ("gols", "assist", "xg", "xa", "chutes", "desarmes", "passes_chave"):
            v = reg.get(campo)
            reg[f"{campo}_90"] = round(v * 90 / min_, 2) if (v is not None and min_ >= 90) else None
        saida.append(reg)
    return saida


def main() -> int:
    arquivos = sorted(CSV_DIR.glob("*.csv"))
    if not arquivos:
        print(f"Nenhum CSV em {CSV_DIR}")
        return 1
    jogadores, descartes, ignorados, vistos = [], [], [], set()
    for csv in arquivos:
        if "-players-" not in csv.name:
            ignorados.append(csv.name)
            continue
        linhas = processa(csv, descartes)
        chaves = {(l["liga_id"], l["temporada"], l["id"], l["clube"]) for l in linhas}
        novas = [l for l in linhas if (l["liga_id"], l["temporada"], l["id"], l["clube"]) not in vistos]
        vistos |= chaves
        jogadores += novas
        print(f"{csv.name}: {len(novas)} jogadores ({len(linhas) - len(novas)} duplicados ignorados)")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "jogadores.json").write_text(json.dumps(jogadores, ensure_ascii=False, separators=(",", ":")),
                                            encoding="utf-8")
    ligas = sorted({(j["liga_id"], j["liga"], j["temporada"]) for j in jogadores})
    meta = {"gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"), "jogadores": len(jogadores),
            "ligas": [{"id": i, "nome": n, "temporada": t} for i, n, t in ligas], "fonte": "FootyStats"}
    (OUT_DIR / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nOK: {len(jogadores)} jogadores em {len(ligas)} liga(s)/temporada(s) -> {OUT_DIR}")
    if descartes:
        print(f"\n{len(descartes)} linha(s) descartada(s):")
        for d in descartes[:15]:
            print("  -", d)
    if ignorados:
        print("\nArquivos de outro tipo (ainda não processados):", ", ".join(ignorados))
    return 0


if __name__ == "__main__":
    sys.exit(main())
