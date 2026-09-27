import io
import zipfile

import pandas as pd
import streamlit as st

import cards
import contexto
import data_loader as dl
import estado
import formacoes
import posicoes_ui as pui
import leiame
import relatorio
import stats
from config import AUTOR, AUTOR_FUNCAO
from theme import cabecalho, rodape

cabecalho("🖼️ Relatórios e cards", "Crie imagens prontas para as redes sociais e um relatório de scout em PDF — com um clique.")
leiame.mostrar("relatorios")

if not dl.tem_dados():
    st.warning("Base de dados ainda não gerada.")
    st.stop()

jogos_all = dl.jogos()
gols_all, cartoes_all, partidas_all, subs_all = dl.gols(), dl.cartoes(), dl.partidas(), dl.substituicoes()

estado.barra_limpar("rc")
with st.container(border=True):
    f1, f2, f3, f4 = st.columns([1, 1, 2, 1.4])
    cats = sorted(jogos_all["categoria"].unique(), reverse=True)
    categoria = f1.selectbox("Categoria", cats, key="rc_cat")
    j = jogos_all[jogos_all["categoria"] == categoria]
    ano = f2.selectbox("Ano", sorted(j["ano"].unique(), reverse=True), index=None, placeholder="Escolha o ano", key="rc_ano")
    j = j[j["ano"] == ano] if ano is not None else j.iloc[0:0]
    comps_disp = sorted(j["competicao_nome"].unique())
    comp = f3.selectbox("Competição", comps_disp, index=None, placeholder="Escolha a competição", key="rc_comp", disabled=ano is None)
    j = j[j["competicao_nome"] == comp] if comp is not None else j.iloc[0:0]
    fases = sorted(j["fase_nome"].dropna().unique())
    fase = f4.selectbox("Fase", ["Todas"] + fases, key="rc_fase", disabled=comp is None)
    if fase != "Todas":
        j = j[j["fase_nome"] == fase]
    times = sorted(set(j["time_mandante"]) | set(j["time_visitante"])) if len(j) else []
    destaque = st.selectbox("Time em destaque (opcional)", ["—"] + times, key="rc_dest", disabled=comp is None)
    destaque = None if destaque == "—" else destaque

if ano is None or comp is None:
    st.info("👆 Escolha o **ano** e a **competição** para criar cards e relatórios.")
    rodape()
    st.stop()

rotulo = f"{comp} {ano}"
tag_comp = "".join(ch for ch in comp.title() if ch.isalnum())


def baixar(imgs: list[bytes], nome: str, chave: str):
    for i, im in enumerate(imgs, 1):
        st.image(im, width="stretch")
        st.download_button(f"⬇️ Baixar PNG {i}/{len(imgs)}", im, file_name=f"{nome}-{i}.png", mime="image/png", key=f"{chave}_{i}")
    if len(imgs) > 1:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for i, im in enumerate(imgs, 1):
                z.writestr(f"{nome}-{i}.png", im)
        st.download_button("⬇️ Baixar todos (ZIP)", buf.getvalue(), file_name=f"{nome}.zip", mime="application/zip", key=f"{chave}_zip")


tab_cards, tab_pdf = st.tabs(["🖼️ Cards para redes sociais", "📄 Relatório do time (PDF)"])

