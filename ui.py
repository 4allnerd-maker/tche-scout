"""Componentes de interface reutilizáveis (tabelas com ordenação explícita, chips, etc.)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

CRESC = "↑ Crescente"
DECRESC = "↓ Decrescente"


def _config_colunas(df: pd.DataFrame, fixar: str | None, ajuda: dict | None, ocultar: list | None = None,
                     imagem: str | list[str] | None = None) -> dict:
    """Largura fixa por coluna: evita cabeçalhos espremidos/sobrepostos ao clicar para ordenar."""
    ajuda = ajuda or {}
    cfg = {}
    for i, col in enumerate(df.columns):
        if ocultar and col in ocultar:
            cfg[col] = None
            continue
        serie = df[col]
        imgs = set(imagem) if isinstance(imagem, (list, tuple, set)) else ({imagem} if imagem else set())
        # com coluna de escudo, não fixamos nenhuma coluna: fixar só o nome (sem o escudo) descola os dois
        # visualmente (o "pinned" do Streamlit não preserva a ordem das colunas fixadas de forma previsível)
        comum = dict(help=ajuda.get(col), pinned=(col == fixar and not imgs) or None)
        comum = {k: v for k, v in comum.items() if v is not None}
        if col in imgs:
            cfg[col] = st.column_config.ImageColumn(" ", width="small")
        elif pd.api.types.is_bool_dtype(serie):
            cfg[col] = st.column_config.CheckboxColumn(col, width="small", **comum)
        elif pd.api.types.is_numeric_dtype(serie):
            inteira = serie.dropna().apply(lambda x: float(x).is_integer()).all() if len(serie.dropna()) else True
            cfg[col] = st.column_config.NumberColumn(col, width="small", format="%d" if inteira else "%.2f", **comum)
        elif pd.api.types.is_datetime64_any_dtype(serie):
            cfg[col] = st.column_config.DateColumn(col, width="small", format="DD/MM/YYYY", **comum)
        else:
            maior = int(serie.fillna("").astype(str).str.len().max() or 0) if len(serie) else 0
            cfg[col] = st.column_config.TextColumn(col, width="large" if maior > 26 else "medium", **comum)
    return cfg


def tabela(df: pd.DataFrame, chave: str, ordenar_por: str | None = None, crescente: bool = False,
           altura: int | None = None, fixar: str | None = None, ajuda: dict | None = None,
           exportar: str | None = None, com_controles: bool = True, selecionavel: bool = False,
           ocultar: list | None = None, imagem_col: str | list[str] | None = None) -> pd.DataFrame:
    """Mostra a tabela com seletores visíveis de 'Ordenar por' e 'Ordem'.
    `imagem_col`: nome (ou lista de nomes) de coluna com data-URIs de imagem (ex.: escudo do time) —
    vira coluna estreita sem texto, fora do seletor de ordenação. `chave` precisa ser única na página.
    Retorna o DataFrame já ordenado."""
    if df is None or df.empty:
        st.info("Nada para mostrar com os filtros atuais.")
        return df
    _imgs = set(imagem_col) if isinstance(imagem_col, (list, tuple, set)) else ({imagem_col} if imagem_col else set())
    colunas = [c for c in df.columns if not (ocultar and c in ocultar) and c not in _imgs]
    if com_controles:
        c1, c2, c3 = st.columns([2, 2, 3])
        padrao = ordenar_por if ordenar_por in colunas else colunas[0]
        col = c1.selectbox("Ordenar por", colunas, index=colunas.index(padrao), key=f"{chave}_col")
        ordem = c2.segmented_control("Ordem", [DECRESC, CRESC], default=CRESC if crescente else DECRESC,
                                     key=f"{chave}_ordem", help="Escolha a coluna e o sentido da classificação.")
        c3.caption(f"{len(df)} linhas · dica: role para o lado para ver todas as colunas")
        df = df.sort_values(col, ascending=(ordem or (CRESC if crescente else DECRESC)) == CRESC,
                            kind="stable", na_position="last")
    kwargs = {"height": altura} if altura else {}
    if selecionavel:
        kwargs.update(on_select="rerun", selection_mode="single-row", key=f"{chave}_df")
    evento = st.dataframe(df, hide_index=True, width="stretch",
                          column_config=_config_colunas(df, fixar, ajuda, ocultar, imagem_col), **kwargs)
    if selecionavel:
        linhas = list(evento.selection.rows) if evento is not None and getattr(evento, "selection", None) else []
        st.session_state[f"{chave}_linha"] = df.iloc[linhas[0]] if linhas else None
    if exportar:
        st.download_button("⬇️ Baixar tabela (CSV)", df.to_csv(index=False, sep=";").encode("utf-8-sig"),
                           file_name=f"{exportar}.csv", mime="text/csv", key=f"{chave}_csv")
    return df


def chips_forma(resultados: list[tuple[str, str]]) -> str:
    """HTML com bolinhas V/E/D. `resultados` = [(letra, dica), ...] do mais antigo ao mais recente."""
    cores = {"V": "#0E6B3F", "E": "#F2B705", "D": "#C8102E"}
    txt = {"V": "#fff", "E": "#16241C", "D": "#fff"}
    itens = "".join(
        f'<span title="{dica}" style="display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;'
        f'border-radius:50%;background:{cores[l]};color:{txt[l]};font-weight:800;margin-right:6px;font-size:.9rem">{l}</span>'
        for l, dica in resultados)
    return f'<div style="margin:.2rem 0 .6rem 0">{itens}</div>'


def linha_selecionada(chave: str):
    """Linha (Series) selecionada numa tabela criada com selecionavel=True, ou None."""
    return st.session_state.get(f"{chave}_linha")


def abrir_jogo(jogo_id: str) -> None:
    """Leva para a aba Jogo & súmula já com o jogo escolhido."""
    st.session_state["jogo_id"] = str(jogo_id)
    st.session_state["_manter_jogo"] = True  # o roteador não apaga este pedido ao trocar de aba
    st.switch_page("pages/8_🧾_Jogo.py")
