import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import analise as an
import data_loader as dl
import estado
import formacoes
import posicoes_ui as pui
import leiame
from theme import COR, cabecalho, rodape
from ui import abrir_jogo, chips_forma, linha_selecionada, tabela

cabecalho("🔬 Análise de time", "Escolha um time e receba um painel de scout completo, com insights prontos para o seu relatório.")
leiame.mostrar("analise")

if not dl.tem_dados():
    st.warning("Base de dados ainda não gerada.")
    st.stop()

jogos_all = dl.jogos()
gols_all, cartoes_all, partidas_all, subs_all = dl.gols(), dl.cartoes(), dl.partidas(), dl.substituicoes()


def estilo(fig, altura=360, legenda=True):
    fig.update_layout(height=altura, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(family="Inter, sans-serif", color=COR["texto"]), showlegend=legenda,
                      legend=dict(orientation="h", y=1.12, x=0))
    fig.update_yaxes(gridcolor="#E6ECE7", zeroline=False)
    fig.update_xaxes(showgrid=False)
    return fig


# ------------------------------------------------------------------ filtros
estado.barra_limpar("an")
with st.container(border=True):
    f1, f2, f3, f4 = st.columns([1, 1, 2, 1.4])
    cats = sorted(jogos_all["categoria"].unique(), reverse=True)
    categoria = f1.selectbox("Categoria", cats, key="an_cat")
    j = jogos_all[jogos_all["categoria"] == categoria]
    ano = f2.selectbox("Ano", sorted(j["ano"].unique(), reverse=True), index=None, placeholder="Escolha o ano", key="an_ano")
    j = j[j["ano"] == ano] if ano is not None else j.iloc[0:0]
    comps_disp = sorted(j["competicao_nome"].unique())
    comps = f3.multiselect("Competição", comps_disp, placeholder="Escolha a(s) competição(ões)", key="an_comp", disabled=ano is None)
    j = j[j["competicao_nome"].isin(comps)] if comps else j.iloc[0:0]
    fases = sorted(j["fase_nome"].dropna().unique())
    fase = f4.selectbox("Fase", ["Todas"] + fases, key="an_fase", disabled=not comps)
    if fase != "Todas":
        j = j[j["fase_nome"] == fase]

    times = sorted(set(j["time_mandante"]) | set(j["time_visitante"])) if len(j) else []
    g1, g2, g3 = st.columns([2, 1.5, 1.5])
    time = g1.selectbox("Time a analisar", times, index=None, placeholder="Escolha o time", key="an_time", disabled=not times)
    mando = g2.segmented_control("Mando", ["Todos", "Casa", "Fora"], default="Todos", key="an_mando") or "Todos"
    ultimos = g3.number_input("Últimos N jogos (0 = todos)", min_value=0, max_value=60, value=0, step=1, key="an_ult")

if ano is None or not comps or time is None:
    st.info("👆 Escolha o **ano**, a **competição** e o **time** para ver a análise.")
    rodape()
    st.stop()

d = an.jogos_do_time(j, time, mando, int(ultimos))
if d.empty:
    st.info(f"O {time} ainda não tem jogos com súmula nessa seleção.")
    st.stop()

ids = set(d["jogo_id"])
r = an.resumo(d)
g = an.gols_do_time(gols_all, ids, time)
cart_t = an.cartoes_do_time(cartoes_all, ids, time)
elen = an.elenco(partidas_all, ids, time)
subs_t = subs_all[subs_all["jogo_id"].isin(ids) & (subs_all["equipe"] == time)] if not subs_all.empty else subs_all
liga = an.metricas_liga(j, cartoes_all, mando)
prim = an.primeiro_gol(d, g) if not g.empty else pd.DataFrame()
quadro = an.quadro_intervalo(d)
Lm = liga.set_index("Time") if not liga.empty else pd.DataFrame()

