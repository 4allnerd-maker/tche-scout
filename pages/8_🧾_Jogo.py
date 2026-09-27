import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import camisas as cm
import campo
import data_loader as dl
from theme import COR, cabecalho, rodape
from ui import tabela

cabecalho("🧾 Jogo & súmula", "A súmula de uma partida, aberta e explicada: linha do tempo, escalações por numeração e arbitragem.")

if not dl.tem_dados():
    st.warning("Base de dados ainda não gerada.")
    st.stop()

jogos_all = dl.jogos()
real = jogos_all[jogos_all["situacao"] == "Realizado"]
partidas_all, gols_all, cartoes_all, subs_all = dl.partidas(), dl.gols(), dl.cartoes(), dl.substituicoes()

# ------------------------------------------------------------------ seleção do jogo
pedido = st.session_state.get("jogo_id")
if pedido and (real["jogo_id"] == pedido).any():
    padrao = real[real["jogo_id"] == pedido].iloc[0]
else:  # sem jogo pedido: o mais recente da base masculina
    recentes = real[real["categoria"] == "Masculino"].sort_values(["data", "jogo_id"])
    padrao = recentes.iloc[-1] if len(recentes) else None
    pedido = padrao["jogo_id"] if padrao is not None else None

with st.container(border=True):
    f1, f2, f3, f4 = st.columns([1, 1, 2, 2])
    cats = sorted(real["categoria"].unique(), reverse=True)
    cat0 = cats.index(padrao["categoria"]) if padrao is not None else 0
    categoria = f1.selectbox("Categoria", cats, index=cat0, key="jg_cat")
    j = real[real["categoria"] == categoria]
    anos = sorted(j["ano"].unique(), reverse=True)
    ano0 = anos.index(padrao["ano"]) if padrao is not None and padrao["ano"] in anos else 0
    ano = f2.selectbox("Ano", anos, index=ano0, key="jg_ano")
    j = j[j["ano"] == ano]
    comps = sorted(j["competicao_nome"].unique())
    comp0 = comps.index(padrao["competicao_nome"]) if padrao is not None and padrao["competicao_nome"] in comps else 0
    comp = f3.selectbox("Competição", comps, index=comp0, key="jg_comp")
    j = j[j["competicao_nome"] == comp]
    times = ["Todos"] + sorted(set(j["time_mandante"]) | set(j["time_visitante"]))
    time = f4.selectbox("Time (opcional)", times, key="jg_time")
    if time != "Todos":
        j = j[(j["time_mandante"] == time) | (j["time_visitante"] == time)]

    j = j.sort_values(["data", "jogo_id"], ascending=False)
    rotulos = {r.jogo_id: f"{r.data:%d/%m/%Y} · {r.time_mandante} {int(r.gols_mandante)} x {int(r.gols_visitante)} "
                          f"{r.time_visitante}" + (f" · R{r.rodada}" if pd.notna(r.rodada) else "")
               for r in j.itertuples()}
    ids = list(rotulos)
    if not ids:
        st.info("Nenhum jogo nessa seleção.")
        st.stop()
    idx0 = ids.index(pedido) if pedido in ids else 0
    jogo_id = st.selectbox("Jogo", ids, index=idx0, format_func=lambda i: rotulos[i], key="jg_jogo")
st.session_state["jogo_id"] = jogo_id

r = real[real["jogo_id"] == jogo_id].iloc[0]
mand, visit = r["time_mandante"], r["time_visitante"]
pj = partidas_all[partidas_all["jogo_id"] == jogo_id].rename(columns={"categoria": "vinculo"})
g = gols_all[gols_all["jogo_id"] == jogo_id]
c = cartoes_all[cartoes_all["jogo_id"] == jogo_id]
s_ = subs_all[subs_all["jogo_id"] == jogo_id]

# ------------------------------------------------------------------ placar
ht = f"{int(r['gols_1t_mandante'])} x {int(r['gols_1t_visitante'])}" if pd.notna(r["gols_1t_mandante"]) else "—"
st.markdown(
    f"""
    <div class="ts-hero" style="display:block; padding:1.4rem 1.8rem; text-align:center;">
      <div style="font-size:.95rem; opacity:.9">{html.escape(str(r['competicao_nome']))} · {html.escape(str(r['fase_nome']))}
        {'· Rodada ' + str(r['rodada']) if pd.notna(r['rodada']) else ''}</div>
      <div style="display:flex; align-items:center; justify-content:center; gap:1.4rem; margin:.5rem 0;">
        <div style="flex:1; text-align:right; font-family:'Archivo Black',Inter; font-size:1.7rem">{html.escape(mand)}</div>
        <div style="font-family:'Archivo Black',Inter; font-size:3rem; color:#F2B705; white-space:nowrap">
          {int(r['gols_mandante'])} <span style="font-size:1.6rem">x</span> {int(r['gols_visitante'])}</div>
        <div style="flex:1; text-align:left; font-family:'Archivo Black',Inter; font-size:1.7rem">{html.escape(visit)}</div>
      </div>
      <div style="font-size:.95rem; opacity:.9">{r['data']:%d/%m/%Y} · {r['hora'] or ''} · {html.escape(str(r['estadio'] or ''))}
        · intervalo {ht}</div>
    </div>
    """,
    unsafe_allow_html=True)
