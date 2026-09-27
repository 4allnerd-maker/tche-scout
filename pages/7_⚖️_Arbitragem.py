import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import arbitragem as ab
import data_loader as dl
import escudos as es
import estado
import leiame
from theme import COR, cabecalho, rodape
from ui import tabela

cabecalho("⚖️ Arbitragem", "Como cada árbitro conduz os jogos: disciplina, pênaltis, acréscimos e equilíbrio entre mandante e visitante.")
leiame.mostrar("arbitragem")

if not dl.tem_dados():
    st.warning("Base de dados ainda não gerada.")
    st.stop()

jogos_all = dl.jogos()
if "arbitro" not in jogos_all or jogos_all["arbitro"].dropna().empty:
    st.info("Os dados de arbitragem ainda estão sendo gerados. Volte em alguns minutos.")
    st.stop()
gols_all, cartoes_all = dl.gols(), dl.cartoes()


def estilo(fig, altura=360, legenda=True):
    fig.update_layout(height=altura, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="Inter, sans-serif", color=COR["texto"]), showlegend=legenda,
                      legend=dict(orientation="h", y=1.12, x=0))
    fig.update_yaxes(gridcolor="#E6ECE7", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


estado.barra_limpar("ar")
with st.container(border=True):
    f1, f2, f3, f4 = st.columns([1, 1.2, 2, 1.3])
    cats = sorted(jogos_all["categoria"].unique(), reverse=True)
    categoria = f1.selectbox("Categoria", cats, key="ar_cat")
    j = jogos_all[jogos_all["categoria"] == categoria]
    anos_disp = sorted(j["ano"].unique(), reverse=True)
    anos = f2.multiselect("Ano", anos_disp, placeholder="Todos os anos", key="ar_ano")
    j = j[j["ano"].isin(anos)] if anos else j
    comps_disp = sorted(j["competicao_nome"].unique())
    comps = f3.multiselect("Competição", comps_disp, placeholder="Todas", key="ar_comp")
    j = j[j["competicao_nome"].isin(comps)] if comps else j
    minimo = f4.slider("Mínimo de jogos apitados", 1, 15, 3, key="ar_min")

base = ab.base_por_jogo(j, cartoes_all, gols_all)
if base.empty:
    st.info("Nenhum jogo com dados de arbitragem nessa seleção.")
    st.stop()
tab = ab.tabela_arbitros(base, minimo)
if tab.empty:
    st.info(f"Nenhum árbitro com pelo menos {minimo} jogos nessa seleção. Reduza o mínimo de jogos.")
    st.stop()

k = st.columns(5)
k[0].metric("Árbitros", base["arbitro"].nunique())
k[1].metric("Jogos", len(base))
k[2].metric("Amarelos por jogo", f"{base['amarelos'].mean():.2f}")
k[3].metric("Vermelhos por jogo", f"{base['vermelhos'].mean():.2f}")
k[4].metric("Acréscimo médio 2º tempo", f"{base['acrescimo_2t'].mean():.1f} min" if base["acrescimo_2t"].notna().any() else "—")

tabs = st.tabs(["📌 Insights & ranking", "🧑‍⚖️ Ficha do árbitro", "🚩 Equipes de arbitragem", "⏱️ Cartões por minuto"])

with tabs[0]:
    st.markdown("#### Insights automáticos")
    for t in ab.insights_arbitragem(base, tab):
        st.markdown(f"- {t}")
    st.caption("Amostras pequenas variam muito: sempre olhe a coluna Jogos antes de tirar conclusões.")
    st.markdown("#### Cartões por jogo — ranking")
    top = tab.sort_values("Cartões/jogo", ascending=True).tail(20)
    media = (base["amarelos"].sum() + base["vermelhos"].sum()) / len(base)
    fig = go.Figure()
    fig.add_bar(y=top["Árbitro"], x=top["Amarelos/jogo"], orientation="h", name="Amarelos", marker_color=COR["dourado"])
    fig.add_bar(y=top["Árbitro"], x=top["Vermelhos/jogo"], orientation="h", name="Vermelhos", marker_color=COR["vermelho"])
    fig.add_vline(x=media, line_dash="dot", line_color="#5B6B62", annotation_text=f"média {media:.2f}")
    fig.update_layout(barmode="stack", xaxis_title="Cartões por jogo")
    st.plotly_chart(estilo(fig, max(320, 26 * len(top))), width="stretch")
    st.markdown("#### Tabela completa")
    tabela(tab, "arb_tab", ordenar_por="Jogos", fixar="Árbitro", exportar="tche-scout-arbitros",
           ajuda={"Pênaltis conv./jogo": "Gols de pênalti por jogo (a súmula só registra os convertidos)",
                  "Acréscimo 1ºT (min)": "Acréscimo indicado pela arbitragem, média",
                  "Vitória mandante (%)": "% de jogos com vitória do mandante"})

with tabs[1]:
    nomes = list(tab.sort_values("Jogos", ascending=False)["Árbitro"])
    arb = st.selectbox("Árbitro", nomes, key="ar_sel")
    mine = base[base["arbitro"] == arb].sort_values("data")
    linha = tab[tab["Árbitro"] == arb].iloc[0]
    st.markdown(f"### {arb}  <small style='color:#5B6B62'>· {linha['Vínculo'] or 'vínculo n/d'}</small>", unsafe_allow_html=True)
    ma = st.columns(6)
    ma[0].metric("Jogos", int(linha["Jogos"]))
    ma[1].metric("Amarelos/jogo", linha["Amarelos/jogo"], f"{linha['Amarelos/jogo'] - base['amarelos'].mean():+.2f} vs média",
                 delta_color="off")
    ma[2].metric("Vermelhos/jogo", linha["Vermelhos/jogo"], f"{linha['Vermelhos/jogo'] - base['vermelhos'].mean():+.2f} vs média",
                 delta_color="off")
    ma[3].metric("Pênaltis conv./jogo", linha["Pênaltis conv./jogo"])
    ma[4].metric("Acréscimo 2ºT", f"{linha['Acréscimo 2ºT (min)']} min" if pd.notna(linha["Acréscimo 2ºT (min)"]) else "—")
    ma[5].metric("Vitória mandante", f"{linha['Vitória mandante (%)']:.0f}%")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Amarelos: mandante × visitante")
        fig = go.Figure(go.Bar(x=["Mandante", "Visitante"], y=[linha["Amarelos mandante/jogo"], linha["Amarelos visitante/jogo"]],
                               marker_color=[COR["verde"], COR["vermelho"]], text=[linha["Amarelos mandante/jogo"],
                                                                                    linha["Amarelos visitante/jogo"]],
                               textposition="outside"))
        fig.add_hline(y=base["amarelos_mandante"].mean(), line_dash="dot", line_color=COR["verde"])
        fig.add_hline(y=base["amarelos_visitante"].mean(), line_dash="dot", line_color=COR["vermelho"])
        st.plotly_chart(estilo(fig, 300, False), width="stretch")
        st.caption("Linhas pontilhadas = média da seleção para mandante e visitante.")
    with c2:
        st.markdown("#### Cartões por faixa de minuto")
        cf = ab.cartoes_por_faixa(cartoes_all, set(mine["jogo_id"]))
        fig = go.Figure()
        fig.add_bar(x=cf["Faixa"], y=cf["Amarelos"], name="Amarelos", marker_color=COR["dourado"])
        fig.add_bar(x=cf["Faixa"], y=cf["Vermelhos"], name="Vermelhos", marker_color=COR["vermelho"])
        fig.update_layout(barmode="stack")
        st.plotly_chart(estilo(fig, 300), width="stretch")
    st.markdown("#### Times mais advertidos por este árbitro")
    c_arb = cartoes_all[cartoes_all["jogo_id"].isin(set(mine["jogo_id"]))]
    tm = c_arb.groupby("equipe").agg(Amarelos=("tipo", lambda s: (s == "amarelo").sum()),
                                     Vermelhos=("tipo", lambda s: (s == "vermelho").sum()),
                                     Jogos=("jogo_id", "nunique")).reset_index().rename(columns={"equipe": "Time"})
    tm_v = es.inserir_coluna(tm, "Time")
    tabela(tm_v, "arb_times", ordenar_por="Amarelos", altura=260, imagem_col="Escudo")
    st.markdown("#### Jogos apitados")
    jj = mine[["data", "competicao_nome", "rodada", "time_mandante", "gols_mandante", "gols_visitante", "time_visitante",
               "amarelos", "vermelhos", "penaltis_convertidos", "acrescimo_1t", "acrescimo_2t", "sumula_url"]].rename(columns={
        "data": "Data", "competicao_nome": "Competição", "rodada": "Rodada", "time_mandante": "Mandante", "gols_mandante": "GM",
        "gols_visitante": "GV", "time_visitante": "Visitante", "amarelos": "Amarelos", "vermelhos": "Vermelhos",
        "penaltis_convertidos": "Pên. conv.", "acrescimo_1t": "Acr. 1ºT", "acrescimo_2t": "Acr. 2ºT", "sumula_url": "Súmula"})
    jj = es.inserir_coluna(jj, "Mandante", "Esc. M")
    jj = es.inserir_coluna(jj, "Visitante", "Esc. V")
    st.dataframe(jj.sort_values("Data", ascending=False), hide_index=True, width="stretch", height=340,
                 column_config={"Súmula": st.column_config.LinkColumn("Súmula", display_text="PDF"),
                                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                                "Esc. M": st.column_config.ImageColumn(" ", width="small"),
                                "Esc. V": st.column_config.ImageColumn(" ", width="small")})

with tabs[2]:
    eq = ab.equipes_de_arbitragem(base)
    funcoes = ["Todas"] + sorted(eq["Função"].unique()) if not eq.empty else ["Todas"]
    fsel = st.selectbox("Função", funcoes, key="ar_func")
    e2 = eq if fsel == "Todas" else eq[eq["Função"] == fsel]
    tabela(e2, "arb_eq", ordenar_por="Jogos", altura=420, exportar="tche-scout-equipes-arbitragem")

with tabs[3]:
    cf = ab.cartoes_por_faixa(cartoes_all, set(base["jogo_id"]))
    fig = go.Figure()
    fig.add_bar(x=cf["Faixa"], y=cf["Amarelos"], name="Amarelos", marker_color=COR["dourado"])
    fig.add_bar(x=cf["Faixa"], y=cf["Vermelhos"], name="Vermelhos", marker_color=COR["vermelho"])
    fig.update_layout(barmode="stack", xaxis_title="Minuto do jogo", yaxis_title="Cartões")
    st.plotly_chart(estilo(fig, 360), width="stretch")
    tot = cf["Amarelos"].sum() + cf["Vermelhos"].sum()
    if tot:
        ult = (cf.loc[cf["Faixa"].isin(["61-75", "76-90+"]), ["Amarelos", "Vermelhos"]].sum().sum()) / tot * 100
        st.caption(f"{ult:.0f}% dos cartões saem depois dos 60 minutos.")

rodape()