cont = an.continuidade_onze(partidas_all, d, time)
cont_res = an.resumo_continuidade(cont)
recorte = f"{mando}" + (f" · últimos {int(ultimos)} jogos" if ultimos else "")
st.markdown(
    f'<div class="ts-hero" style="padding:1.2rem 1.6rem; display:block;"><h1 style="font-size:2rem;margin:0">{time}</h1>'
    f'<p style="margin:.2rem 0 0 0">{", ".join(comps) or "Todas as competições"} · {ano} · {fase} · recorte: {recorte}</p></div>',
    unsafe_allow_html=True)
if r["J"] < 5:
    st.warning(f"Amostra pequena: só {r['J']} jogo(s). Interprete os percentuais com cautela.")


def delta(valor, col, inverso=False):
    if Lm.empty or col not in Lm:
        return None
    return f"{valor - Lm[col].mean():+.2f} vs média"


ultimo = d.iloc[-1]
u1, u2 = st.columns([1.3, 3])
if u1.button("🔎 Ver a súmula do último jogo", key="an_ultimo", type="secondary"):
    abrir_jogo(ultimo["jogo_id"])
u2.caption(f"Último jogo: {ultimo['data']:%d/%m/%Y} · {ultimo['mando']} vs {ultimo['adversario']} · {ultimo['gp']}x{ultimo['gc']}")

m = st.columns(6)
m[0].metric("Jogos", r["J"], f"{r['V']}V {r['E']}E {r['D']}D", delta_color="off")
m[1].metric("Aproveitamento", f"{r['aprov']}%", delta(r["aprov"], "Aproveitamento"))
m[2].metric("Gols pró/jogo", r["gp_j"], delta(r["gp_j"], "Gols pró/jogo"))
m[3].metric("Gols contra/jogo", r["gc_j"], delta(r["gc_j"], "Gols contra/jogo"), delta_color="inverse")
m[4].metric("Saldo de gols", f"{r['SG']:+d}", f"{r['GP']} pró · {r['GC']} contra", delta_color="off")
m[5].metric("Jogos sem sofrer", f"{r['sem_sofrer']}", f"{r['pct_sem_sofrer']}%", delta_color="off")

tabs = st.tabs(["📌 Resumo & insights", "⏱️ Gols e minutagem", "🧠 Como joga", "🟨 Disciplina", "👥 Elenco", "📋 Jogo a jogo", "🧩 Formações"])