b1, b2, _ = st.columns([1, 1, 3])
if isinstance(r.get("sumula_url"), str) and r["sumula_url"]:
    b1.link_button("📄 Abrir súmula oficial (PDF)", r["sumula_url"], width="stretch")
b2.caption(f"Código do jogo: {jogo_id}")

tabs = st.tabs(["⏱️ Linha do tempo", "👕 Escalações por numeração", "📊 Comparativo", "⚖️ Arbitragem"])

# ------------------------------------------------------------------ linha do tempo
with tabs[0]:
    ev = []
    for x in g.itertuples():
        lado = x.equipe_creditada
        tipo = "Gol contra" if x.contra else {"PN": "Gol de pênalti", "FT": "Gol de falta"}.get(x.tipo, "Gol")
        ev.append({"Min": x.minuto, "Time": lado, "Evento": f"⚽ {tipo}", "Atleta": x.jogador, "Detalhe": "", "icone": "⚽"})
    for x in c.itertuples():
        det = (x.detalhe or "") if isinstance(getattr(x, "detalhe", None), str) else ""
        ev.append({"Min": x.minuto, "Time": x.equipe, "Evento": "🟥 Vermelho" if x.tipo == "vermelho" else "🟨 Amarelo",
                   "Atleta": x.jogador + (" (comissão)" if getattr(x, "comissao", False) else ""),
                   "Detalhe": (det + " · " if det else "") + (x.motivo or "")[:110], "icone": "🟥" if x.tipo == "vermelho" else "🟨"})
    for x in s_.itertuples():
        ev.append({"Min": x.minuto, "Time": x.equipe, "Evento": "🔁 Substituição", "Atleta": f"Entra {x.entrou}",
                   "Detalhe": f"Sai {x.saiu}", "icone": "🔁"})
    if not ev:
        st.info("Sem eventos registrados.")
    else:
        e = pd.DataFrame(ev).sort_values("Min", na_position="last").reset_index(drop=True)
        fig = go.Figure()
        for lado, y in ((mand, 1), (visit, 0)):
            x = e[e["Time"] == lado]
            fig.add_trace(go.Scatter(x=x["Min"], y=[y] * len(x), mode="text", text=x["icone"], textfont=dict(size=22),
                                     name=lado, hovertext=x["Evento"] + " · " + x["Atleta"], hoverinfo="text"))
        fig.add_vline(x=45, line_dash="dot", line_color="#9AA9A0")
        fig.update_yaxes(tickvals=[1, 0], ticktext=[mand, visit], range=[-.6, 1.6], showgrid=False)
        fig.update_xaxes(title="Minuto", range=[-2, 100], gridcolor="#E6ECE7")
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", showlegend=False)
        st.plotly_chart(fig, width="stretch")
        e["Min"] = e["Min"].map(lambda m: "" if pd.isna(m) else f"{int(m)}'" if m <= 90 else f"90+{int(m - 90)}'")
        st.dataframe(e[["Min", "Time", "Evento", "Atleta", "Detalhe"]], hide_index=True, width="stretch",
                     column_config={"Min": st.column_config.TextColumn(width="small"),
                                    "Detalhe": st.column_config.TextColumn(width="large")})

