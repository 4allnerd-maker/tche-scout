"""Carrega os datasets processados (data/processed/*.json) em DataFrames.
O cache do Streamlit é chaveado pela data de modificação dos arquivos: quando o robô diário atualiza os
dados, o site já mostra o novo conteúdo na próxima visita, sem esperar o cache expirar."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROCESSED_DIR = Path(__file__).resolve().parent / "data" / "processed"
TTL = 6 * 60 * 60


def _stamp() -> float:
    """Versão dos dados = quando o meta.json foi gravado pela última vez."""
    meta = PROCESSED_DIR / "meta.json"
    return meta.stat().st_mtime if meta.exists() else 0.0


def _json(nome: str):
    caminho = PROCESSED_DIR / f"{nome}.json"
    if not caminho.exists():
        return [] if nome != "meta" else {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def _datas(df: pd.DataFrame) -> pd.DataFrame:
    if not df.empty and "data" in df:
        df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    return df


def tem_dados() -> bool:
    return (PROCESSED_DIR / "jogos.json").exists()


@st.cache_data(ttl=TTL)
def _carrega(nome: str, versao: float):
    dados = _json(nome)
    if nome == "meta":
        return dados
    return _datas(pd.DataFrame(dados))


def meta() -> dict:
    return _carrega("meta", _stamp())


def jogos() -> pd.DataFrame:
    return _carrega("jogos", _stamp())


def calendario() -> pd.DataFrame:
    return _carrega("calendario", _stamp())


def partidas() -> pd.DataFrame:
    return _carrega("jogadores_partida", _stamp())


def atletas() -> pd.DataFrame:
    return _carrega("atletas", _stamp())


def gols() -> pd.DataFrame:
    return _carrega("gols", _stamp())


def cartoes() -> pd.DataFrame:
    return _carrega("cartoes", _stamp())


def substituicoes() -> pd.DataFrame:
    return _carrega("substituicoes", _stamp())