# ------------------------------------------------------------------ cards
with tab_cards:
    tipo = st.radio("Tipo de card", ["Resultados da rodada", "Artilheiros", "Classificação", "Raio-X do time"], horizontal=True,
                    key="rc_tipo")
    real = j[j["situacao"].isin(["Realizado", "W.O."])]

    if tipo == "Resultados da rodada":
        rodadas = sorted([x for x in real["rodada"].dropna().unique()], key=lambda v: int(v) if str(v).isdigit() else 999)
        if not rodadas:
            st.info("Essa competição não tem rodadas numeradas — escolha outra ou use o filtro de fase.")
        else:
            rod = st.selectbox("Rodada", rodadas, index=len(rodadas) - 1, format_func=lambda r: f"Rodada {r}", key="rc_rod")
            sel = real[real["rodada"] == rod].sort_values("data")
            st.caption(f"{len(sel)} jogos na rodada {rod}.")
            imgs = cards.card_resultados(sel, "Resultados da rodada", f"{rotulo} · Rodada {rod}", destaque)
            baixar(imgs, f"tche-scout-resultados-rodada-{rod}", "res")
            linhas = "\n".join(f"{r.time_mandante} {int(r.gols_mandante)} x {int(r.gols_visitante)} {r.time_visitante}" for r in sel.itertuples())
            st.markdown("**Legenda sugerida**")
            st.code(f"⚽ Resultados da rodada {rod} — {rotulo}\n\n{linhas}\n\n📊 Dados: súmulas oficiais da FGF\n"
                    f"tchescout.streamlit.app\n#TchêScout #FutebolGaúcho #{tag_comp}", language=None)

    elif tipo == "Artilheiros":
        esc = st.radio("Escopo", ["Geral da competição", "Da rodada"], horizontal=True, key="rc_art_esc")
        top = st.slider("Quantos atletas", 5, 12, 10, key="rc_art_top")
        p = partidas_all.merge(j[["jogo_id", "rodada"]], on="jogo_id")
        sub_t = f"{rotulo}"
        if esc == "Da rodada":
            rodadas = sorted(p["rodada"].dropna().unique(), key=lambda v: int(v) if str(v).isdigit() else 999)
            rod = st.selectbox("Rodada", rodadas, index=len(rodadas) - 1 if rodadas else 0, key="rc_art_rod") if rodadas else None
            if rod is not None:
                p = p[p["rodada"] == rod]
                sub_t = f"{rotulo} · Rodada {rod}"
        art = stats.artilharia(p, top)
        if art.empty:
            st.info("Sem gols nessa seleção.")
        else:
            baixar([cards.card_artilheiros(art, "Artilheiros" if esc.startswith("Geral") else "Artilheiros da rodada", sub_t, top)],
                   "tche-scout-artilheiros", "art")
            lista = "\n".join(f"{i}. {r.Atleta} ({r.Time}) — {int(r.Gols)}" for i, r in enumerate(art.itertuples(), 1))
            st.markdown("**Legenda sugerida**")
            st.code(f"🥇 Artilheiros — {sub_t}\n\n{lista}\n\n📊 tchescout.streamlit.app\n#TchêScout #FutebolGaúcho #{tag_comp}", language=None)

    elif tipo == "Classificação":
        top = st.slider("Quantos times", 6, 16, 12, key="rc_cls_top")
        cl = stats.classificacao(j)
        if cl.empty:
            st.info("Sem jogos nessa seleção.")
        else:
            baixar([cards.card_classificacao(cl, "Classificação", rotulo + ("" if fase == "Todas" else f" · {fase}"), destaque, top)],
                   "tche-scout-classificacao", "cls")
            lista = "\n".join(f"{int(r.Pos)}º {r.Time} — {int(r.P)} pts" for r in cl.head(top).itertuples())
            st.markdown("**Legenda sugerida**")
            st.code(f"🏆 Classificação — {rotulo}\n\n{lista}\n\n📊 tchescout.streamlit.app\n#TchêScout #FutebolGaúcho #{tag_comp}", language=None)

    else:  # Raio-X
        time = st.selectbox("Time", times, index=None, placeholder="Escolha o time", key="rc_rx_time")
        ctx = contexto.contexto_time(time, j, gols_all, cartoes_all, partidas_all, subs_all, [comp], ano) if time is not None else None
        if ctx is None:
            st.info("Escolha um time com jogos com súmula para gerar o raio-X.")
        else:
            r = ctx["r"]
            kp = [("JOGOS", f"{r['J']}"), ("APROVEITAMENTO", f"{r['aprov']}%".replace(".", ",")),
                  ("GOLS PRÓ/JOGO", f"{r['gp_j']}".replace(".", ",")), ("GOLS CONTRA/JOGO", f"{r['gc_j']}".replace(".", ",")),
                  ("SALDO DE GOLS", f"{r['SG']:+d}"), ("JOGOS SEM SOFRER", f"{r['sem_sofrer']}")]
            destaques = [t for t in ctx["insights"] if t.startswith(("Quando marca", "Abre o placar", "Referência", "Ataque", "Defesa"))][:3] \
                or ctx["insights"][:3]
            baixar([cards.card_time(time, f"{rotulo} · {r['J']} jogos", kp, ctx["forma"], ctx["faixas"], destaques)],
                   f"tche-scout-raio-x-{time}", "rx")