# ------------------------------------------------------------------ 1. resumo
with tabs[0]:
    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.markdown("#### Forma recente")
        rec = d.tail(10)
        st.markdown(chips_forma([(x.res, f"{x.data:%d/%m} {x.mando} vs {x.adversario}: {x.gp}x{x.gc}")
                                 for x in rec.itertuples()]), unsafe_allow_html=True)
        st.caption("Passe o mouse sobre a bolinha para ver o jogo · mais antigo → mais recente")
        st.markdown("#### Insights automáticos")
        textos = an.insights(time, d, g, cart_t, elen, liga, prim, quadro, subs_t, cont_res)
        for t in textos:
            st.markdown(f"- {t}")
    with c2:
        st.markdown("#### Perfil frente ao campeonato")
        if len(liga) >= 3:
            comparar = st.radio("Comparar com", ["Média do campeonato", "Outro time"], horizontal=True, key="an_comp_com",
                                label_visibility="collapsed")
            rv = an.radar_valores(liga, time)
            eixos = list(rv["media"].keys())
            fig = go.Figure()
            if comparar == "Outro time":
                outros = [t for t in liga["Time"] if t != time]
                outro = st.selectbox("Time de comparação", outros, key="an_outro")
                ov = an.radar_valores(liga, outro)["time"]
                fig.add_trace(go.Scatterpolar(r=list(ov.values()) + [list(ov.values())[0]], theta=eixos + [eixos[0]],
                                              name=outro, line=dict(color=COR["vermelho"], width=2), fill="toself",
                                              fillcolor="rgba(200,16,46,.12)"))
            else:
                fig.add_trace(go.Scatterpolar(r=list(rv["media"].values()) + [list(rv["media"].values())[0]],
                                              theta=eixos + [eixos[0]], name="Média do campeonato",
                                              line=dict(color=COR["dourado"], width=2, dash="dot")))
            tv = rv["time"]
            if tv:
                fig.add_trace(go.Scatterpolar(r=list(tv.values()) + [list(tv.values())[0]], theta=eixos + [eixos[0]],
                                              name=time, line=dict(color=COR["verde"], width=3), fill="toself",
                                              fillcolor="rgba(14,107,63,.25)"))
            fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], showticklabels=False, gridcolor="#E6ECE7")),
                              height=380, margin=dict(l=30, r=30, t=20, b=20), legend=dict(orientation="h", y=-0.08))
            st.plotly_chart(fig, width="stretch")
            st.caption("100 = melhor time da seleção naquele eixo, 0 = pior. Defesa e Disciplina são invertidas "
                       "(menos gols/cartões = melhor).")
        else:
            st.info("Poucos times na seleção para montar o comparativo.")
    if not liga.empty:
        st.markdown("#### Ranking na seleção")
        rk = liga.copy()
        for col, asc in (("Aproveitamento", False), ("Gols pró/jogo", False), ("Gols contra/jogo", True),
                         ("Jogos sem sofrer (%)", False), ("Amarelos/jogo", True)):
            rk[f"{col} (pos.)"] = rk[col].rank(ascending=asc, method="min").astype(int)
        linha = rk[rk["Time"] == time]
        cols = st.columns(5)
        for c, (nome, pos_col) in zip(cols, (("Aproveitamento", "Aproveitamento (pos.)"), ("Ataque", "Gols pró/jogo (pos.)"),
                                             ("Defesa", "Gols contra/jogo (pos.)"), ("Solidez", "Jogos sem sofrer (%) (pos.)"),
                                             ("Disciplina", "Amarelos/jogo (pos.)"))):
            c.metric(nome, f"{int(linha[pos_col].iloc[0])}º", f"de {len(rk)} times", delta_color="off")
    st.markdown("#### Texto pronto para o relatório")
    if textos:
        limpo = "\n".join("• " + t.replace("**", "") for t in textos)
        st.code(f"{time} — {', '.join(comps)} {ano} ({recorte})\n{limpo}", language=None)
        st.caption("Use o ícone de copiar no canto do bloco.")

