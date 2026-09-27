"""Avisos 'Leia-me' de cada página: explicam a lógica dos números e onde podem acontecer equívocos."""

from __future__ import annotations

import streamlit as st

TITULO = "ℹ️ Leia-me: como interpretar esta página (e onde pode haver erro)"

TEXTOS = {
    "calendario": """
**Lógica.** Os jogos vêm do site da FGF. *Resultados* traz jogos já disputados; *Próximos jogos*, os agendados.

**Atenção**
- **W.O.**: jogo cancelado que aparece com placar 3×0 no site (um time não compareceu). Conta 3 pontos na classificação, mas **não entra** em médias de gols nem de minutagem.
- **Cancelado** (sem placar) não conta nada. **Sem súmula** = jogo realizado cuja súmula ainda não foi publicada ou não foi encontrada.
- Datas, horários e estádios mudam com frequência: o calendário reflete o que a FGF publicava na última atualização.
- Para abrir uma súmula: clique numa linha da tabela e use **🔎 Analisar**.
""",
    "classificacoes": """
**Lógica.** A tabela soma os jogos da seleção (competição, ano e fase). Critério de ordenação: pontos, vitórias, saldo e gols pró.

**Atenção**
- **Não é a tabela oficial:** confrontos diretos, disputa de pontos no tribunal e regulamentos específicos não são aplicados.
- Por padrão, mostra a **1ª fase** de cada competição; escolha "Todas" para somar todas as fases (útil só para estatística).
- *Gols por minuto*: gols contra são creditados ao adversário; acréscimos entram na última faixa de cada tempo.
- Artilharia conta gols de jogo (não inclui disputa de pênaltis) e **não há assistências** — a súmula não as registra.
""",
    "jogadores": """
**Lógica.** Cada atleta é identificado pelo **registro da CBF** que consta na súmula. Os nomes são padronizados (caixa, cortes com "...").

**Atenção**
- **Amadores sem registro CBF** são identificados por *time + nome*: podem aparecer separados se mudarem de clube ou de grafia.
- **Minutos jogados** são estimados (base de 90 min): titular joga do início, reserva a partir da substituição, expulsão encerra a participação. Não usa o tempo real de jogo nem acréscimos.
- Em algumas súmulas **femininas de base** a FGF marca poucos titulares; os minutos desses jogos podem estar errados.
- Nomes completos podem vir **cortados** pela própria FGF; "Apelido" é como o atleta é chamado na súmula (pode repetir entre atletas).
- **Posição do atleta NÃO vem da súmula.** Parte dos atletas já tem posição (goleiro exato pela súmula, *provável* pela camisa ou confirmada em fonte aberta); os demais aparecem como **Não confirmada**. A base é atualizada toda semana e vai melhorando.
- **Camisas**: a numeração segue a convenção brasileira (1 goleiro, 9 centroavante…), mas **não é posição** — é uma pista.
""",
    "analise": """
**Lógica.** Todas as métricas usam apenas os jogos **com súmula** dentro dos filtros. A "média do campeonato" é calculada sobre os times da mesma seleção.

**Atenção**
- **Amostra pequena:** com poucos jogos ou gols, percentuais oscilam muito (o painel avisa abaixo de 5 jogos; abaixo de ~10 gols, evite conclusões sobre minutagem).
- **Insights automáticos** são frases geradas por regras — confira sempre os números que as sustentam.
- **Quem abre o placar** usa o minuto registrado pela arbitragem; gols sem minuto ficam de fora dessa análise.
- **Continuidade do onze** compara os titulares de cada jogo com o jogo anterior *do recorte escolhido*.
- **Formação tática não vem da súmula.** Só aparece aqui se você a registrar manualmente (aba 🧩 Formações).
""",
    "jogo": """
**Lógica.** A súmula é lida do PDF oficial; a linha do tempo junta gols, cartões e substituições pelo minuto registrado.

**Atenção**
- **O campo tático NÃO é a formação real.** Ele posiciona os titulares pela **numeração de camisa** (convenção brasileira). Com camisas tradicionais o resultado é quase sempre "4-3-3", seja qual for o desenho do time. O selo *Padrão de numeração* mostra o quanto a escalação segue a convenção.
- Se o time usa números fora do padrão (ex.: titulares com camisas 13, 22, 30), a leitura fica **menos confiável**.
- Gols/cartões sem minuto registrado aparecem no fim da linha do tempo.
- Para a formação de verdade, use a aba **🧩 Formação (manual)**.
""",
    "arbitragem": """
**Lógica.** Cada jogo tem seu árbitro na súmula. As métricas são médias por jogo apitado dentro da seleção de filtros.

**Atenção**
- **Descrição, não julgamento.** Rigor de um árbitro depende dos jogos que recebeu (clássicos, rodadas decisivas, times mais faltosos).
- **Amostras pequenas** variam muito: use o filtro de mínimo de jogos e olhe a coluna *Jogos*.
- **Pênaltis:** só entram os *convertidos* (a súmula não registra pênaltis perdidos ou defendidos).
- **Acréscimos** são os indicados pela arbitragem, não o tempo realmente jogado.
- Nomes de árbitros podem variar de grafia entre súmulas; quando possível, foram padronizados.
""",
    "relatorios": """
**Lógica.** Os cards e o PDF usam exatamente os mesmos números das abas de Classificações e Análise.

**Atenção**
- Confira o resultado antes de publicar: dados vêm de súmulas, que podem ter erros de digitação ou ser corrigidas depois.
- **Rodada** vem da súmula; competições com fases eliminatórias não têm rodada numerada.
- As legendas sugeridas são um ponto de partida — revise antes de postar.
- Os relatórios são de **estatística de desempenho**, sem finalidade de apostas.
""",
}


def mostrar(chave: str) -> None:
    texto = TEXTOS.get(chave)
    if texto:
        with st.expander(TITULO):
            st.markdown(texto)
            st.caption("Encontrou algo estranho? Avise pelo WhatsApp da aba **Quem sou eu** — a base é reprocessada e corrigida.")
