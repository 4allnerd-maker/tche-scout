"""Reúne os números de um time (os mesmos da aba Análise) em um dicionário pronto para cards e relatório em PDF."""

from __future__ import annotations

import pandas as pd

import analise as an
import camisas as cm
import cards
import formacoes
import posicoes_ui as pui


def _limpa(t: str) -> str:
    return t.replace("**", "")


def contexto_time(time, jogos_sel, gols, cartoes, partidas, subs, comps, ano, mando="Todos", ultimos=0):
    d = an.jogos_do_time(jogos_sel, time, mando, int(ultimos))
    if d.empty:
        return None
    ids = set(d["jogo_id"])
    g = an.gols_do_time(gols, ids, time)
    ct = an.cartoes_do_time(cartoes, ids, time)
    el = an.elenco(partidas, ids, time)
    st_ = subs[subs["jogo_id"].isin(ids) & (subs["equipe"] == time)] if not subs.empty else subs
    liga = an.metricas_liga(jogos_sel, cartoes, mando)
    prim = an.primeiro_gol(d, g) if not g.empty else pd.DataFrame()
    quadro = an.quadro_intervalo(d)
    r = an.resumo(d)
    cont_res = an.resumo_continuidade(an.continuidade_onze(partidas, d, time))
    ins = [_limpa(t) for t in an.insights(time, d, g, ct, el, liga, prim, quadro, st_, cont_res)]

    faixas = an.por_faixa(g) if not g.empty else pd.DataFrame({"Faixa": an.FAIXAS, "Feitos": 0, "Sofridos": 0})
    tempos = an.por_tempo(g) if not g.empty else pd.DataFrame({"Tempo": ["1º tempo", "2º tempo"], "Feitos": 0, "Sofridos": 0})

    cf = d.groupby("mando").agg(Jogos=("jogo_id", "count"), V=("res", lambda s: (s == "V").sum()), E=("res", lambda s: (s == "E").sum()),
                                D=("res", lambda s: (s == "D").sum()), GP=("gp", "sum"), GC=("gc", "sum"), Pts=("pontos", "sum")).reset_index()
    cf["Pró/jogo"] = (cf["GP"] / cf["Jogos"]).round(2)
    cf["Contra/jogo"] = (cf["GC"] / cf["Jogos"]).round(2)
    cf["Aprov. (%)"] = (cf["Pts"] / (cf["Jogos"] * 3) * 100).round(1)
    cf = cf.rename(columns={"mando": "Mando"})[["Mando", "Jogos", "V", "E", "D", "GP", "GC", "Pró/jogo", "Contra/jogo"]]

    ps = pd.DataFrame()
    if not prim.empty:
        linhas = []
        for rot, chave in (("Marca primeiro", "Pró"), ("Sofre primeiro", "Contra"), ("Sem gols", "Sem gols")):
            x = prim[prim["primeiro"] == chave]
            linhas.append({"Situação": rot, "Jogos": len(x), "Vitórias": int((x.res == "V").sum()), "Empates": int((x.res == "E").sum()),
                           "Derrotas": int((x.res == "D").sum())})
        ps = pd.DataFrame(linhas)

    if not el.empty:
        _pos = pui.tabela_final().set_index("atleta_id")
        el2 = el.copy()
        el2["Posição"] = el2["atleta_id"].map(_pos["exibicao"]).fillna("Não confirmada")
        elenco_top = el2.head(16)[["Atleta", "Posição", "Jogos", "Titular", "Minutos", "Gols", "Amarelos", "Vermelhos"]]
    else:
        elenco_top = el
    form_res = formacoes.resumo_por_formacao(d, time)

    am = int((ct["tipo"] == "amarelo").sum()) if not ct.empty else 0
    vm = int((ct["tipo"] == "vermelho").sum()) if not ct.empty else 0
    dir_ = int((ct.get("detalhe", pd.Series(dtype=str)) == "Cartão Vermelho Direto").sum()) if not ct.empty else 0
    cart = {"amarelos": am, "vermelhos": vm, "amarelos_jogo": am / r["J"], "diretos": dir_, "segundo_amarelo": vm - dir_}

    jj = d.sort_values("data", ascending=False).copy()
    jj["Data"] = jj["data"].dt.strftime("%d/%m/%y")
    jj["Placar"] = jj["gp"].astype(str) + " x " + jj["gc"].astype(str)
    jogos_pdf = pd.DataFrame({"Data": jj["Data"], "Mando": jj["mando"], "Rodada": jj["rodada"].fillna("").astype(str),
                              "Adversário": jj["adversario"], "GP": jj["gp"], "GC": jj["gc"],
                              "GP 1ºT": jj["gp1"].map(lambda v: "" if pd.isna(v) else int(v)),
                              "GC 1ºT": jj["gc1"].map(lambda v: "" if pd.isna(v) else int(v)), "Res.": jj["res"]})
    campos = campos_taticos(time, d, partidas)
    return {"time": time, "campos": campos, "d": d, "g": g, "r": r, "forma": list(d["res"]), "insights": ins, "faixas": faixas, "tempos": tempos,
            "primeiro": ps, "quadro": quadro, "casa_fora": cf, "elenco": elenco_top, "cartoes": cart, "jogos": jogos_pdf,
            "comps": comps, "ano": ano, "recorte": mando + (f" · últimos {int(ultimos)} jogos" if ultimos else ""),
            "liga": liga, "elenco_full": el, "formacoes": form_res}


