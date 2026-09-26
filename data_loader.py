"""Carrega os datasets processados (data/processed/*.json) em DataFrames, com cache do Streamlit."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROCESSED_DIR = Path(__file__).resolve().parent / "data" / "processed"
TTL = 60 * 60  # 1h: o robo atualiza os JSONs, o app recarrega sozinho


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
def meta() -> dict:
    return _json("meta")


@st.cache_data(ttl=TTL)
def jogos() -> pd.DataFrame:
    return _datas(pd.DataFrame(_json("jogos")))


@st.cache_data(ttl=TTL)
def calendario() -> pd.DataFrame:
    return _datas(pd.DataFrame(_json("calendario")))


@st.cache_data(ttl=TTL)
def partidas() -> pd.DataFrame:
    return pd.DataFrame(_json("jogadores_partida"))


@st.cache_data(ttl=TTL)
def atletas() -> pd.DataFrame:
    return pd.DataFrame(_json("atletas"))


@st.cache_data(ttl=TTL)
def gols() -> pd.DataFrame:
    return pd.DataFrame(_json("gols"))


@st.cache_data(ttl=TTL)
def cartoes() -> pd.DataFrame:
    return pd.DataFrame(_json("cartoes"))


@st.cache_data(ttl=TTL)
def substituicoes() -> pd.DataFrame:
    return pd.DataFrame(_json("substituicoes"))
