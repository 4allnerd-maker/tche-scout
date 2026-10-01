"""Controle do estado da interface: filtros voltam ao zero ao trocar de aba e por um botão 'Limpar filtros'.
As correções feitas pelo usuário (posições e formações) são preservadas durante a visita."""

from __future__ import annotations

import streamlit as st

# O que NÃO é apagado ao limpar: trabalho do usuário nesta visita e controle interno da navegação.
PRESERVAR = {"posicoes_manuais", "formacoes_manuais", "_pagina_atual", "_manter_jogo", "_manter_time"}


CAMPOS_TIME = {"an_time", "an_cat", "an_ano", "an_comp"}


def limpar_filtros(manter_jogo: bool = False, manter_time: bool = False) -> None:
    for k in list(st.session_state.keys()):
        if k in PRESERVAR or (manter_jogo and k == "jogo_id") or (manter_time and k in CAMPOS_TIME):
            continue
        del st.session_state[k]


def controlar_navegacao(pagina: str) -> None:
    """Chame no roteador (app.py) a cada execução: ao mudar de aba, zera os filtros da aba anterior."""
    anterior = st.session_state.get("_pagina_atual")
    if anterior is not None and anterior != pagina:
        manter_jogo = bool(st.session_state.pop("_manter_jogo", False))
        manter_time = bool(st.session_state.pop("_manter_time", False))
        limpar_filtros(manter_jogo=manter_jogo, manter_time=manter_time)
    st.session_state["_pagina_atual"] = pagina


def botao_limpar(chave: str) -> None:
    """Botão que devolve todos os filtros da página ao estado inicial (sem nada selecionado)."""
    if st.button("🧹 Limpar filtros", key=f"limpar_{chave}", help="Volta todos os filtros desta página ao início"):
        limpar_filtros()
        st.rerun()


def barra_limpar(chave: str) -> None:
    """Botão 'Limpar filtros' alinhado à direita, logo acima dos filtros da página."""
    _, c = st.columns([6, 1.7])
    with c:
        botao_limpar(chave)
