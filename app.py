"""Tchê Scout — roteador do site. Cada aba e um arquivo em pages/ (e inicio.py para a apresentacao)."""

import streamlit as st

from theme import aplicar_tema

aplicar_tema()

navegacao = st.navigation([
    st.Page("inicio.py", title="Início", icon="🏠", default=True),
    st.Page("pages/1_📅_Calendário.py", title="Calendário", icon="📅", url_path="calendario"),
    st.Page("pages/2_🏆_Classificações.py", title="Classificações", icon="🏆", url_path="classificacoes"),
    st.Page("pages/3_🎯_Jogadores.py", title="Jogadores", icon="🎯", url_path="jogadores"),
    st.Page("pages/4_📣_Anuncie.py", title="Anuncie", icon="📣", url_path="anuncie"),
])
navegacao.run()
