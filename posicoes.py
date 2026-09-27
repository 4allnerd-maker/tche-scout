"""Base de posições dos atletas, em camadas — cada posição traz FONTE e CONFIANÇA.

  1. Súmula (exata) ........ goleiro: a súmula marca T(g)/R(g)
  2. Inferida pelos dados ... camisa mais usada + comportamento (aproximação; pode errar)
  3. Fonte aberta .......... pesquisada em notícias/sites de scout, com URL (data/manual/posicoes.csv)
  4. Manual ................ digitada/corrigida pelo usuário na sessão (vale mais que tudo)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import camisas as cm

CSV_PESQUISA = Path(__file__).resolve().parent / "data" / "manual" / "posicoes.csv"
COLUNAS_CSV = ["atleta_id", "posicao", "fonte", "url", "confianca", "data", "obs"]

POSICOES = ["Goleiro", "Lateral direito", "Lateral esquerdo", "Zagueiro", "Volante", "Meia", "Ponta", "Atacante / centroavante"]
ZONA_DA_POSICAO = {"Goleiro": "Goleiro", "Lateral direito": "Defesa", "Lateral esquerdo": "Defesa", "Zagueiro": "Defesa",
                   "Volante": "Meio", "Meia": "Meio", "Ponta": "Ataque", "Atacante / centroavante": "Ataque"}
# convenção camisa -> posição provável (apenas camisas tradicionais 2–11)
POS_DA_CAMISA = {2: "Lateral direito", 3: "Zagueiro", 4: "Zagueiro", 5: "Volante", 6: "Lateral esquerdo", 7: "Ponta",
                 8: "Meia", 9: "Atacante / centroavante", 10: "Meia", 11: "Ponta"}


def normaliza(pos: str | None) -> str | None:
    """Mapeia textos livres (de fontes abertas) para a lista padrão."""
    if not pos:
        return None
    t = pos.strip().lower()
    regras = [("goleir", "Goleiro"), ("lateral-direito", "Lateral direito"), ("lateral direito", "Lateral direito"),
              ("lateral-esquerdo", "Lateral esquerdo"), ("lateral esquerdo", "Lateral esquerdo"), ("lateral", "Lateral direito"),
              ("zagueir", "Zagueiro"), ("beque", "Zagueiro"), ("volante", "Volante"), ("meio-campo", "Meia"), ("meia", "Meia"),
              ("armador", "Meia"), ("ponta", "Ponta"), ("extremo", "Ponta"), ("centroavante", "Atacante / centroavante"),
              ("atacante", "Atacante / centroavante"), ("meia-atacante", "Meia")]
    for chave, padrao in regras:
        if chave in t:
            return padrao
    return pos.strip() if pos.strip() in POSICOES else None


def inferir(partidas: pd.DataFrame) -> pd.DataFrame:
    """Posição inferida pelos dados para cada atleta (camisa principal + flag de goleiro)."""
    p = partidas[partidas["jogou"]].copy()
    if p.empty:
        return pd.DataFrame(columns=["atleta_id", "posicao", "zona", "fonte", "confianca", "camisa_principal"])
    gk = p.groupby("atleta_id")["goleiro"].mean()
    fixo = cm.numeracao_dos_atletas(p).set_index("atleta_id")
    linhas = []
    for aid in p["atleta_id"].unique():
        f = fixo.loc[aid] if aid in fixo.index else None
        cam = int(f["camisa_principal"]) if f is not None else None
        fx = float(f["fixo_pct"]) if f is not None else 0.0
        n = int(f["total"]) if f is not None else 0
        if gk.get(aid, 0) >= 0.5:
            linhas.append((aid, "Goleiro", "Goleiro", "Súmula (goleiro)", 98, cam))
        elif cam in POS_DA_CAMISA:
            conf = min(80, int(35 + fx * 0.35 + min(n, 10) * 1.2))  # nunca passa de 80%: é inferência
            pos = POS_DA_CAMISA[cam]
            linhas.append((aid, pos, ZONA_DA_POSICAO[pos], "Inferida pela camisa", conf, cam))
        else:
            zona = cm.zona(cam, False) if cam else "Variável"
            linhas.append((aid, None, zona if zona != "Variável" else None, "Sem informação (camisa fora do padrão)", 15, cam))
    return pd.DataFrame(linhas, columns=["atleta_id", "posicao", "zona", "fonte", "confianca", "camisa_principal"])


def pesquisadas() -> pd.DataFrame:
    if CSV_PESQUISA.exists() and CSV_PESQUISA.stat().st_size > 0:
        try:
            d = pd.read_csv(CSV_PESQUISA, dtype=str).fillna("")
            return d.reindex(columns=COLUNAS_CSV, fill_value="")
        except Exception:  # noqa: BLE001
            pass
    return pd.DataFrame(columns=COLUNAS_CSV)


def consolidar(partidas: pd.DataFrame) -> pd.DataFrame:
    """Tabela final: inferida + pesquisada (a pesquisada prevalece, exceto goleiro pela súmula)."""
    base = inferir(partidas)
    pq = pesquisadas()
    if not pq.empty:
        pq = pq.assign(posicao=pq["posicao"].map(normaliza)).dropna(subset=["posicao"]).drop_duplicates("atleta_id", keep="last")
        m = base.merge(pq, on="atleta_id", how="left", suffixes=("", "_pq"))
        usa = m["posicao_pq"].notna() & (m["fonte"] != "Súmula (goleiro)")
        m.loc[usa, "posicao"] = m.loc[usa, "posicao_pq"]
        m.loc[usa, "zona"] = m.loc[usa, "posicao_pq"].map(ZONA_DA_POSICAO)
        m.loc[usa, "fonte"] = "Fonte aberta: " + m.loc[usa, "fonte_pq"].fillna("").replace("", "pesquisa")
        m.loc[usa, "confianca"] = pd.to_numeric(m.loc[usa, "confianca_pq"], errors="coerce").fillna(75)
        m["url"] = m["url"].where(usa, "") if "url" in m else ""
        m["url"] = np.where(usa, m.get("url_pq", ""), "")
        m["obs_pesquisa"] = np.where(usa, m.get("obs", ""), "")
        base = m[["atleta_id", "posicao", "zona", "fonte", "confianca", "camisa_principal", "url", "obs_pesquisa"]]
    else:
        base = base.assign(url="", obs_pesquisa="")
    base["confianca"] = base["confianca"].astype(int)
    return base


# ---------------------------------------------------------------- correções manuais (sessão do navegador)
def aplicar_manuais(tabela: pd.DataFrame, manuais: dict) -> pd.DataFrame:
    """manuais: {atleta_id: posicao}. Vale mais que qualquer outra fonte."""
    t = tabela.copy()
    for aid, pos in manuais.items():
        m = t["atleta_id"] == aid
        if m.any() and pos:
            t.loc[m, "posicao"] = pos
            t.loc[m, "zona"] = ZONA_DA_POSICAO.get(pos)
            t.loc[m, "fonte"] = "Manual (você)"
            t.loc[m, "confianca"] = 95
            t.loc[m, "url"] = ""
    return t


def manuais_para_csv(manuais: dict) -> bytes:
    from datetime import date
    linhas = [{"atleta_id": a, "posicao": p, "fonte": "Manual", "url": "", "confianca": 95, "data": date.today().isoformat(), "obs": ""}
              for a, p in manuais.items() if p]
    return pd.DataFrame(linhas, columns=COLUNAS_CSV).to_csv(index=False).encode("utf-8-sig")
