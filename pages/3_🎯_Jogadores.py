import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data_loader as dl
import leiame
import camisas as cm
import posicoes as po
import stats
from theme import COR, cabecalho, rodape
from ui import tabela

cabecalho("🎯 Jogadores", "Base de atletas dos campeonatos gaúchos, com nomes padronizados a partir das súmulas.")
leiame.mostrar("jogadores")

if not dl.tem_dados():
    st.warning("Base de dados ainda não gerada.")
    st.stop()

jogos, partidas = dl.jogos(), dl.partidas()
if partidas.empty:
    st.info("Nenhum dado de atleta na base.")
    st.stop()

meta_jogos = jogos[["jogo_id", "categoria", "ano", "competicao_nome", "fase_nome", "data", "time_mandante",
                    "time_visitante", "gols_mandante", "gols_visitante"]]
# no jogador-partida, "categoria" = vinculo (Profissional/Amador); no jogo, "categoria" = Masculino/Feminino
p = partidas.rename(columns={"categoria": "vinculo"}).merge(meta_jogos, on="jogo_id", how="inner").sort_values("data")  # ordem cronologica: "Time" do atleta = o mais recente

f1, f2, f3, f4 = st.columns(4)
categoria = f1.selectbox("Categoria", sorted(p["categoria"].unique(), reverse=True))
p = p[p["categoria"] == categoria]
anos = f2.multiselect("Ano", sorted(p["ano"].unique(), reverse=True), default=[max(p["ano"])])
p = p[p["ano"].isin(anos)] if anos else p
comps = f3.multiselect("Competição", sorted(p["competicao_nome"].unique()), placeholder="Todas")
if comps:
    p = p[p["competicao_nome"].isin(comps)]
times = f4.multiselect("Time", sorted(p["equipe"].unique()), placeholder="Todos")
if times:
    p = p[p["equipe"].isin(times)]

g1, g2, g3 = st.columns([2, 1, 1])
busca = g1.text_input("Buscar atleta", placeholder="Digite parte do nome ou apelido…")
posicao = g2.selectbox("Posição / zona", ["Todas", "Goleiro", "Defesa", "Meio", "Ataque", "Sem informação"])
so_atuaram = g3.toggle("Só quem atuou", value=True, help="Esconde atletas que ficaram apenas no banco.")

painel = stats.painel_atletas(p).drop(columns=["Posição"]).merge(dl.atletas()[["atleta_id", "nome_completo"]], on="atleta_id", how="left")
pos_tab = dl.posicoes()
if pos_tab.empty:
    pos_tab = pd.DataFrame(columns=["atleta_id", "posicao", "zona", "fonte", "confianca", "camisa_principal", "url", "obs_pesquisa"])
manuais = st.session_state.setdefault("posicoes_manuais", {})
pos_tab = po.aplicar_manuais(pos_tab, manuais)
painel = painel.merge(pos_tab[["atleta_id", "posicao", "zona", "fonte", "confianca", "url", "obs_pesquisa"]], on="atleta_id", how="left")
painel["Posição"] = painel["posicao"].fillna(painel["zona"].map(lambda z: f"{z} (zona)" if isinstance(z, str) else None)).fillna("—")
painel["Fonte da posição"] = painel["fonte"].fillna("—")
painel["Confiança (%)"] = painel["confianca"]
painel = painel.rename(columns={"nome_completo": "Nome completo"})
if painel.empty:
    st.info("Nenhum atleta para essa seleção.")
    st.stop()
if busca:
    painel = painel[painel["Atleta"].str.contains(busca, case=False, na=False)
                    | painel["Nome completo"].str.contains(busca, case=False, na=False)]
if posicao != "Todas":
    if posicao == "Sem informação":
        painel = painel[painel["zona"].isna()]
    else:
        painel = painel[painel["zona"] == posicao]
