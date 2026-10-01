import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data_loader as dl
import escudos as es
import estado
import leiame
import camisas as cm
import posicoes as po
import posicoes_ui as pui
import stats
from theme import COR, cabecalho, rodape
from ui import linha_selecionada, tabela

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

estado.barra_limpar("jog")
f1, f2, f3, f4 = st.columns(4)
categoria = f1.selectbox("Categoria", sorted(p["categoria"].unique(), reverse=True), key="jog_cat")
p = p[p["categoria"] == categoria]
anos = f2.multiselect("Ano", sorted(p["ano"].unique(), reverse=True), placeholder="Todos os anos", key="jog_ano")
p = p[p["ano"].isin(anos)] if anos else p
comps = f3.multiselect("Competição", sorted(p["competicao_nome"].unique()), placeholder="Todas", key="jog_comp")
if comps:
    p = p[p["competicao_nome"].isin(comps)]
times = f4.multiselect("Time", sorted(p["equipe"].unique()), placeholder="Todos", key="jog_time")
if times:
    p = p[p["equipe"].isin(times)]

g1, g2, g3 = st.columns([2, 1, 1])
busca = g1.text_input("Buscar atleta", placeholder="Digite parte do nome ou apelido…", key="jog_busca")
posicao = g2.selectbox("Posição / zona", ["Todas", "Goleiro", "Defesa", "Meio", "Ataque", "Não confirmada"], key="jog_pos")
so_atuaram = g3.toggle("Só quem atuou", value=True, help="Esconde atletas que ficaram apenas no banco.", key="jog_atuou")

painel = stats.painel_atletas(p).drop(columns=["Posição"]).merge(dl.atletas()[["atleta_id", "nome_completo"]], on="atleta_id", how="left")
pos_tab = pui.tabela_final()
painel = painel.merge(pos_tab[["atleta_id", "posicao", "zona", "fonte", "confianca", "url", "obs_pesquisa", "status", "exibicao"]],
                      on="atleta_id", how="left")
painel["Posição"] = painel["exibicao"].fillna("Não confirmada")
painel["Status da posição"] = painel["status"].fillna(pui.STATUS_NAO)
painel = painel.rename(columns={"nome_completo": "Nome completo"})
if painel.empty:
    st.info("Nenhum atleta para essa seleção.")
    st.stop()
if busca:
    painel = painel[painel["Atleta"].str.contains(busca, case=False, na=False)
                    | painel["Nome completo"].str.contains(busca, case=False, na=False)]
if posicao != "Todas":
    if posicao == "Não confirmada":
        painel = painel[painel["status"].fillna(pui.STATUS_NAO) == pui.STATUS_NAO]
    else:
        painel = painel[painel["zona"] == posicao]
