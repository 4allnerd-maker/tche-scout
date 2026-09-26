import streamlit as st

from config import AUTOR, AUTOR_FUNCAO, EMAIL_CONTATO, WHATSAPP_EXIBIR, WHATSAPP_LINK
from theme import cabecalho, rodape

cabecalho("📣 Parcerias e anúncios",
          "O Tchê Scout tem uma parte aberta e gratuita. Se a sua marca conversa com o futebol gaúcho, vamos conversar.")

st.markdown(
    """
    <div class="ts-hero" style="padding:1.6rem 2rem;">
      <h1 style="font-size:1.8rem;">📣 Divulgue sua marca aqui</h1>
      <p>O público do Tchê Scout acompanha o futebol do Rio Grande do Sul de perto: torcedores, analistas de
         desempenho, comissões técnicas, atletas, agentes e jornalistas. Gente que procura dado, não achismo.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2 = st.columns([3, 2])
with c1:
    st.markdown("### Fale com a gente")
    st.link_button("💬 Chamar no WhatsApp", WHATSAPP_LINK, type="primary")
    st.markdown(f"**{AUTOR}**  \n{AUTOR_FUNCAO}  \nWhatsApp: {WHATSAPP_EXIBIR}")
    if EMAIL_CONTATO:
        st.markdown(f"E-mail: [{EMAIL_CONTATO}](mailto:{EMAIL_CONTATO}?subject=Parceria%20-%20T%C3%AAch%C3%AA%20Scout)")
with c2:
    st.markdown(
        '<div class="ts-destaque"><b>Para clubes e analistas</b><br/>Em breve: versão com relatórios prontos '
        "de adversário, comparativos de atletas e recortes sob medida. Quer participar do piloto? Chame no WhatsApp."
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown("### Por que anunciar aqui")
itens = [
    ("Público segmentado", "Quem chega aqui está buscando dados dos campeonatos gaúchos — não é audiência de passagem."),
    ("Conteúdo sempre novo", "A base é atualizada automaticamente a cada rodada publicada pela FGF."),
    ("Transparência", "Todo número vem das súmulas oficiais. Patrocínio não altera nenhum dado."),
    ("Formatos flexíveis", "Faixa na página inicial, destaque em uma aba específica, patrocínio de um campeonato ou de relatórios."),
]
cols = st.columns(len(itens))
for col, (t, d) in zip(cols, itens):
    col.markdown(f'<div class="ts-card"><h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)

st.markdown("### Ideias de parceria")
st.markdown(
    """
    - **Clubes e centros de treinamento** — divulgação de peneiras, escolinhas e categorias de base.
    - **Comércio e serviços esportivos** — material esportivo, nutrição, fisioterapia, preparação física.
    - **Tecnologia e dados** — plataformas de vídeo-análise, GPS, software para comissões técnicas.
    - **Apoio livre ao projeto** — quem quiser ajudar a manter a base atualizada e aberta.
    """
)
st.caption("Valores e formatos serão definidos conforme o alcance do site — sem compromisso.")
rodape()