if so_atuaram:
    painel = painel[painel["Jogos"] > 0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Atletas", len(painel))
k2.metric("Gols", int(painel["Gols"].sum()))
k3.metric("Cartões amarelos", int(painel["Amarelos"].sum()))
k4.metric("Cartões vermelhos", int(painel["Vermelhos"].sum()))

tab_tab, tab_graf, tab_ficha, tab_cam, tab_pos = st.tabs(["Tabela de atletas", "Gráficos", "Ficha do atleta", "👕 Camisas", "📍 Posições"])

with tab_tab:
    cols = ["Atleta", "Nome completo", "Time", "Times", "Posição", "Fonte da posição", "Confiança (%)", "Relacionado", "Jogos", "Titular", "Entrou", "Banco", "Substituído",
            "Minutos", "Gols", "G.C.", "Min/gol", "Amarelos", "Vermelhos"]
    tabela(painel[cols], "atl", ordenar_por="Gols", fixar="Atleta", altura=520, exportar="tche-scout-atletas",
           ajuda={"Times": "Em quantos times o atleta atuou na seleção", "Relacionado": "Jogos em que constou na súmula",
                  "Jogos": "Titular + entrou durante o jogo", "Entrou": "Entrou como substituto",
                  "Banco": "Relacionado e não utilizado", "Substituído": "Saiu por substituição",
                  "G.C.": "Gols contra", "Min/gol": "Minutos jogados por gol marcado"})
    st.caption("Minutos calculados a partir de titularidade, substituições e expulsões (jogo de 90 min). "
               "Assistências não constam nas súmulas oficiais. Nomes completos podem aparecer cortados: é como a FGF os publica.")

with tab_graf:
    top = painel.sort_values("Gols", ascending=False).head(15).iloc[::-1]
    fig = go.Figure(go.Bar(x=top["Gols"], y=top["Atleta"] + " (" + top["Time"] + ")", orientation="h",
                           marker_color=COR["verde"]))
    fig.update_layout(title="Maiores artilheiros", height=460, margin=dict(l=0, r=0, t=40, b=0), plot_bgcolor="white")
    st.plotly_chart(fig, width="stretch")
    disc = painel.assign(Total=painel["Amarelos"] + painel["Vermelhos"] * 2).sort_values("Total", ascending=False).head(15).iloc[::-1]
    fig2 = go.Figure()
    fig2.add_bar(x=disc["Amarelos"], y=disc["Atleta"] + " (" + disc["Time"] + ")", orientation="h", name="Amarelos",
                 marker_color=COR["dourado"])
    fig2.add_bar(x=disc["Vermelhos"], y=disc["Atleta"] + " (" + disc["Time"] + ")", orientation="h", name="Vermelhos",
                 marker_color=COR["vermelho"])
    fig2.update_layout(title="Mais cartões", barmode="stack", height=460, margin=dict(l=0, r=0, t=40, b=0), plot_bgcolor="white")
    st.plotly_chart(fig2, width="stretch")

with tab_ficha:
    opcoes = painel.assign(rotulo=painel["Atleta"] + " — " + painel["Time"]).set_index("atleta_id")["rotulo"]
    if opcoes.empty:
        st.info("Nenhum atleta para exibir.")
    else:
        escolhido = st.selectbox("Atleta", opcoes.index, format_func=lambda a: opcoes[a])
        linha = painel[painel["atleta_id"] == escolhido].iloc[0]
        st.subheader(linha["Atleta"])
        cad = dl.atletas()
        c = cad[cad["atleta_id"] == escolhido]
        if not c.empty:
            st.caption(f"Nome completo: {c.iloc[0]['nome_completo']} · Registro CBF: {escolhido} · "
                       f"Equipes: {', '.join(c.iloc[0]['equipes'])}")
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Jogos", int(linha["Jogos"]))
        m2.metric("Titular", int(linha["Titular"]))
        m3.metric("Entrou", int(linha["Entrou"]))
        m4.metric("Minutos", int(linha["Minutos"]))
        m5.metric("Gols", int(linha["Gols"]))
        m6.metric("🟨 / 🟥", f"{int(linha['Amarelos'])} / {int(linha['Vermelhos'])}")
        hist = p[p["atleta_id"] == escolhido].sort_values("data", ascending=False).copy()
        hist["Data"] = hist["data"]
        hist["Confronto"] = (hist["time_mandante"] + " " + hist["gols_mandante"].astype(int).astype(str) + " x "
                             + hist["gols_visitante"].astype(int).astype(str) + " " + hist["time_visitante"])
        hist["Situação"] = hist.apply(lambda r: "Titular" if r["titular"] else ("Entrou" if r["entrou"] else "Banco"), axis=1)
        out = hist[["Data", "competicao_nome", "Confronto", "equipe", "Situação", "minutos", "gols", "amarelos", "vermelhos"]]
        out.columns = ["Data", "Competição", "Confronto", "Time", "Situação", "Min", "Gols", "🟨", "🟥"]
        tabela(out, "ficha", ordenar_por="Data", altura=360)

with tab_cam:
    st.markdown("#### O que cada número costuma significar")
    st.caption("A súmula não traz a posição do atleta, mas a numeração no Brasil segue convenções fortes. "
               "Aqui, a convenção é comparada com o que os dados mostram (gols, cartões, goleiros) na seleção de filtros acima.")
    perfil = cm.perfil_camisas(p, minimo_jogos=15)
    if perfil.empty:
        st.info("Poucos dados para montar o perfil das camisas nessa seleção.")
    else:
        fig = go.Figure()
        cores = perfil["Zona (convenção)"].map(cm.COR_ZONA)
        fig.add_bar(x=perfil["Camisa"].astype(str), y=perfil["Gols/jogo"], marker_color=cores,
                    text=perfil["Zona (convenção)"], hovertext=perfil["Função provável"])
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor="white",
                          xaxis_title="Camisa", yaxis_title="Gols por jogo (atleta que atuou)", title="Gols por jogo de cada camisa")
        st.plotly_chart(fig, width="stretch")
        for t in cm.insights_camisas(perfil):
            st.markdown(f"- {t}")
        st.caption("Cores = zona pela convenção: goleiro, defesa (laterais e zagueiros), meio e ataque. "
                   "Se a barra alta for mesmo das camisas de ataque (7, 9, 11...), a convenção se confirma nos dados.")
        tabela(perfil, "camisas", ordenar_por="Camisa", crescente=True, fixar="Camisa", altura=460, exportar="tche-scout-camisas",
               ajuda={"Leitura dos dados": "Zona sugerida pelo comportamento estatístico da camisa (gols, cartões, goleiro)",
                      "Atletas": "Quantos atletas diferentes vestiram o número"})
    fixos = cm.numeracao_dos_atletas(p)
    if not fixos.empty:
        st.markdown("#### Atletas de camisa fixa")
        f = fixos.merge(painel[["atleta_id", "Atleta", "Time", "Jogos"]], on="atleta_id")
        f = f[f["Jogos"] >= 5].rename(columns={"camisa_principal": "Camisa principal", "fixo_pct": "% dos jogos com essa camisa",
                                                "numeros_usados": "Nº de camisas diferentes"})
        f["Zona (convenção)"] = f["Camisa principal"].map(lambda n: cm.zona(n))
        tabela(f[["Atleta", "Time", "Camisa principal", "% dos jogos com essa camisa", "Nº de camisas diferentes", "Zona (convenção)",
                  "Jogos"]], "camfixa", ordenar_por="Jogos", fixar="Atleta", altura=360)