# ------------------------------------------------------------------ escalações
with tabs[1]:
    st.caption("A súmula não informa a posição nem o desenho tático. O campo abaixo posiciona os titulares **pela numeração de camisa** "
               "(convenção brasileira: 1 goleiro, 2 lateral direito, 3–4 zagueiros, 5 volante, 6 lateral esquerdo, 7 e 11 pontas, "
               "8 meia, 9 centroavante, 10 armador). É uma **leitura da súmula**, não a formação real do jogo.")
    cols = st.columns(2)
    for col, equipe in zip(cols, (mand, visit)):
        with col:
            e = pj[pj["equipe"] == equipe].copy()
            e["situacao"] = e.apply(lambda x: "Titular" if x["titular"] else ("Entrou" if x["entrou"] else "Banco"), axis=1)
            padrao_n = cm.padrao_de_numeracao(e)
            st.markdown(f"#### {equipe}")
            if padrao_n["total"]:
                st.markdown(f"**Padrão de numeração: {padrao_n['nivel']}** — {padrao_n['convencionais']} de {padrao_n['total']} titulares "
                            f"de linha usam camisas 2–11<br/><small style='color:#5B6B62'>{padrao_n['distribuicao']}</small>",
                            unsafe_allow_html=True)
            pos = cm.posicoes_no_campo(e)
            if not pos.empty:
                st.plotly_chart(campo.figura_campo(pos, "Titulares pela numeração", 460), width="stretch", key=f"campo_{equipe}")
            e["Função (convenção)"] = e["numero"].map(cm.funcao_provavel)
            out = e.sort_values(["numero"])[["numero", "nome", "situacao", "Função (convenção)", "minutos", "gols", "amarelos",
                                             "vermelhos"]].rename(columns={"numero": "Nº", "nome": "Atleta", "situacao": "Situação",
                                                                          "minutos": "Min", "gols": "Gols", "amarelos": "🟨",
                                                                          "vermelhos": "🟥"})
            tabela(out, f"esc_{equipe}", ordenar_por="Nº", crescente=True, com_controles=False, altura=420, fixar="Atleta")

# ------------------------------------------------------------------ comparativo
with tabs[2]:
    linhas = []
    for equipe, gp, gc, gp1, gc1 in ((mand, r["gols_mandante"], r["gols_visitante"], r["gols_1t_mandante"], r["gols_1t_visitante"]),
                                     (visit, r["gols_visitante"], r["gols_mandante"], r["gols_1t_visitante"], r["gols_1t_mandante"])):
        e = pj[pj["equipe"] == equipe]
        ce = c[c["equipe"] == equipe]
        se = s_[s_["equipe"] == equipe]
        linhas.append({"Time": equipe, "Gols": int(gp), "Gols 1º tempo": int(gp1) if pd.notna(gp1) else None,
                       "Gols 2º tempo": int(gp - gp1) if pd.notna(gp1) else None,
                       "Amarelos": int((ce["tipo"] == "amarelo").sum()), "Vermelhos": int((ce["tipo"] == "vermelho").sum()),
                       "Substituições": len(se), "Minuto da 1ª troca": round(se["minuto"].min()) if len(se) else None,
                       "Relacionados": len(e), "Titulares": int(e["titular"].sum()), "Atletas utilizados": int(e["jogou"].sum())})
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
    if not g.empty:
        st.markdown("#### Quem marcou")
        gg = g.groupby(["jogador", "equipe_creditada"]).size().reset_index(name="Gols").rename(
            columns={"jogador": "Atleta", "equipe_creditada": "Time"}).sort_values("Gols", ascending=False)
        st.dataframe(gg, hide_index=True, width="stretch")

# ------------------------------------------------------------------ arbitragem
with tabs[3]:
    if not isinstance(r.get("arbitro"), str):
        st.info("Sem dados de arbitragem para este jogo.")
    else:
        a = st.columns(4)
        a[0].metric("Árbitro", r["arbitro"], r.get("arbitro_vinculo"), delta_color="off")
        a[1].metric("Assistentes", " · ".join(x for x in (r.get("assistente1"), r.get("assistente2")) if isinstance(x, str)) or "—")
        a[2].metric("Quarto árbitro", r.get("quarto_arbitro") if isinstance(r.get("quarto_arbitro"), str) else "—")
        a[3].metric("VAR", r.get("var") if isinstance(r.get("var"), str) else "Sem VAR")
        ac = st.columns(4)
        ac[0].metric("Acréscimo 1º tempo", f"{int(r['acrescimo_1t'])} min" if pd.notna(r.get("acrescimo_1t")) else "—")
        ac[1].metric("Acréscimo 2º tempo", f"{int(r['acrescimo_2t'])} min" if pd.notna(r.get("acrescimo_2t")) else "—")
        ac[2].metric("Amarelos no jogo", int((c["tipo"] == "amarelo").sum()))
        ac[3].metric("Vermelhos no jogo", int((c["tipo"] == "vermelho").sum()))
        outros = real[(real["arbitro"] == r["arbitro"])]
        if len(outros) > 1:
            cs = cartoes_all[cartoes_all["jogo_id"].isin(set(outros["jogo_id"]))]
            st.caption(f"Nos {len(outros)} jogos deste árbitro na base: {(cs['tipo'] == 'amarelo').sum() / len(outros):.2f} amarelos e "
                       f"{(cs['tipo'] == 'vermelho').sum() / len(outros):.2f} vermelhos por jogo. Veja mais na aba Arbitragem.")

rodape()