# ------------------------------------------------------------------ 2. gols e minutagem
with tabs[1]:
    if g.empty:
        st.info("Sem gols registrados nos jogos dessa seleção.")
    else:
        faixas, tempos = an.por_faixa(g), an.por_tempo(g)
        a, b = st.columns([1.6, 1])
        with a:
            st.markdown("#### Gols por faixa de 15 minutos")
            fig = go.Figure()
            fig.add_bar(x=faixas["Faixa"], y=faixas["Feitos"], name="Feitos", marker_color=COR["verde"], text=faixas["Feitos"])
            fig.add_bar(x=faixas["Faixa"], y=faixas["Sofridos"], name="Sofridos", marker_color=COR["vermelho"], text=faixas["Sofridos"])
            fig.update_traces(textposition="outside")
            fig.update_layout(barmode="group", xaxis_title="Minuto do jogo", yaxis_title="Gols")
            st.plotly_chart(estilo(fig), width="stretch")
        with b:
            st.markdown("#### 1º tempo × 2º tempo")
            fig = go.Figure()
            fig.add_bar(x=tempos["Tempo"], y=tempos["Feitos"], name="Feitos", marker_color=COR["verde"], text=tempos["Feitos"])
            fig.add_bar(x=tempos["Tempo"], y=tempos["Sofridos"], name="Sofridos", marker_color=COR["vermelho"], text=tempos["Sofridos"])
            fig.update_traces(textposition="outside")
            fig.update_layout(barmode="group")
            st.plotly_chart(estilo(fig), width="stretch")
        tf, ts = int(tempos["Feitos"].sum()), int(tempos["Sofridos"].sum())
        k = st.columns(4)
        k[0].metric("Gols feitos no 2º tempo", f"{round(tempos.loc[1, 'Feitos'] / tf * 100) if tf else 0}%")
        k[1].metric("Gols sofridos no 2º tempo", f"{round(tempos.loc[1, 'Sofridos'] / ts * 100) if ts else 0}%")
        pro_g = g[g["lado"] == "Pró"]
        k[2].metric("Minuto médio do gol marcado", f"{pro_g['minuto'].mean():.0f}'" if len(pro_g) else "—")
        con_g = g[g["lado"] == "Contra"]
        k[3].metric("Minuto médio do gol sofrido", f"{con_g['minuto'].mean():.0f}'" if len(con_g) else "—")

        st.markdown("#### Linha do tempo acumulada dos gols")
        fig = go.Figure()
        for lado, cor, nome in (("Pró", COR["verde"], "Feitos"), ("Contra", COR["vermelho"], "Sofridos")):
            m_ = sorted(g[(g["lado"] == lado)]["minuto"].dropna())
            fig.add_scatter(x=[0] + m_ + [95], y=[0] + list(range(1, len(m_) + 1)) + [len(m_)], mode="lines",
                            line=dict(color=cor, width=3, shape="hv"), name=nome)
        fig.add_vline(x=45, line_dash="dot", line_color="#9AA9A0", annotation_text="Intervalo")
        fig.update_layout(xaxis_title="Minuto", yaxis_title="Gols acumulados")
        st.plotly_chart(estilo(fig, 320), width="stretch")

        st.markdown("#### Distribuição de gols por jogo")
        dist = an.dist_gols_por_jogo(d)
        fig = go.Figure()
        fig.add_bar(x=dist["Gols no jogo"], y=dist["Feitos"], name="Feitos", marker_color=COR["verde"])
        fig.add_bar(x=dist["Gols no jogo"], y=dist["Sofridos"], name="Sofridos", marker_color=COR["vermelho"])
        fig.update_layout(barmode="group", xaxis_title="Gols em um jogo", yaxis_title="Nº de jogos")
        st.plotly_chart(estilo(fig, 300), width="stretch")
        placar = d.apply(lambda x: f"{x.gp}x{x.gc}", axis=1).value_counts()
        st.caption(f"Placar mais comum: {placar.index[0]} ({placar.iloc[0]}x) · placares do time (feitos x sofridos).")

# ------------------------------------------------------------------ 3. como joga
with tabs[2]:
    a, b = st.columns(2)
    with a:
        st.markdown("#### Quem abre o placar")
        if prim.empty:
            st.info("Sem dados de gols.")
        else:
            resumo_p = []
            for rot, chave in (("Marca primeiro", "Pró"), ("Sofre primeiro", "Contra"), ("Sem gols", "Sem gols")):
                x = prim[prim["primeiro"] == chave]
                resumo_p.append({"Situação": rot, "Jogos": len(x), "Vitórias": int((x.res == "V").sum()),
                                 "Empates": int((x.res == "E").sum()), "Derrotas": int((x.res == "D").sum())})
            tabela(pd.DataFrame(resumo_p), "prim", com_controles=False)
    with b:
        st.markdown("#### Intervalo × resultado final")
        if quadro.empty:
            st.info("Sem placar de intervalo.")
        else:
            tabela(quadro, "quad", com_controles=False)
    a, b = st.columns(2)
    with a:
        st.markdown("#### Casa × fora")
        cf = d.groupby("mando").agg(Jogos=("jogo_id", "count"), Vitórias=("res", lambda s: (s == "V").sum()),
                                    Empates=("res", lambda s: (s == "E").sum()), Derrotas=("res", lambda s: (s == "D").sum()),
                                    GP=("gp", "sum"), GC=("gc", "sum"), Pontos=("pontos", "sum")).reset_index()
        cf["Gols pró/jogo"] = (cf["GP"] / cf["Jogos"]).round(2)
        cf["Gols contra/jogo"] = (cf["GC"] / cf["Jogos"]).round(2)
        cf["Aproveitamento (%)"] = (cf["Pontos"] / (cf["Jogos"] * 3) * 100).round(1)
        tabela(cf.rename(columns={"mando": "Mando"}), "cf", com_controles=False)
    with b:
        st.markdown("#### Como saem os gols do time")
        tg = an.tipos_de_gol(g) if not g.empty else pd.DataFrame()
        if tg.empty:
            st.info("Sem gols do time na seleção.")
        else:
            fig = go.Figure(go.Pie(labels=tg["Tipo"], values=tg["Gols"], hole=.55,
                                   marker=dict(colors=[COR["verde"], COR["dourado"], COR["vermelho"], "#7FB59A"])))
            st.plotly_chart(estilo(fig, 300), width="stretch")
    st.markdown("#### Resultado por adversário")
    tabela(d[["data", "adversario", "mando", "gp", "gc", "res"]].rename(columns={
        "data": "Data", "adversario": "Adversário", "mando": "Mando", "gp": "GP", "gc": "GC", "res": "Res."}),
        "advers", ordenar_por="Data", altura=300)

