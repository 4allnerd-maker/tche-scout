"""Identidade visual do Tchê Scout: dark mode esportivo (verde farroupilha + dourado, com acentos
vivos) e blocos de layout compartilhados."""

from __future__ import annotations

import plotly.io as pio
import streamlit as st

from config import NOME

pio.templates.default = "plotly_dark"

COR = {
    "verde": "#2ECC71",
    "verde_escuro": "#0E6B3F",
    "dourado": "#F2C230",
    "vermelho": "#FF5468",
    "azul": "#3FA7FF",
    "fundo": "#0D1B14",
    "fundo_cartao": "#132620",
    "fundo_suave": "#17302475",
    "borda": "#24392C",
    "texto": "#EAF2EC",
    "texto_suave": "#9FB3A6",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;700;800&display=swap');
html, body, .stApp {{ background: {COR['fundo']} !important; }}
.stMarkdown, .stCaption, label, p, span, div {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3, .ts-hero h1 {{ font-family: 'Archivo Black', 'Inter', sans-serif !important; font-weight: 400; }}
:root {{ --verde:{COR['verde']}; --verde-escuro:{COR['verde_escuro']}; --dourado:{COR['dourado']}; }}
.block-container {{ padding-top: 2rem; max-width: 1250px; }}
h1, h2, h3 {{ color: {COR['texto']}; letter-spacing: -0.01em; }}
h1 {{ background: linear-gradient(90deg, {COR['verde']}, {COR['dourado']});
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  display: inline-block; }}
[data-testid="stMetric"] {{ background:{COR['fundo_cartao']}; border:1px solid {COR['borda']};
  border-radius:12px; padding:.9rem 1rem; }}
[data-testid="stMetricValue"] {{ color: {COR['verde']}; font-weight: 800; }}
[data-testid="stMetricLabel"] {{ color: {COR['texto_suave']}; }}
div[data-testid="stTabs"] button[aria-selected="true"] {{ color: {COR['verde']} !important;
  border-bottom-color: {COR['dourado']} !important; }}
[data-testid="stSidebar"] {{ background: #0A1510; border-right: 1px solid {COR['borda']}; }}
[data-testid="stDataFrame"] {{ border:1px solid {COR['borda']}; border-radius:10px; overflow:hidden; }}
.stButton button, .stDownloadButton button, .stLinkButton a {{ border-radius:8px; }}
hr {{ border-color: {COR['borda']} !important; }}
.ts-hero {{
  background: radial-gradient(circle at 15% 20%, #163B28 0%, {COR['fundo']} 55%),
    linear-gradient(120deg, {COR['verde_escuro']} 0%, #0A2E1C 100%);
  border-radius: 16px; padding: 2.4rem 2.2rem; color: #fff; margin-bottom: 1.2rem;
  border: 1px solid {COR['borda']}; border-bottom: 4px solid {COR['dourado']};
  box-shadow: 0 8px 28px rgba(0,0,0,.35);
}}
.ts-hero {{ display:flex; align-items:center; gap:2rem; }}
.ts-hero img {{ height: 190px; flex: 0 0 auto; filter: drop-shadow(0 6px 18px rgba(0,0,0,.4)); }}
.ts-hero h1 {{ color:#fff; -webkit-text-fill-color:#fff; font-size: 3rem; margin:0 0 .3rem 0;
  text-transform: uppercase; line-height:1.05; }}
@media (max-width: 700px) {{ .ts-hero {{ flex-direction:column; text-align:center; }} .ts-hero img {{ height:120px; }} }}
.ts-hero h1 span {{ color: {COR['dourado']}; }}
.ts-hero p {{ font-size: 1.15rem; opacity:.92; max-width: 46rem; margin:.2rem 0; color:#DCEAE1; }}
.ts-tag {{ display:inline-block; background:rgba(242,194,48,.14); color:{COR['dourado']};
  border:1px solid rgba(242,194,48,.35); border-radius:999px; padding:.15rem .8rem;
  font-size:.82rem; margin: .8rem .4rem 0 0; font-weight:600; }}
.ts-card {{ background:{COR['fundo_cartao']}; border:1px solid {COR['borda']}; border-radius:14px;
  padding:1.1rem 1.2rem; height:100%; transition: border-color .15s, transform .15s;
  box-shadow: 0 1px 3px rgba(0,0,0,.25); }}
.ts-card:hover {{ border-color:{COR['verde']}; transform: translateY(-2px); }}
.ts-card h4 {{ margin:.1rem 0 .35rem 0; color:{COR['texto']}; }}
.ts-card p {{ margin:0; color:{COR['texto_suave']}; font-size:.95rem; line-height:1.5; }}
.ts-card .ico {{ font-size:1.6rem; }}
.ts-destaque {{ background:linear-gradient(135deg, rgba(46,204,113,.12), rgba(242,194,48,.08));
  border-left:4px solid {COR['dourado']}; border-radius:10px; padding:1rem 1.2rem; color:{COR['texto']}; }}
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
        "Estatísticas de scout — não é conteúdo de apostas. Leia a aba <b>Metodologia</b> para entender como os números são feitos e onde podem ocorrer equívocos.</div>",
        unsafe_allow_html=True,
    )
