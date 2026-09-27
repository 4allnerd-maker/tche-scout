"""Interface de posições: mostra só o que a base conhece e avisa onde a posição ainda não está confirmada.
Correção local: o usuário ajusta a posição no painel do time e ela vale nesta visita (inclusive no PDF)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import data_loader as dl
import posicoes as po

AVISO = ("**Sobre as posições:** parte dos atletas já tem a posição incluída automaticamente (goleiros pela súmula, posição provável "
         "pela camisa e posição confirmada em fonte aberta). Os demais ainda **não têm posição confirmada**. Estamos atualizando a base "
         "toda semana, e a cobertura vai melhorar com o tempo.")

STATUS_CONFIRMADA = "Confirmada"
STATUS_PROVAVEL = "Provável (pela camisa)"
STATUS_NAO = "Não confirmada"


def status(fonte) -> str:
    f = str(fonte or "")
    if f.startswith("Súmula") or f.startswith("Fonte aberta") or f.startswith("Manual"):
        return STATUS_CONFIRMADA
    if f.startswith("Inferida"):
        return STATUS_PROVAVEL
    return STATUS_NAO


def _rotulo(r) -> str:
    st_ = r["status"]
    if st_ == STATUS_CONFIRMADA:
        return r["posicao"]
    if st_ == STATUS_PROVAVEL:
        return f"{r['posicao']} (provável)"
    return "Não confirmada"


def manuais() -> dict:
    return st.session_state.setdefault("posicoes_manuais", {})


def tabela_final() -> pd.DataFrame:
    """Posições da base + correções feitas nesta visita. Colunas extras: status e exibicao."""
    t = dl.posicoes()
    if t.empty:
        t = pd.DataFrame(columns=["atleta_id", "posicao", "zona", "fonte", "confianca", "camisa_principal", "url", "obs_pesquisa"])
    t = po.aplicar_manuais(t, manuais())
    t["status"] = t["fonte"].map(status)
    t["exibicao"] = t.apply(_rotulo, axis=1) if len(t) else pd.Series(dtype=str)
    return t


def aviso() -> None:
    st.info(AVISO)


def editor_time(elenco: pd.DataFrame, chave: str) -> None:
    """elenco: colunas atleta_id, Atleta, Jogos. Permite corrigir a posição dos atletas do time (vale só nesta visita)."""
    if elenco is None or elenco.empty:
        return
    tab = tabela_final().set_index("atleta_id")
    e = elenco[["atleta_id", "Atleta", "Jogos"]].copy()
    e["Posição atual"] = e["atleta_id"].map(tab["exibicao"]).fillna("Não confirmada")
    e["Corrigir posição"] = e["atleta_id"].map(manuais()).fillna("")
    e = e.set_index("atleta_id")
    editado = st.data_editor(
        e, hide_index=True, width="stretch", key=f"ed_pos_{chave}", disabled=["Atleta", "Jogos", "Posição atual"],
        column_config={"Corrigir posição": st.column_config.SelectboxColumn("Corrigir posição", options=[""] + po.POSICOES, width="medium"),
                       "Jogos": st.column_config.NumberColumn(width="small")})
    m = manuais()
    for aid, row in editado.iterrows():
        if row["Corrigir posição"]:
            m[aid] = row["Corrigir posição"]
        elif aid in m:
            del m[aid]
    n = sum(1 for a in e.index if a in m)
    if n:
        st.caption(f"✅ {n} posição(ões) ajustada(s) por você. Vale nesta visita (e no PDF que você gerar agora); "
                   "ao recarregar a página, volta ao padrão da base.")
    else:
        st.caption("Ajuste local: escolha a posição na coluna **Corrigir posição**. Vale nesta visita e entra no PDF; "
                   "ao recarregar a página, volta ao padrão da base.")
