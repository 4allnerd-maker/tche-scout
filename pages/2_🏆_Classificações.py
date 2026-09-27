import plotly.graph_objects as go
import streamlit as st

import data_loader as dl
import estado
import leiame
import stats
from theme import COR, cabecalho, rodape
from ui import tabela

cabecalho("🏆 Classificações e scout dos times",
          "Tabela, perfil de cada time e em que momento do jogo os gols acontecem.")
leiame.mostrar("classificacoes")

if not dl.tem_dados():
    st.warning("Base de dados ainda não gerada.")
    st.stop()

jogos = dl.jogos()
if jogos.empty:
    st.info("Nenhum jogo com resultado na base.")
    st.stop()

estado.barra_limpar("cls")
f1, f2, f3, f4 = st.columns(4)
cats = sorted(jogos["categoria"].unique(), reverse=True)  # Masculino primeiro
categoria = f1.selectbox("Categoria", cats, key="cls_cat")
j = jogos[jogos["categoria"] == categoria]
ano = f2.selectbox("Ano", sorted(j["ano"].unique(), reverse=True), index=None, placeholder="Escolha o ano", key="cls_ano")
comps = sorted(j[j["ano"] == ano]["competicao_nome"].unique()) if ano is not None else []
competicao = f3.selectbox("Competição", comps, index=None, placeholder="Escolha a competição", key="cls_comp",
                          disabled=ano is None)
fases = sorted(j[(j["ano"] == ano) & (j["competicao_nome"] == competicao)]["fase_nome"].dropna().unique()) if competicao else []
fase = f4.selectbox("Fase", ["Todas as fases"] + fases, index=None, placeholder="1ª fase (padrão)", key="cls_fase",
                    disabled=competicao is None,
                    help="Sem escolher, mostra a 1ª fase; 'Todas as fases' soma todas (útil só para estatística).")
if ano is None or competicao is None:
    st.info("👆 Escolha o **ano** e a **competição** para ver a classificação.")
    rodape()
    st.stop()
j = j[(j["ano"] == ano) & (j["competicao_nome"] == competicao)]
fase_uso = fase if fase is not None else (fases[0] if fases else "Todas as fases")
if fase_uso != "Todas as fases":
    j = j[j["fase_nome"] == fase_uso]

st.caption(f"{len(j)} jogos nesta seleção · {competicao} {ano} · {fase_uso}")

gols_df, cartoes_df = dl.gols(), dl.cartoes()
tab_class, tab_perfil, tab_minutos, tab_art = st.tabs(
    ["Classificação", "Perfil dos times", "Gols por minuto", "Artilharia"])

with tab_class:
    classif = stats.classificacao(j)
    tabela_class = tabela(classif, "cls", ordenar_por="Pos", crescente=True, fixar="Time", exportar="tche-scout-classificacao",
                          ajuda={"P": "Pontos", "J": "Jogos", "V": "Vitórias", "E": "Empates", "D": "Derrotas", "GP": "Gols pró",
                                 "GC": "Gols contra", "SG": "Saldo de gols", "%": "Aproveitamento (%)",
                                 "WO": "Jogos decididos por W.O. (3x0)"})
    if "WO" in classif and classif["WO"].sum():
        st.caption("Critérios de ordenação: pontos, vitórias, saldo de gols e gols pró. "
                   "A coluna W.O. mostra jogos decididos por ausência do adversário.")

with tab_perfil:
    perfil = stats.perfil_times(j, cartoes_df, gols_df)
    if perfil.empty:
        st.info("Sem jogos disputados (com súmula) nesta seleção.")
    else:
        cols = ["Time", "J", "Gols pró/jogo", "Gols contra/jogo", "Pró/jogo (casa)", "Pró/jogo (fora)",
                "Contra/jogo (casa)", "Contra/jogo (fora)", "Min/gol feito", "Min/gol sofrido",
                "Jogos s/ sofrer", "Jogos s/ marcar", "Amarelos", "Vermelhos", "Amarelos/jogo"]
        tabela(perfil[[c for c in cols if c in perfil]], "perfil", ordenar_por="Gols pró/jogo", fixar="Time",
               exportar="tche-scout-perfil-times")
        st.caption("Médias calculadas só sobre jogos com súmula (W.O. não entra). "
                   "‘Min/gol’ = minutos de jogo (90 × jogos) por gol.")
        fig = go.Figure()
        ordem = perfil.sort_values("Gols pró/jogo")
        fig.add_bar(y=ordem["Time"], x=ordem["Gols pró/jogo"], name="Gols pró/jogo", orientation="h",
                    marker_color=COR["verde"])
        fig.add_bar(y=ordem["Time"], x=ordem["Gols contra/jogo"], name="Gols contra/jogo", orientation="h",
                    marker_color=COR["vermelho"])
        fig.update_layout(barmode="group", height=max(320, 34 * len(ordem)), margin=dict(l=0, r=0, t=10, b=0),
                          legend=dict(orientation="h", y=1.05), plot_bgcolor="white")
        st.plotly_chart(fig, width="stretch")

with tab_minutos:
    times = sorted(set(j["time_mandante"]) | set(j["time_visitante"]))
    alvo = st.selectbox("Time", ["Todos os times (campeonato)"] + times, key="cls_time")
    time = None if alvo.startswith("Todos") else alvo
    dist = stats.gols_por_faixa(gols_df, j, time)
    fig = go.Figure()
    fig.add_bar(x=dist["Faixa"], y=dist["Feitos"], name="Gols feitos" if time else "Gols", marker_color=COR["verde"])
    if time:
        fig.add_bar(x=dist["Faixa"], y=dist["Sofridos"], name="Gols sofridos", marker_color=COR["vermelho"])
    fig.update_layout(barmode="group", height=380, margin=dict(l=0, r=0, t=10, b=0),
                      xaxis_title="Minuto do jogo", yaxis_title="Gols", plot_bgcolor="white",
                      legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fig, width="stretch")
    tabela(dist, "faixas", ordenar_por="Faixa", crescente=True, com_controles=False)
    st.caption("Gols contra são creditados ao adversário. Acréscimos entram na última faixa de cada tempo.")

with tab_art:
    p = dl.partidas()
    p = p[p["jogo_id"].isin(set(j["jogo_id"]))]
    art = stats.artilharia(p, 30)
    if art.empty:
        st.info("Ainda não há gols nesta seleção.")
    else:
        art.insert(0, "Pos", range(1, len(art) + 1))
        tabela(art, "art", ordenar_por="Pos", crescente=True, fixar="Atleta")

rodape()
