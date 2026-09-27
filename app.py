"""Tchê Scout — roteador do site. Cada aba e um arquivo em pages/ (e inicio.py para a apresentacao)."""

from pathlib import Path

import streamlit as st

import estado
from theme import aplicar_tema

aplicar_tema()
st.logo(str(Path(__file__).parent / "assets" / "logo.svg"), size="large")

navegacao = st.navigation([
    st.Page("inicio.py", title="Início", icon="🏠", default=True),
    st.Page("pages/11_📰_Notícias.py", title="Notícias", icon="📰", url_path="noticias"),
    st.Page("pages/1_📅_Calendário.py", title="Calendário", icon="📅", url_path="calendario"),
    st.Page("pages/2_🏆_Classificações.py", title="Classificações", icon="🏆", url_path="classificacoes"),
    st.Page("pages/3_🎯_Jogadores.py", title="Jogadores", icon="🎯", url_path="jogadores"),
    st.Page("pages/5_🔬_Análise.py", title="Análise", icon="🔬", url_path="analise"),
    st.Page("pages/8_🧾_Jogo.py", title="Jogo & súmula", icon="🧾", url_path="jogo"),
    st.Page("pages/7_⚖️_Arbitragem.py", title="Arbitragem", icon="⚖️", url_path="arbitragem"),
    st.Page("pages/9_🖼️_Relatórios_e_Cards.py", title="Relatórios e cards", icon="🖼️", url_path="relatorios"),
    st.Page("pages/10_📘_Metodologia.py", title="Metodologia", icon="📘", url_path="metodologia"),
    st.Page("pages/6_👤_Quem_sou_eu.py", title="Quem sou eu", icon="👤", url_path="quem-sou-eu"),
    st.Page("pages/4_📣_Anuncie.py", title="Anuncie", icon="📣", url_path="anuncie"),
])
estado.controlar_navegacao(navegacao.title)
navegacao.run()
