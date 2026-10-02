from pathlib import Path

import streamlit as st

from config import AUTOR, AUTOR_FUNCAO
from contato import botao_contato
from theme import cabecalho, rodape

ASSETS = Path(__file__).resolve().parent.parent / "assets"

cabecalho("👤 Quem sou eu", "Por trás do Tchê Scout: a pessoa, o método e as publicações.")

st.markdown(
    f"""
    <div class="ts-hero" style="display:block; padding:1.8rem 2rem;">
      <h1 style="font-size:2.4rem; margin:0">Lucho <span>Pahim</span></h1>
      <p style="margin:.3rem 0 0 0"><b>{AUTOR_FUNCAO}</b></p>
      <p style="margin:.2rem 0 0 0">Autor do e-book <i>Jogo de Dados: Sabermetria no Futebol</i> e criador da metodologia
         <b>IEEA — Inteligência Esportiva Estratégica Aplicada</b>.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_a, col_b = st.columns([1.5, 1])
with col_a:
    st.markdown("### Sobre mim")
    st.markdown(
        """
        Sou **João Paulo Pahim Moreira**, o **Lucho Pahim**. Tenho ampla experiência na atividade de **inteligência**,
        onde atuei como **analista de dados**, e fui **atleta das categorias de base do Riograndense Futebol Clube**
        (Santa Maria/RS).

        Foi a união desses dois mundos — a disciplina de transformar dado disperso em conhecimento útil e a vivência
        de quem já esteve dentro do campo — que me levou à análise de desempenho no futebol. Acredito que o futebol
        vive um paradoxo: **nunca houve tanto dado disponível e, ao mesmo tempo, tantas decisões tomadas por
        impressão, reputação e “achismo”**.

        O **Tchê Scout** nasceu dessa ideia: como não existia um site de scout cobrindo os campeonatos gaúchos,
        transformei as súmulas oficiais da FGF em dados abertos, organizados e comparáveis — para que analistas,
        comissões técnicas, jornalistas e torcedores possam entender o futebol do Rio Grande do Sul com números.
        """
    )
with col_b:
    st.markdown(
        """
        <div class="ts-destaque">
        <b>Em uma frase</b><br/>
        Dado bruto, por si só, não é conhecimento. O trabalho do analista é transformá-lo em algo <b>útil, oportuno e
        acionável</b> para quem decide.
        </div>
        """,
        unsafe_allow_html=True,
    )
    botao_contato("💬 Falar comigo", chave="quem", type="primary", width="stretch")

st.markdown("### A metodologia IEEA")
st.markdown(
    """
    A **Inteligência Esportiva Estratégica Aplicada (IEEA)** transpõe os fundamentos da doutrina de inteligência —
    em suas versões públicas e de fonte aberta — para o ambiente do futebol profissional: o **ciclo de produção do
    conhecimento**, os princípios da atividade e a lógica do **assessoramento à decisão** encontram correspondência
    direta nas necessidades de clubes, comissões técnicas e departamentos de mercado.

    Ela se operacionaliza por meio dos três pilares do modelo **Jogo de Dados**:
    """
)
pilares = [
    ("VCA", "Valor Coletivo Agregado",
     "Cruza o desempenho individual do atleta com o desempenho agregado da equipe. Um jogador com números medianos, "
     "mas cuja presença eleva o time, vale mais do que uma estrela cujos números não viram pontos."),
    ("ETA", "Eficiência Tática Adaptativa",
     "Leitura tática que ajuda a calibrar formações e escolhas ao contexto de cada partida."),
    ("AIE", "Análise de Impacto Estratégico",
     "Une estatística contextual e produção de conhecimento para qualificar decisões técnicas e de mercado, "
     "como identificar talentos subvalorizados e reorientar políticas de contratação."),
]
cols = st.columns(3)
for c, (sigla, nome, texto) in zip(cols, pilares):
    c.markdown(f'<div class="ts-card"><div class="ico" style="font-family:Archivo Black,Inter;color:#F2B705;font-size:1.9rem">'
               f'{sigla}</div><h4>{nome}</h4><p>{texto}</p></div>', unsafe_allow_html=True)

st.markdown("### Publicações para baixar")
p1, p2 = st.columns(2)
with p1:
    with st.container(border=True):
        i1, i2 = st.columns([1, 2])
        i1.image(str(ASSETS / "capa_jogo_de_dados.png"), width="stretch")
        i2.markdown("**Jogo de Dados**  \n*Sabermetria no Futebol: a transposição do método de Bill James para o "
                    "desempenho coletivo no esporte mais popular do mundo.*  \nE-book · 32 páginas · VCA · ETA · AIE")
        arq = ASSETS / "downloads" / "Jogo-de-Dados-Ebook-Lucho-Pahim.pdf"
        if arq.exists():
            i2.download_button("⬇️ Baixar o e-book (PDF)", arq.read_bytes(), file_name=arq.name, mime="application/pdf",
                               key="dl_ebook")
with p2:
    with st.container(border=True):
        i1, i2 = st.columns([1, 2])
        i1.image(str(ASSETS / "capa_artigo_ieea.png"), width="stretch")
        i2.markdown("**Inteligência Esportiva Estratégica Aplicada — IEEA**  \n*A adaptação da doutrina de inteligência "
                    "à análise de desempenho, de mercado e de jogo no futebol.*  \nArtigo · 6 páginas")
        arq = ASSETS / "downloads" / "Artigo-IEEA-Lucho-Pahim.pdf"
        if arq.exists():
            i2.download_button("⬇️ Baixar o artigo (PDF)", arq.read_bytes(), file_name=arq.name, mime="application/pdf",
                               key="dl_artigo")

st.markdown("### Como posso ajudar")
st.markdown(
    """
    - **Relatórios de adversário e de desempenho** para comissões técnicas e departamentos de análise.
    - **Scout e análise de atletas** a partir de dados de jogo.
    - **Ferramentas de dados sob medida** para o dia a dia do clube — como o próprio Tchê Scout.
    """
)
st.info("Quer conversar sobre o seu clube ou projeto? Identifique-se e libere o contato por WhatsApp:")
botao_contato("💬 Liberar contato por WhatsApp", chave="quem2")
rodape()
