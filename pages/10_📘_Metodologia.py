import streamlit as st

import data_loader as dl
from contato import botao_contato
from theme import cabecalho, rodape

cabecalho("📘 Metodologia e limitações", "Como os números são feitos — e onde podem acontecer equívocos. Leia antes de tirar conclusões.")

if dl.tem_dados():
    m = dl.meta()
    st.caption(f"Base gerada em {m.get('gerado_em', '—')} · {m.get('jogos', 0)} jogos com resultado · {m.get('atletas', 0)} atletas.")

st.markdown(
    """
    <div class="ts-destaque">
    <b>Em resumo:</b> o Tchê Scout lê as <b>súmulas oficiais em PDF</b> da FGF e organiza os dados. Ele é tão bom quanto a súmula:
    se a súmula tem erro, o erro vem junto. Onde a súmula é <b>omissa</b> (posições, assistências, formação tática), o site
    <b>não inventa</b> — ou avisa que é uma pista, ou pede que você registre a informação.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 1. De onde vêm os dados")
st.markdown(
    """
    - **Fonte única:** súmulas oficiais publicadas pela Federação Gaúcha de Futebol (site fgf.com.br), dos campeonatos profissionais
      (Gauchão, Série A2, Série B, Copa FGF, Recopa) e do futebol feminino (Gauchão Feminino e Sub 20/17/15).
    - **Atualização:** um robô busca súmulas novas todos os dias (e a cada 4 horas nos sábados e domingos). A FGF costuma publicar
      depois de cada rodada; até lá, o jogo aparece no calendário, mas **fora das estatísticas**.
    - **Correções da FGF:** se a federação corrigir uma súmula depois, o site só reflete a correção na próxima leitura.
    """
)

st.markdown("### 2. Como a súmula vira dado")
st.markdown(
    """
    - O PDF é lido por posição das tabelas e das palavras. Existem **vários layouts** de súmula (2024, 2025, 2026, feminino);
      o leitor foi validado nos que encontramos, mas um layout novo pode causar leituras erradas até ser ajustado.
    - **Times:** nomes padronizados (por exemplo, "Brasil", "Brasil SAF" e "Grêmio Esportivo Brasil SAF" viram *Brasil de Pelotas*).
    - **Atletas:** identificados pelo **registro da CBF**. Atletas amadores sem registro são identificados por *time + nome*.
    - **Nomes:** a FGF corta nomes longos ("Fulano da Silva ..."); o site reconstrói o nome usando as outras ocorrências do atleta.
    """
)

st.markdown("### 3. Regras que mudam os números")
st.markdown(
    """
    - **W.O.:** jogo cancelado com placar 3×0 no site. Vale 3 pontos na classificação, mas **fica fora** de médias de gols e de minutagem.
      **Cancelado sem placar** não conta.
    - **Gol contra** é creditado ao adversário; **pênalti** aparece como tipo de gol (só convertidos).
    - **Cartões:** o vermelho é separado em *direto* e *por 2º amarelo*. Cartões de **comissão técnica** ficam em separado dos atletas.
    - **Minutos jogados:** estimados (90 min base; entradas, saídas e expulsões). Não são o tempo efetivo de jogo.
    - **Faixas de minuto:** 0–15, 16–30, 31–45+, 46–60, 61–75, 76–90+ (acréscimos entram na última faixa de cada tempo).
    """
)

st.markdown("### 4. O que a súmula NÃO informa (e como o site lida com isso)")
st.markdown(
    """
    | Informação | Situação no Tchê Scout |
    |---|---|
    | **Posição do atleta** | Não existe. Montamos em **camadas com fonte e confiança**: goleiro (exato, pela súmula) → inferida pela camisa (até 80%) → pesquisada em fonte aberta (com link; poucos atletas; pode confundir homônimos) → correção manual. Veja em Jogadores → 📍 Posições. |
    | **Formação tática** | Não existe. Contar camisas por zona resulta em "4-3-3" em ~81% dos jogos, por isso **não é usado como formação**. Você pode **registrar manualmente** (aba Jogo & súmula / Análise). |
    | **Assistências, finalizações, passes** | Não existem em súmula. Ficam de fora. |
    | **Pênaltis perdidos, tempo efetivo, faltas** | Não constam. |
    """
)

st.markdown("### 5. Limitações conhecidas")
st.markdown(
    """
    - **Súmulas femininas de base:** em algumas, a FGF marca poucos titulares — **minutos e "titular/reserva" desses jogos podem estar errados**.
    - **Amostras pequenas:** com poucos jogos ou gols, percentuais oscilam muito. Os painéis avisam quando a amostra é pequena.
    - **Insights automáticos** são frases geradas por regras: sempre confira os números por trás.
    - **Árbitros:** métricas descrevem o que aconteceu, não julgam a qualidade da arbitragem; depende dos jogos recebidos.
    - **Formações manuais** ficam só na sua sessão até você baixar o CSV (veja abaixo).
    """
)

st.markdown("### 6. Posições e formações: o que é da base e o que é seu")
st.markdown(
    """
    - **Posições:** parte dos atletas já tem posição incluída automaticamente (goleiros pela súmula, posição *provável* pela camisa e
      posição *confirmada* em fonte aberta, com link). Os demais aparecem como **Não confirmada** — o site não inventa. A base é
      atualizada **toda semana** e a cobertura vai melhorar com o tempo.
    - **Correção local:** ao analisar um time (Análise → Elenco, ou em Relatórios e cards), você pode ajustar posições e registrar
      formações. Isso vale **na sua visita** e entra no PDF que você gerar; ao recarregar a página, volta ao padrão da base.
      Dados digitados por pessoas **não são verificados** e podem conter equívocos.
    """
)

st.markdown("### 7. Encontrou um erro?")
st.markdown("Se um número parecer estranho, avise com o **jogo** e o **que estava errado** — a base é reprocessada e corrigida.")
botao_contato("💬 Avisar sobre um erro", chave="metod")
rodape()
