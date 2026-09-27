"""Formações táticas registradas MANUALMENTE (a súmula não traz o desenho do time).
Fontes: (1) data/manual/formacoes.csv, versionado no repositório; (2) o que o usuário digita na sessão.
Valem só na visita atual (sessão do navegador); entram no PDF gerado nesta visita."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent / "data" / "manual" / "formacoes.csv"
COLUNAS = ["jogo_id", "equipe", "formacao", "obs"]
OPCOES = ["", "4-3-3", "4-4-2", "4-2-3-1", "4-1-4-1", "4-3-1-2", "4-5-1", "3-5-2", "3-4-3", "3-4-1-2", "5-3-2", "5-4-1", "Outra"]
CHAVE = "formacoes_manuais"


def _base() -> pd.DataFrame:
    if BASE.exists() and BASE.stat().st_size > 0:
        try:
            return pd.read_csv(BASE, dtype=str).fillna("")[COLUNAS]
        except Exception:  # noqa: BLE001
            pass
    return pd.DataFrame(columns=COLUNAS)


def estado() -> pd.DataFrame:
    """Base do repositório + edições da sessão (a sessão vence em caso de conflito)."""
    if CHAVE not in st.session_state:
        st.session_state[CHAVE] = _base()
    return st.session_state[CHAVE]


def salvar(jogo_id: str, equipe: str, formacao: str, obs: str = "") -> None:
    df = estado()
    df = df[~((df["jogo_id"] == str(jogo_id)) & (df["equipe"] == equipe))]
    if formacao:
        df = pd.concat([df, pd.DataFrame([{"jogo_id": str(jogo_id), "equipe": equipe, "formacao": formacao, "obs": obs}])],
                       ignore_index=True)
    st.session_state[CHAVE] = df


def obter(jogo_id: str, equipe: str) -> tuple[str, str]:
    df = estado()
    x = df[(df["jogo_id"] == str(jogo_id)) & (df["equipe"] == equipe)]
    return (x.iloc[0]["formacao"], x.iloc[0]["obs"]) if len(x) else ("", "")


def exportar_csv() -> bytes:
    return estado().to_csv(index=False).encode("utf-8-sig")


def importar_csv(conteudo: bytes) -> int:
    novo = pd.read_csv(io.BytesIO(conteudo), dtype=str).fillna("")
    faltam = [c for c in COLUNAS if c not in novo.columns]
    if faltam:
        raise ValueError(f"CSV sem as colunas: {', '.join(faltam)}")
    atual = estado()
    junto = pd.concat([atual, novo[COLUNAS]], ignore_index=True).drop_duplicates(["jogo_id", "equipe"], keep="last")
    st.session_state[CHAVE] = junto[junto["formacao"] != ""].reset_index(drop=True)
    return len(novo)


def resumo_por_formacao(d: pd.DataFrame, time: str) -> pd.DataFrame:
    """d = jogos_do_time(...). Cruza com as formações registradas para o time."""
    f = estado()
    f = f[f["equipe"] == time][["jogo_id", "formacao"]]
    x = d.merge(f, on="jogo_id", how="inner")
    if x.empty:
        return pd.DataFrame()
    g = x.groupby("formacao").agg(Jogos=("jogo_id", "count"), V=("res", lambda s: (s == "V").sum()),
                                  E=("res", lambda s: (s == "E").sum()), D=("res", lambda s: (s == "D").sum()),
                                  GP=("gp", "sum"), GC=("gc", "sum"), Pts=("pontos", "sum")).reset_index()
    g["Aproveitamento (%)"] = (g["Pts"] / (g["Jogos"] * 3) * 100).round(1)
    g["Gols pró/jogo"] = (g["GP"] / g["Jogos"]).round(2)
    g["Gols contra/jogo"] = (g["GC"] / g["Jogos"]).round(2)
    return g.rename(columns={"formacao": "Formação"}).drop(columns="Pts").sort_values("Jogos", ascending=False).reset_index(drop=True)


def painel_arquivo() -> None:
    """(Mantido por compatibilidade.) Apenas explica que os registros valem na visita atual."""
    st.caption("As formações que você registra valem nesta visita e entram no PDF/relatório gerado agora; "
               "ao recarregar a página, voltam ao padrão.")