# ------------------------------------------------------------------ PDF
with tab_pdf:
    st.markdown("Relatório de scout do time com resumo, insights, gols por minuto, quem abre o placar, elenco, disciplina e jogo a jogo. "
                "Pronto para enviar à comissão técnica.")
    c1, c2, c3 = st.columns([2, 1.5, 1.5])
    time_r = c1.selectbox("Time", times, index=None, placeholder="Escolha o time", key="rc_pdf_time")
    mando = c2.segmented_control("Mando", ["Todos", "Casa", "Fora"], default="Todos", key="rc_pdf_mando") or "Todos"
    ult = c3.number_input("Últimos N jogos (0 = todos)", 0, 60, 0, key="rc_pdf_ult")
    if time_r is not None:
        _pre = contexto.contexto_time(time_r, j, gols_all, cartoes_all, partidas_all, subs_all, [comp], ano, mando, ult)
        if _pre is not None:
            _ult = _pre["d"].iloc[-1]
            st.markdown("#### 🧩 Campo tático do relatório")
            st.caption(f"Último jogo: {_ult['data']:%d/%m/%Y} · {_ult['mando']} vs {_ult['adversario']} ({_ult['gp']}x{_ult['gc']}). "
                       "Se você assistiu ao jogo, informe a formação. Se deixar em branco, o PDF usa a **leitura automática pela "
                       "numeração de camisa** (que **não** é a formação real, pois a súmula não informa o desenho).")
            _atual, _ = formacoes.obter(_ult["jogo_id"], time_r)
            _ops = formacoes.OPCOES + ([_atual] if _atual and _atual not in formacoes.OPCOES else [])
            _f = st.selectbox("Formação do último jogo (opcional)", _ops, index=_ops.index(_atual) if _atual in _ops else 0,
                              key=f"rc_form_{_ult['jogo_id']}_{time_r}", format_func=lambda x: x or "— usar leitura automática —")
            formacoes.salvar(_ult["jogo_id"], time_r, _f, "")
            _campos = contexto.campos_taticos(time_r, _pre["d"], partidas_all)
            if _campos:
                _cols = st.columns(len(_campos))
                for _c, _cp in zip(_cols, _campos):
                    _c.image(_cp["png"], caption=f"{_cp['titulo']} — {_cp['subtitulo']}", width="stretch")
                    _c.caption(_cp["legenda"])
                st.caption("Este campo entra no PDF, na página **Escalação e campo tático**.")
    with st.expander("✏️ Conferir e ajustar as posições do elenco antes de gerar (vale só para esta visita)"):
        pui.aviso()
        _ctx = contexto.contexto_time(time_r, j, gols_all, cartoes_all, partidas_all, subs_all, [comp], ano, mando, ult) if time_r is not None else None
        if _ctx is not None and not _ctx["elenco_full"].empty:
            pui.editor_time(_ctx["elenco_full"][["atleta_id", "Atleta", "Jogos"]], f"rc_{time_r}")
        else:
            st.caption("Sem elenco para ajustar nessa seleção.")
    if st.button("📄 Gerar relatório em PDF", type="primary", key="rc_pdf_go", disabled=time_r is None):
        ctx = contexto.contexto_time(time_r, j, gols_all, cartoes_all, partidas_all, subs_all, [comp], ano, mando, ult)
        if ctx is None:
            st.warning("Esse time ainda não tem jogos com súmula nessa seleção.")
        else:
            with st.spinner("Montando o PDF..."):
                ctx.update(autor=AUTOR, funcao=AUTOR_FUNCAO)
                st.session_state["rc_pdf_bytes"] = (relatorio.gerar_pdf_time(ctx), f"tche-scout-relatorio-{time_r}.pdf")
    if "rc_pdf_bytes" in st.session_state:
        pdf_b, nome = st.session_state["rc_pdf_bytes"]
        st.success(f"Relatório pronto: {nome}")
        st.download_button("⬇️ Baixar o PDF", pdf_b, file_name=nome, mime="application/pdf", key="rc_pdf_dl")

rodape()