# ------------------------------------------------------------------ 4. disciplina
with tabs[3]:
    if cart_t.empty:
        st.info("Sem cartões registrados para o time nessa seleção.")
    else:
        am, vm = int((cart_t["tipo"] == "amarelo").sum()), int((cart_t["tipo"] == "vermelho").sum())
        k = st.columns(4)
        k[0].metric("Amarelos", am, f"{am / r['J']:.2f} por jogo", delta_color="off")
        diretos = int((cart_t.get("detalhe", pd.Series(dtype=str)) == "Cartão Vermelho Direto").sum())
        k[1].metric("Vermelhos", vm, f"{diretos} diretos · {vm - diretos} por 2º amarelo" if vm else None, delta_color="off")
        if not Lm.empty:
            k[2].metric("Amarelos/jogo (média da seleção)", f"{Lm['Amarelos/jogo'].mean():.2f}")
        k[3].metric("Cartões no 2º tempo", f"{round((cart_t['periodo'] == 2).mean() * 100)}%")
        a, b = st.columns([1.4, 1])
        with a:
            st.markdown("#### Cartões por faixa de minuto")
            cf_ = cart_t.groupby(["faixa", "tipo"]).size().unstack(fill_value=0).reindex(an.FAIXAS, fill_value=0)
            fig = go.Figure()
            fig.add_bar(x=cf_.index, y=cf_.get("amarelo", pd.Series(0, index=cf_.index)), name="Amarelos", marker_color=COR["dourado"])
            fig.add_bar(x=cf_.index, y=cf_.get("vermelho", pd.Series(0, index=cf_.index)), name="Vermelhos", marker_color=COR["vermelho"])
            fig.update_layout(barmode="stack", xaxis_title="Minuto do jogo", yaxis_title="Cartões")
            st.plotly_chart(estilo(fig, 320), width="stretch")
        with b:
            st.markdown("#### Atletas mais advertidos")
            staff = cart_t["comissao"].fillna(False).astype(bool) if "comissao" in cart_t else pd.Series(False, index=cart_t.index)
            top = cart_t.assign(jogador=cart_t["jogador"].where(~staff, cart_t["jogador"] + " (comissão)")).groupby("jogador").agg(Amarelos=("tipo", lambda s: (s == "amarelo").sum()),
                                                Vermelhos=("tipo", lambda s: (s == "vermelho").sum())).reset_index()
            top = top.rename(columns={"jogador": "Atleta"})
            tabela(top, "cart_top", ordenar_por="Amarelos", altura=320)
        motivos = cart_t["motivo"].dropna().str.replace(r"^\d+\s*-\s*", "", regex=True).str.split(" - ").str[0]
        if len(motivos):
            st.markdown("#### Motivos mais comuns")
            mv = motivos.value_counts().head(6).reset_index()
            mv.columns = ["Motivo", "Cartões"]
            tabela(mv, "motivos", com_controles=False)