if so_atuaram:
    painel = painel[painel["Jogos"] > 0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Atletas", len(painel))
k2.metric("Gols", int(painel["Gols"].sum()))
k3.metric("Cartões amarelos", int(painel["Amarelos"].sum()))
k4.metric("Cartões vermelhos", int(painel["Vermelhos"].sum()))

def _render_ficha(escolhido, chave: str = "ficha") -> None:
    linha = painel[painel["atleta_id"] == escolhido].iloc[0]
    st.markdown(f'{es.img_tag(linha["Time"], 34)} &nbsp; **{linha["Atleta"]}** — {linha["Time"]}',
               unsafe_allow_html=True)
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
    out_v = es.inserir_coluna(out, "Time")
    tabela(out_v, chave, ordenar_por="Data", altura=360, imagem_col="Escudo")


@st.dialog("Ficha rápida do atleta")
def _dialog_ficha() -> None:
    aid = st.session_state.get("_jog_dialog_id")
    if aid is None or aid not in set(painel["atleta_id"]):
        st.info("Selecione um atleta na tabela.")
        return
    _render_ficha(aid, chave="ficha_dialog")


pui.aviso()
tab_tab, tab_graf, tab_ficha, tab_cam, tab_pos = st.tabs(["Tabela de atletas", "Gráficos", "Ficha do atleta", "👕 Camisas", "📍 Posições"])

with tab_tab:
    cols = ["Atleta", "Nome completo", "Time", "Times", "Posição", "Status da posição", "Relacionado", "Jogos", "Titular", "Entrou", "Banco", "Substituído",
            "Minutos", "Gols", "G.C.", "Min/gol", "Amarelos", "Vermelhos", "atleta_id"]
    painel_v = es.inserir_coluna(painel[cols], "Time")
    tabela(painel_v, "atl", ordenar_por="Gols", fixar="Atleta", altura=520, exportar="tche-scout-atletas",
           imagem_col="Escudo", selecionavel=True, ocultar=["atleta_id"],
           ajuda={"Times": "Em quantos times o atleta atuou na seleção", "Relacionado": "Jogos em que constou na súmula",
                  "Jogos": "Titular + entrou durante o jogo", "Entrou": "Entrou como substituto",
                  "Banco": "Relacionado e não utilizado", "Substituído": "Saiu por substituição",
                  "G.C.": "Gols contra", "Min/gol": "Minutos jogados por gol marcado"})
    sel = linha_selecionada("atl")
    bcol, ccol = st.columns([1, 3])
    if bcol.button("👁️ Ver ficha rápida", disabled=sel is None, type="primary", key="jog_abrir_ficha"):
        st.session_state["_jog_dialog_id"] = sel["atleta_id"]
        _dialog_ficha()
    ccol.caption("Clique numa linha da tabela pra selecionar o atleta e ver a ficha num painel, sem sair da página.")
    st.caption("Minutos calculados a partir de titularidade, substituições e expulsões (jogo de 90 min). "
               "Assistências não constam nas súmulas oficiais. Nomes completos podem aparecer cortados: é como a FGF os publica.")

with tab_graf:
    top = painel.sort_values("Gols", ascending=False).head(15).iloc[::-1]
    fig = go.Figure(go.Bar(x=top["Gols"], y=top["Atleta"] + " (" + top["Time"] + ")", orientation="h",
                           marker_color=COR["verde"]))
    fig.update_layout(title="Maiores artilheiros", height=460, margin=dict(l=0, r=0, t=40, b=0), plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")
    disc = painel.assign(Total=painel["Amarelos"] + painel["Vermelhos"] * 2).sort_values("Total", ascending=False).head(15).iloc[::-1]
    fig2 = go.Figure()
    fig2.add_bar(x=disc["Amarelos"], y=disc["Atleta"] + " (" + disc["Time"] + ")", orientation="h", name="Amarelos",
                 marker_color=COR["dourado"])
    fig2.add_bar(x=disc["Vermelhos"], y=disc["Atleta"] + " (" + disc["Time"] + ")", orientation="h", name="Vermelhos",
                 marker_color=COR["vermelho"])
    fig2.update_layout(title="Mais cartões", barmode="stack", height=460, margin=dict(l=0, r=0, t=40, b=0), plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, width="stretch")

with tab_ficha:
    opcoes = painel.assign(rotulo=painel["Atleta"] + " — " + painel["Time"]).set_index("atleta_id")["rotulo"]
    if opcoes.empty:
        st.info("Nenhum atleta para exibir.")
    else:
        escolhido = st.selectbox("Atleta", opcoes.index, format_func=lambda a: opcoes[a], key="jog_ficha")
        _render_ficha(escolhido)

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
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor="rgba(0,0,0,0)",
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
        f_v = es.inserir_coluna(f[["Atleta", "Time", "Camisa principal", "% dos jogos com essa camisa", "Nº de camisas diferentes",
                                  "Zona (convenção)", "Jogos"]], "Time")
        tabela(f_v, "camfixa", ordenar_por="Jogos", fixar="Atleta", altura=360, imagem_col="Escudo")

with tab_pos:
    st.markdown("A súmula não traz a posição do atleta. A base de posições é montada em camadas e **melhora a cada semana**:")
    st.markdown(
        "- **Confirmada** — goleiros (a súmula marca quem é goleiro) e atletas cuja posição foi encontrada em fonte aberta "
        "(com o link da fonte, abaixo).  \n"
        "- **Provável (pela camisa)** — estimada pela numeração tradicional do futebol brasileiro. É uma pista: pode errar "
        "(a camisa 5 nem sempre é volante).  \n"
        "- **Não confirmada** — ainda não sabemos. O Tchê Scout não inventa: a posição aparece como *Não confirmada*.")
    cob = painel["Status da posição"].value_counts().rename_axis("Situação").reset_index(name="Atletas")
    cob["%"] = (cob["Atletas"] / cob["Atletas"].sum() * 100).round(1)
    st.markdown("#### Cobertura na seleção atual")
    st.dataframe(cob, hide_index=True, width="stretch")
    st.markdown("#### Posições confirmadas em fontes abertas")
    pesq = pos_tab[pos_tab["fonte"].fillna("").str.startswith("Fonte aberta")]
    if len(pesq):
        v = pesq.merge(dl.atletas()[["atleta_id", "nome", "equipe_principal"]], on="atleta_id", how="left")
        st.dataframe(v[["nome", "equipe_principal", "posicao", "fonte", "obs_pesquisa", "url"]].rename(
            columns={"nome": "Atleta", "equipe_principal": "Time", "posicao": "Posição", "fonte": "Fonte",
                     "obs_pesquisa": "Observação", "url": "Link"}), hide_index=True, width="stretch",
            column_config={"Link": st.column_config.LinkColumn("Link", display_text="abrir")})
    else:
        st.caption("Ainda não há posições de fonte aberta.")
    st.caption("Vai analisar um time e quer ajustar as posições antes de gerar o PDF? Faça isso na aba **Análise → Elenco** "
               "ou em **Relatórios e cards**: a correção vale na sua visita.")

rodape()
