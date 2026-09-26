import base64
from pathlib import Path

import streamlit as st

import data_loader as dl
from config import AUTOR, AUTOR_FUNCAO, NOME, SLOGAN, WHATSAPP_EXIBIR, WHATSAPP_LINK
from theme import rodape

LOGO = base64.b64encode((Path(__file__).parent / "assets" / "logo.svg").read_bytes()).decode()

st.markdown(
    f"""
    <div class="ts-hero">
      <img src="data:image/svg+xml;base64,{LOGO}" alt="Tchê Scout" style="height:190px; width:auto; max-width:none;"/>
      <div>
      <h1>Tchê <span>Scout</span></h1>
      <p><b>{SLOGAN}</b></p>
      <p>Resultados, classificações, perfil dos times e a ficha de cada atleta — dos campeonatos profissionais
         e femininos do Rio Grande do Sul, num só lugar e de graça.</p>
      <span class="ts-tag">Gauchão</span><span class="ts-tag">Série A2</span><span class="ts-tag">Série B</span>
      <span class="ts-tag">Copa FGF</span><span class="ts-tag">Recopa Gaúcha</span><span class="ts-tag">Gauchão Feminino</span>
      <span class="ts-tag">Sub 20 · 17 · 15 Feminino</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if dl.tem_dados():
    m = dl.meta()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jogos analisados", f"{m.get('jogos', 0):,}".replace(",", "."))
    c2.metric("Atletas cadastrados", f"{m.get('atletas', 0):,}".replace(",", "."))
    c3.metric("Gols registrados", f"{m.get('gols', 0):,}".replace(",", "."))
    c4.metric("Última atualização", m.get("gerado_em", "—"))
else:
    st.warning("Base de dados ainda não gerada. Rode `python scraper/build_dataset.py` (veja o README).")

st.markdown("## Por que o Tchê Scout existe")
col_a, col_b = st.columns([3, 2])
with col_a:
    st.markdown(
        """
        O futebol gaúcho é gigante — Gauchão, Série A2, Série B, Copa FGF, categorias femininas — mas quem quer
        **entender o desempenho** de um time ou de um atleta esbarra sempre no mesmo problema: **não existe um site de
        scout que cubra esses campeonatos**. As plataformas de estatística focam nas ligas nacionais e internacionais;
        aqui, o que existe é a **súmula em PDF**, jogo a jogo, no site da federação.

        O Tchê Scout transforma essas súmulas em **dados organizados, padronizados e consultáveis**:
        quem jogou, quanto tempo, quem marcou, quem levou cartão, em que minuto cada time faz e sofre gols.
        """
    )
with col_b:
    st.markdown(
        """
        <div class="ts-destaque">
        <b>A lacuna que ele preenche</b><br/>
        Uma base aberta e atualizada a cada rodada, com o scout que analistas de desempenho, comissões técnicas,
        jornalistas e torcedores precisam — sem depender de planilha manual nem de abrir PDF por PDF.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("## O que você encontra aqui")
cards = [
    ("📅", "Calendário", "pages/1_📅_Calendário.py",
     "Resultados de todos os jogos e a agenda das próximas rodadas, com filtro por competição, ano e time. "
     "W.O. e jogos cancelados aparecem identificados."),
    ("🏆", "Classificações", "pages/2_🏆_Classificações.py",
     "Tabela por competição, ano e fase, com o perfil de cada time: média de gols feitos e sofridos, "
     "casa × fora, disciplina e em quais minutos o time marca e sofre gols."),
    ("🎯", "Jogadores", "pages/3_🎯_Jogadores.py",
     "Painel de atletas com nomes padronizados: jogos, titular, reserva, entradas, substituições, "
     "minutos, gols e cartões — filtrável por ano, competição e time."),
    ("🔬", "Análise", "pages/5_🔬_Análise.py",
     "Escolha um time e veja um painel completo: forma, gols por minuto, 1º × 2º tempo, quem abre o placar, "
     "disciplina, elenco e insights prontos para relatório."),
    ("📣", "Anuncie", "pages/4_📣_Anuncie.py",
     "Quer colocar sua marca diante de quem vive o futebol gaúcho? Veja como apoiar e anunciar."),
]
cols = st.columns(len(cards))
for col, (ico, titulo, pagina, texto) in zip(cols, cards):
    col.markdown(f'<div class="ts-card"><div class="ico">{ico}</div><h4>{titulo}</h4><p>{texto}</p></div>',
                 unsafe_allow_html=True)
    col.page_link(pagina, label=f"Abrir {titulo} →", width="stretch")
st.caption("Clique em “Abrir” em qualquer cartão ou use o menu à esquerda.")

st.markdown("## Como funciona")
st.markdown(
    """
    1. **Coleta automática** — após cada rodada a FGF publica as súmulas; um robô do Tchê Scout busca as novas todos os dias.
    2. **Extração e limpeza** — os PDFs são lidos e os dados são padronizados (nomes de times e atletas, minutos, cartões, substituições).
    3. **Painéis** — tudo vira tabela e gráfico, sempre com a mesma base para todo mundo.
    """
)

st.markdown("## Quem está por trás")
st.markdown(
    f"**{AUTOR}** — {AUTOR_FUNCAO}.  \n"
    f"Contato: [{WHATSAPP_EXIBIR} (WhatsApp)]({WHATSAPP_LINK})"
)
rodape()