# ------------------------------------------------------------------ 5. elenco
with tabs[4]:
    if elen.empty:
        st.info("Sem dados de elenco.")
    else:
        a, b = st.columns([1.3, 1])
        with a:
            st.markdown("#### Minutos jogados")
            top = elen.head(15).iloc[::-1]
            fig = go.Figure(go.Bar(x=top["Minutos"], y=top["Atleta"], orientation="h", marker_color=COR["verde"],
                                   text=top["Minutos"], textposition="outside"))
            st.plotly_chart(estilo(fig, 440, False), width="stretch")
        with b:
            st.markdown("#### Onze mais utilizado")
            onze = elen.sort_values(["Titular", "Minutos"], ascending=False).head(11)[["Atleta", "Posição", "Titular", "Minutos"]]
            tabela(onze, "onze", com_controles=False)
            if len(subs_t):
                k = st.columns(2)
                k[0].metric("Substituições/jogo", f"{len(subs_t) / r['J']:.1f}")
                k[1].metric("Minuto da 1ª troca", f"{subs_t.groupby('jogo_id')['minuto'].min().mean():.0f}'")
        if not cont.empty:
            st.markdown("#### Continuidade do onze")
            k = st.columns(4)
            k[0].metric("Titulares mantidos por jogo", cont_res["media_mantidos"], help="Média de atletas que repetem como titulares em relação ao jogo anterior")
            k[1].metric("Mudanças por jogo", cont_res["media_novos"])
            k[2].metric("Jogos com até 2 mudanças", f"{cont_res['pct_ate_2']}%")
            k[3].metric("Onze idêntico ao anterior", f"{cont_res['pct_igual']}%")
            fig = go.Figure(go.Bar(x=cont["Data"], y=cont["Titulares novos"], marker_color=COR["dourado"],
                                   text=cont["Titulares novos"], textposition="outside",
                                   hovertext="vs " + cont["Adversário"]))
            fig.update_layout(yaxis_title="Titulares novos vs jogo anterior")
            st.plotly_chart(estilo(fig, 260, False), width="stretch")
            st.caption("Quanto mais alto, mais rotação. Barras sempre baixas indicam um time-base estável.")
        st.markdown("#### Elenco completo")
        pui.aviso()
        _pos = pui.tabela_final().set_index("atleta_id")
        elen_v = elen.drop(columns=["Posição"], errors="ignore")
        elen_v.insert(1, "Posição", elen_v["atleta_id"].map(_pos["exibicao"]).fillna("Não confirmada"))
        elen_v.insert(2, "Status da posição", elen_v["atleta_id"].map(_pos["status"]).fillna(pui.STATUS_NAO))
        tabela(elen_v.drop(columns=["atleta_id"]), "elenco", ordenar_por="Minutos", fixar="Atleta", altura=420,
               exportar=f"tche-scout-elenco-{time}")
        with st.expander("✏️ Ajustar posições deste time (vale só para esta visita e para o PDF)"):
            pui.editor_time(elen[["atleta_id", "Atleta", "Jogos"]], f"an_{time}")

