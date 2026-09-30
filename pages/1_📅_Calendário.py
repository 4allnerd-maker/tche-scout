import pandas as pd
import streamlit as st

import data_loader as dl
import escudos as es
import estado
import fases
import leiame
from theme import cabecalho, rodape
from ui import abrir_jogo, linha_selecionada, tabela

cabecalho("📅 Calendário", "Resultados e próximos jogos dos campeonatos gaúchos.")
leiame.mostrar("calendario")

if not dl.tem_dados():
    st.warning("Base de dados ainda não gerada.")
    st.stop()

cal = dl.calendario()
if cal.empty:
    st.info("Nenhum jogo na base.")
    st.stop()

estado.barra_limpar("cal")
f1, f2, f3, f4 = st.columns(4)
categoria = f1.selectbox("Categoria", ["Todas"] + sorted(cal["categoria"].unique()), key="cal_cat")
base = cal if categoria == "Todas" else cal[cal["categoria"] == categoria]
anos = sorted(base["ano"].unique(), reverse=True)
ano = f2.selectbox("Ano", ["Todos"] + anos, key="cal_ano")
if ano != "Todos":
    base = base[base["ano"] == ano]
competicao = f3.multiselect("Competição", sorted(base["competicao_nome"].unique()),
                            placeholder="Todas as competições", key="cal_comp")
if competicao:
    base = base[base["competicao_nome"].isin(competicao)]
times = sorted(set(base["time_mandante"].dropna()) | set(base["time_visitante"].dropna()))
time = f4.selectbox("Time", ["Todos"] + times, key="cal_time")
if time != "Todos":
    base = base[(base["time_mandante"] == time) | (base["time_visitante"] == time)]

fases_disp = sorted(base["fase_nome"].dropna().unique())
fase_sel = st.multiselect("Fase", fases_disp, placeholder="Todas as fases (classificatória + mata-mata)",
                          key="cal_fase",
                          help="Filtre por uma fase específica pra ver só o mata-mata (quartas, semifinal etc.).")
if fase_sel:
    base = base[base["fase_nome"].isin(fase_sel)]

if base["fase_nome"].dropna().apply(fases.eh_mata_mata).any():
    st.info("🏆 Essa seleção inclui jogos de **mata-mata** (ida e volta) — quem avança é definido pelo "
            "regulamento da FGF (normalmente: mais gols no total dos dois jogos).")

def _rotulo_confronto(df: pd.DataFrame) -> pd.Series:
    """'Ida'/'Volta' (ou 'Jogo N') pra times que se enfrentam mais de uma vez na mesma fase de mata-mata."""
    if df.empty:
        return pd.Series(dtype=str)
    par = df.apply(lambda r: tuple(sorted([str(r["time_mandante"]), str(r["time_visitante"])])), axis=1)
    grupo = list(zip(df["competicao_nome"], df["ano"], df["fase_nome"], par))
    ordenado = df.assign(_grupo=grupo).sort_values("data")
    ordem = ordenado.groupby("_grupo").cumcount() + 1
    total = ordenado.groupby("_grupo")["_grupo"].transform("count")
    eh_mm = ordenado["fase_nome"].apply(fases.eh_mata_mata)
    rot = [("Ida" if o == 1 else "Volta") if (mm and t == 2) else (f"Jogo {o}" if (mm and t > 2) else "")
          for o, t, mm in zip(ordem, total, eh_mm)]
    return pd.Series(rot, index=ordenado.index).reindex(df.index)


base = base.assign(confronto=_rotulo_confronto(base))

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
        v["Data"] = v["data"]  # datetime: ordena de verdade (o formato dd/mm/aaaa vem da coluna)
        out = v[["Data", "competicao_nome", "fase_nome", "confronto", "rodada", "time_mandante", "Placar",
                 "time_visitante", "estadio", "Obs.", "jogo_id"]]
        out.columns = ["Data", "Competição", "Fase", "Confronto", "Rodada", "Mandante", "Placar", "Visitante",
                      "Estádio", "Obs.", "jogo_id"]
        out = es.inserir_coluna(out, "Mandante", "Esc. M")
        out = es.inserir_coluna(out, "Visitante", "Esc. V")
        tabela(out, "cal_res", ordenar_por="Data", exportar="tche-scout-resultados", selecionavel=True,
               ocultar=["jogo_id"], imagem_col=["Esc. M", "Esc. V"])
        sel = linha_selecionada("cal_res")
        ok = sel is not None and str(sel["jogo_id"]).isdigit()
        b1, b2 = st.columns([1, 3])
        if b1.button("🔎 Analisar o jogo selecionado", disabled=not ok, type="primary", key="cal_analisar"):
            abrir_jogo(sel["jogo_id"])
        b2.caption("Clique numa linha da tabela para selecioná-la — a análise abre a súmula com linha do tempo e numeração. "
                   "Jogos W.O./cancelados não têm súmula.")
        st.caption("W.O.: o adversário não compareceu e o time presente recebe a vitória por 3 a 0 (conta na classificação).")

with tab_prox:
    if proximos.empty:
        st.info("Nenhum jogo agendado para essa seleção.")
    else:
        p = proximos.sort_values("data").copy()
        p["Data"] = p["data"]
        out = p[["Data", "hora", "competicao_nome", "fase_nome", "confronto", "time_mandante", "time_visitante",
                 "estadio"]]
        out.columns = ["Data", "Hora", "Competição", "Fase", "Confronto", "Mandante", "Visitante", "Estádio"]
        out = es.inserir_coluna(out, "Mandante", "Esc. M")
        out = es.inserir_coluna(out, "Visitante", "Esc. V")
        tabela(out, "cal_prox", ordenar_por="Data", crescente=True, imagem_col=["Esc. M", "Esc. V"])

rodape()
