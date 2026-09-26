"""Identidade visual do Tchê Scout (verde farroupilha + dourado) e blocos de layout compartilhados."""

from __future__ import annotations

import streamlit as st

from config import NOME

COR = {
    "verde": "#0E6B3F",
    "verde_escuro": "#0A3D26",
    "dourado": "#F2B705",
    "vermelho": "#C8102E",
    "fundo_suave": "#F3F6F1",
    "texto": "#16241C",
    "texto_suave": "#5B6B62",
}

CSS = f"""
<style>
:root {{ --verde:{COR['verde']}; --verde-escuro:{COR['verde_escuro']}; --dourado:{COR['dourado']}; }}
.block-container {{ padding-top: 2rem; max-width: 1250px; }}
h1, h2, h3 {{ color: {COR['verde_escuro']}; letter-spacing: -0.01em; }}
[data-testid="stMetricValue"] {{ color: {COR['verde']}; font-weight: 800; }}
[data-testid="stMetricLabel"] {{ color: {COR['texto_suave']}; }}
div[data-testid="stTabs"] button[aria-selected="true"] {{ color: {COR['verde']}; border-bottom-color: {COR['dourado']} !important; }}
.ts-hero {{
  background: linear-gradient(120deg, {COR['verde_escuro']} 0%, {COR['verde']} 100%);
  border-radius: 14px; padding: 2.4rem 2.2rem; color: #fff; margin-bottom: 1.2rem;
  border-bottom: 6px solid {COR['dourado']};
}}
.ts-hero h1 {{ color:#fff; font-size: 2.6rem; margin:0 0 .3rem 0; }}
.ts-hero h1 span {{ color: {COR['dourado']}; }}
.ts-hero p {{ font-size: 1.15rem; opacity:.95; max-width: 46rem; margin:.2rem 0; }}
.ts-tag {{ display:inline-block; background:rgba(255,255,255,.14); border-radius:999px; padding:.15rem .8rem;
  font-size:.82rem; margin: .8rem .4rem 0 0; }}
.ts-card {{ background:#fff; border:1px solid #DCE5DD; border-radius:12px; padding:1.1rem 1.2rem; height:100%;
  box-shadow: 0 1px 2px rgba(10,61,38,.05); }}
.ts-card h4 {{ margin:.1rem 0 .35rem 0; color:{COR['verde_escuro']}; }}
.ts-card p {{ margin:0; color:{COR['texto_suave']}; font-size:.95rem; line-height:1.5; }}
.ts-card .ico {{ font-size:1.6rem; }}
.ts-destaque {{ background:{COR['fundo_suave']}; border-left:6px solid {COR['dourado']}; border-radius:8px; padding:1rem 1.2rem; }}
.ts-rodape {{ color:{COR['texto_suave']}; font-size:.85rem; }}
</style>
"""


def aplicar_tema() -> None:
    """Chamado uma vez pelo roteador (app.py) a cada execucao: configura a pagina e injeta o CSS."""
    st.set_page_config(page_title=NOME, page_icon="⚽", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def cabecalho(titulo: str, subtitulo: str = "") -> None:
    st.markdown(f"# {titulo}")
    if subtitulo:
        st.caption(subtitulo)


def rodape() -> None:
    st.divider()
    st.markdown(
        '<div class="ts-rodape">Dados extraídos das súmulas oficiais publicadas pela Federação Gaúcha de Futebol (FGF). '
        "O Tchê Scout é um projeto independente e não tem vínculo oficial com a FGF ou com os clubes. "
        "Estatísticas de scout — não é conteúdo de apostas.</div>",
        unsafe_allow_html=True,
    )