# ------------------------------------------------------------------ 6. jogo a jogo
with tabs[5]:
    x = d.copy()
    x["pontos_acum"] = x["pontos"].cumsum()
    fig = go.Figure(go.Scatter(x=x["data"], y=x["pontos_acum"], mode="lines+markers", line=dict(color=COR["verde"], width=3),
                               marker=dict(size=9, color=x["res"].map({"V": COR["verde"], "E": COR["dourado"], "D": COR["vermelho"]})),
                               text=x["adversario"] + " " + x["gp"].astype(str) + "x" + x["gc"].astype(str),
                               hovertemplate="%{text}<br>%{y} pts<extra></extra>"))
    fig.update_layout(yaxis_title="Pontos acumulados")
    st.plotly_chart(estilo(fig, 280, False), width="stretch")
    tabela(x[["data", "competicao", "fase", "rodada", "mando", "adversario", "gp", "gc", "gp1", "gc1", "res", "jogo_id"]].rename(columns={
        "data": "Data", "competicao": "Competição", "fase": "Fase", "rodada": "Rodada", "mando": "Mando",
        "adversario": "Adversário", "gp": "GP", "gc": "GC", "gp1": "GP 1ºT", "gc1": "GC 1ºT", "res": "Res."}),
        "jxj", ordenar_por="Data", exportar=f"tche-scout-jogos-{time}", altura=420, selecionavel=True, ocultar=["jogo_id"])
    sel = linha_selecionada("jxj")
    if st.button("🔎 Analisar o jogo selecionado", disabled=sel is None, type="primary", key="jxj_analisar"):
        abrir_jogo(sel["jogo_id"])
    st.caption("Clique numa linha para selecioná-la.")

# ------------------------------------------------------------------ 7. formações (manual)
with tabs[6]:
    st.markdown("A súmula não traz a formação tática. Preencha o desenho de cada jogo do time na tabela abaixo (clique na célula "
                "**Formação**) e veja o rendimento por formação.")
    st.warning("Os registros são digitados por pessoas e **não são verificados**. Valem só nesta visita "
               "(e entram no PDF que você gerar em Relatórios e cards); ao recarregar a página, somem.")
    ed = d[["jogo_id", "data", "adversario", "mando", "gp", "gc", "res"]].copy()
    ed["Formação"] = ed["jogo_id"].map(lambda i: formacoes.obter(i, time)[0])
    ed["Observação"] = ed["jogo_id"].map(lambda i: formacoes.obter(i, time)[1])
    ed["Placar"] = ed["gp"].astype(str) + " x " + ed["gc"].astype(str)
    ed = ed.rename(columns={"data": "Data", "adversario": "Adversário", "mando": "Mando", "res": "Res."}).set_index("jogo_id")
    ed = ed[["Data", "Adversário", "Mando", "Placar", "Res.", "Formação", "Observação"]]
    opcoes = formacoes.OPCOES + sorted({v for v in ed["Formação"] if v and v not in formacoes.OPCOES})
    editado = st.data_editor(
        ed, hide_index=True, width="stretch", key=f"ed_form_{time}_{mando}_{int(ultimos)}",
        disabled=["Data", "Adversário", "Mando", "Placar", "Res."],
        column_config={"Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY", width="small"),
                       "Formação": st.column_config.SelectboxColumn("Formação", options=opcoes, width="small"),
                       "Observação": st.column_config.TextColumn("Observação", width="large")})
    for jid, row in editado.iterrows():
        formacoes.salvar(jid, time, row["Formação"] or "", row["Observação"] or "")
    resumo_f = formacoes.resumo_por_formacao(d, time)
    if resumo_f.empty:
        st.info("Nenhuma formação registrada ainda para este recorte.")
    else:
        st.markdown("#### Rendimento por formação")
        top = resumo_f.iloc[0]
        st.markdown(f"- **Mais usada:** {top['Formação']} em {int(top['Jogos'])} jogos "
                    f"({top['Aproveitamento (%)']}% de aproveitamento).")
        tabela(resumo_f, "formacoes_res", ordenar_por="Jogos", com_controles=False)
        fig = go.Figure(go.Bar(x=resumo_f["Formação"], y=resumo_f["Aproveitamento (%)"], marker_color=COR["verde"],
                               text=resumo_f["Jogos"].map(lambda n: f"{n} jogo(s)"), textposition="outside"))
        fig.update_layout(yaxis_title="Aproveitamento (%)", yaxis_range=[0, 110])
        st.plotly_chart(estilo(fig, 300, False), width="stretch")
        st.caption("Com poucos jogos por formação, a comparação é frágil — use como indício, não como conclusão.")
    formacoes.painel_arquivo()

rodape()