def _esc_time(partidas, jogo_id, time):
    return partidas[(partidas["jogo_id"] == jogo_id) & (partidas["equipe"] == time)]


def campos_taticos(time, d, partidas):
    """Campos para o PDF: última escalação e onze mais utilizado. Usa a formação registrada manualmente, se houver;
    senão, a leitura automática pela numeração de camisa (que NÃO é a formação real)."""
    out = []
    ultimo = d.iloc[-1]
    esc = _esc_time(partidas, ultimo["jogo_id"], time)
    if not esc.empty and esc["titular"].sum() >= 9:
        form, _ = formacoes.obter(ultimo["jogo_id"], time)
        pos = cm.layout_por_formacao(esc, form) if form else None
        if pos is not None:
            legenda = (f"Formação {form} informada manualmente. Os atletas foram distribuídos nas linhas pela posição típica de "
                       "cada camisa. Dado digitado, não verificado.")
            titulo_f = f"Formação informada: {form}"
        else:
            pos = cm.posicoes_no_campo(esc)
            pn = cm.padrao_de_numeracao(esc)
            aviso_form = f" (a formação '{form}' informada não fecha com 10 jogadores de linha)" if form else ""
            legenda = (f"Leitura automática pela numeração de camisa (padrão de numeração: {pn['nivel'].lower()}){aviso_form}. "
                       "NÃO é a formação tática real: a súmula não informa o desenho.")
            titulo_f = "Leitura pela numeração"
        out.append({"titulo": f"Última escalação — {ultimo['data']:%d/%m/%Y} vs {ultimo['adversario']} ({ultimo['gp']}x{ultimo['gc']})",
                    "subtitulo": titulo_f, "png": cards.campo_png(pos), "legenda": legenda})

    # onze mais utilizado (maior número de titularidades)
    ids = set(d["jogo_id"])
    tit = partidas[(partidas["equipe"] == time) & (partidas["titular"]) & (partidas["jogo_id"].isin(ids))]
    if len(tit):
        cont = tit.groupby("atleta_id").size().sort_values(ascending=False)
        base_ids = list(cont.head(11).index)
        fix = cm.numeracao_dos_atletas(partidas[partidas["jogo_id"].isin(ids) & (partidas["equipe"] == time)])
        fix = fix.set_index("atleta_id")
        linhas = []
        for aid in base_ids:
            r = tit[tit["atleta_id"] == aid].iloc[-1]
            linhas.append({"numero": fix.loc[aid, "camisa_principal"] if aid in fix.index else r["numero"], "nome": r["nome"],
                           "titular": True, "goleiro": bool(tit[tit["atleta_id"] == aid]["goleiro"].mean() > 0.5)})
        base_df = pd.DataFrame(linhas)
        if len(base_df) >= 9:
            regs = formacoes.estado()
            regs = regs[(regs["equipe"] == time) & (regs["jogo_id"].isin(ids))]
            form_base = regs["formacao"].mode().iloc[0] if len(regs) else ""
            pos = cm.layout_por_formacao(base_df, form_base) if form_base else None
            if pos is not None:
                legenda = f"Formação mais registrada por você ({form_base}), com os 11 atletas mais utilizados como titulares."
                sub = f"Formação informada: {form_base}"
            else:
                pos = cm.posicoes_no_campo(base_df)
                legenda = ("Os 11 atletas com mais titularidades, posicionados pela camisa mais usada por cada um (convenção brasileira). "
                           "NÃO é a formação tática real.")
                sub = "Leitura pela numeração"
            out.append({"titulo": f"Onze mais utilizado ({len(d)} jogos)", "subtitulo": sub, "png": cards.campo_png(pos),
                        "legenda": legenda})
    return out
