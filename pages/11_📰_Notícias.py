import pandas as pd
import streamlit as st

import data_loader as dl
import estado
import leiame
import noticias as nt
from theme import COR, cabecalho, rodape

cabecalho("📰 Notícias", "Transferências, artigos e os resultados de cada rodada dos campeonatos gaúchos.")
leiame.mostrar("noticias")

jogos = dl.jogos() if dl.tem_dados() else None
df = nt.feed(jogos)

if df.empty:
    st.info("Ainda não há notícias publicadas.")
    rodape()
    st.stop()

estado.barra_limpar("news")
c1, c2 = st.columns([2, 3])
cats = ["Todas"] + [c for c in nt.CATEGORIAS if c in df["categoria"].unique()]
cat = c1.selectbox("Categoria", cats, key="news_cat")
busca = c2.text_input("Buscar", placeholder="Palavra-chave no título ou resumo…", key="news_busca")

v = df.copy()
if cat != "Todas":
    v = v[v["categoria"] == cat]
if busca:
    alvo = busca.lower()
    v = v[v["titulo"].str.lower().str.contains(alvo) | v["resumo"].str.lower().str.contains(alvo)]

if v.empty:
    st.info("Nenhuma notícia encontrada para esse filtro.")
    rodape()
    st.stop()


def _card_css(p) -> str:
    ico = nt.ICONE_CAT.get(p["categoria"], "📰")
    data_fmt = p["data"].strftime("%d/%m/%Y") if pd.notna(p["data"]) else ""
    tags = " ".join(f'<span class="ts-tag" style="background:{COR["fundo_suave"]};color:{COR["verde_escuro"]}">{t}</span>'
                    for t in p["tags"][:3])
    return (f'<div class="ts-card" style="margin-bottom:.8rem"><div class="ico">{ico} '
            f'<span style="font-size:.8rem;color:{COR["texto_suave"]};font-family:Inter">{data_fmt} · {p["categoria"]}'
            f'{" · gerado automaticamente" if p["auto"] else ""}</span></div>'
            f'<h4>{p["titulo"]}</h4><p>{p["resumo"]}</p><div style="margin-top:.4rem">{tags}</div></div>')


destaque = v.iloc[0]
st.markdown(_card_css(destaque), unsafe_allow_html=True)
with st.expander(f"Ler: {destaque['titulo']}", expanded=True):
    st.caption(f"Por {destaque['autor']} · {destaque['data'].strftime('%d/%m/%Y') if pd.notna(destaque['data']) else ''}")
    st.markdown(destaque["corpo"])

st.markdown("### Mais notícias")
for _, p in v.iloc[1:].iterrows():
    st.markdown(_card_css(p), unsafe_allow_html=True)
    with st.expander("Ler mais"):
        st.caption(f"Por {p['autor']} · {p['data'].strftime('%d/%m/%Y') if pd.notna(p['data']) else ''}")
        st.markdown(p["corpo"])

st.caption("Resumos de rodada são gerados automaticamente a partir dos dados das súmulas. Artigos e transferências "
           "são escritos pela equipe do Tchê Scout.")
rodape()
