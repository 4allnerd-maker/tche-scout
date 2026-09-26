import pandas as pd
import streamlit as st

import data_loader as dl
from theme import cabecalho, rodape

cabecalho("📅 Calendário", "Resultados e próximos jogos dos campeonatos gaúchos.")

if not dl.tem_dados():
    st.warning("Base de dados ainda não gerada.")
    st.stop()

cal = dl.calendario()
if cal.empty:
    st.info("Nenhum jogo na base.")
    st.stop()

f1, f2, f3, f4 = st.columns(4)
categoria = f1.selectbox("Categoria", ["Todas"] + sorted(cal["categoria"].unique()))
base = cal if categoria == "Todas" else cal[cal["categoria"] == categoria]
anos = sorted(base["ano"].unique(), reverse=True)
ano = f2.selectbox("Ano", anos)
base = base[base["ano"] == ano]
competicao = f3.multiselect("Competição", sorted(base["competicao_nome"].unique()),
                            placeholder="Todas as competições")
if competicao:
    base = base[base["competicao_nome"].isin(competicao)]
times = sorted(set(base["time_mandante"].dropna()) | set(base["time_visitante"].dropna()))
time = f4.selectbox("Time", ["Todos"] + times)
if time != "Todos":
    base = base[(base["time_mandante"] == time) | (base["time_visitante"] == time)]

HOJE = pd.Timestamp.today().normalize()
jogados = base[base["situacao"].isin(["Realizado", "W.O.", "Realizado (sem súmula)"])]
proximos = base[base["situacao"] == "A realizar"]
outros = base[base["situacao"] == "Cancelado"]

tab_res, tab_prox = st.tabs([f"Resultados ({len(jogados) + len(outros)})", f"Próximos jogos ({len(proximos)})"])

with tab_res:
    v = pd.concat([jogados, outros]).sort_values("data", ascending=False)
    if v.empty:
        st.info("Nenhum resultado para essa seleção.")
    else:
        v = v.copy()
        v["Placar"] = v.apply(
            lambda r: "—" if pd.isna(r["gols_mandante"]) else f"{int(r['gols_mandante'])} x {int(r['gols_visitante'])}", axis=1)
        v["Obs."] = v["situacao"].map({"W.O.": "W.O. (3x0)", "Cancelado": "Cancelado",
                                        "Realizado (sem súmula)": "Sem súmula"}).fillna("")
        v["Data"] = v["data"].dt.strftime("%d/%m/%Y")
        out = v[["Data", "competicao_nome", "fase_nome", "rodada", "time_mandante", "Placar", "time_visitante",
                 "estadio", "Obs."]]
        out.columns = ["Data", "Competição", "Fase", "Rodada", "Mandante", "Placar", "Visitante", "Estádio", "Obs."]
        st.dataframe(out, hide_index=True, width="stretch")
        st.caption("W.O.: o adversário não compareceu e o time presente recebe a vitória por 3 a 0 (conta na classificação).")

with tab_prox:
    if proximos.empty:
        st.info("Nenhum jogo agendado para essa seleção.")
    else:
        p = proximos.sort_values("data").copy()
        p["Data"] = p["data"].dt.strftime("%d/%m/%Y").fillna("A definir")
        out = p[["Data", "hora", "competicao_nome", "fase_nome", "time_mandante", "time_visitante", "estadio"]]
        out.columns = ["Data", "Hora", "Competição", "Fase", "Mandante", "Visitante", "Estádio"]
        st.dataframe(out, hide_index=True, width="stretch")

rodape()