with tab_pos:
    st.markdown("A súmula não traz a posição do atleta. O Tchê Scout monta a posição em **camadas**, sempre mostrando a **fonte** e a **confiança**:")
    st.markdown(
        "1. **Súmula (goleiro)** — exata: a súmula marca quem é goleiro.  \n"
        "2. **Inferida pela camisa** — usa a camisa mais usada (convenção brasileira) e quanto o atleta a repete. "
        "Confiança máxima de 80%: é aproximação e pode errar (ex.: a camisa 5 nem sempre é volante).  \n"
        "3. **Fonte aberta** — pesquisada em notícias e sites de scout, com o **link da fonte**. Cobre só parte dos atletas "
        "(os de mais destaque) e pode confundir homônimos: confira o link.  \n"
        "4. **Manual (você)** — vale mais que todas as outras.")
    st.warning("Posições não vêm da súmula e **podem estar erradas**. A camisa é uma pista e as fontes abertas podem confundir "
               "atletas homônimos. Correções manuais ficam só na sua sessão — use **Baixar CSV**.")
    cob = painel["fonte"].fillna("Sem informação").value_counts().rename_axis("Fonte").reset_index(name="Atletas")
    cob["%"] = (cob["Atletas"] / cob["Atletas"].sum() * 100).round(1)
    st.markdown("#### Cobertura na seleção atual")
    st.dataframe(cob, hide_index=True, width="stretch")
    st.markdown("#### Conferir e corrigir")
    ed = painel[["atleta_id", "Atleta", "Time", "Jogos", "posicao", "Fonte da posição", "Confiança (%)", "url"]].rename(
        columns={"posicao": "Posição", "url": "Fonte (link)"}).sort_values("Jogos", ascending=False).head(400).set_index("atleta_id")
    ed["Posição"] = ed["Posição"].fillna("")
    ed["Fonte (link)"] = ed["Fonte (link)"].fillna("")
    editado = st.data_editor(
        ed, hide_index=True, width="stretch", height=420, key="ed_posicoes",
        disabled=["Atleta", "Time", "Jogos", "Fonte da posição", "Confiança (%)", "Fonte (link)"],
        column_config={"Posição": st.column_config.SelectboxColumn("Posição", options=[""] + po.POSICOES, width="medium"),
                       "Fonte (link)": st.column_config.LinkColumn("Fonte (link)", display_text="abrir")})
    st.caption("Mostrando até 400 atletas (mais jogos primeiro). Escolha a posição na coluna **Posição** para corrigir.")
    for aid, row in editado.iterrows():
        if row["Posição"] and row["Posição"] != ed.loc[aid, "Posição"]:
            manuais[aid] = row["Posição"]
    if manuais:
        st.success(f"{len(manuais)} correção(ões) manual(is) nesta sessão.")
        st.download_button("⬇️ Baixar correções (CSV)", po.manuais_para_csv(manuais), file_name="tche-scout-posicoes-manuais.csv",
                           mime="text/csv", key="pos_dl")
    pesq = pos_tab[pos_tab["fonte"].fillna("").str.startswith("Fonte aberta")]
    if len(pesq):
        st.markdown("#### Posições pesquisadas em fontes abertas")
        v = pesq.merge(dl.atletas()[["atleta_id", "nome", "equipe_principal"]], on="atleta_id", how="left")
        st.dataframe(v[["nome", "equipe_principal", "posicao", "fonte", "confianca", "obs_pesquisa", "url"]].rename(
            columns={"nome": "Atleta", "equipe_principal": "Time", "posicao": "Posição", "fonte": "Fonte", "confianca": "Confiança (%)",
                     "obs_pesquisa": "Observação", "url": "Link"}), hide_index=True, width="stretch",
            column_config={"Link": st.column_config.LinkColumn("Link", display_text="abrir")})

rodape()
