"""Contato por WhatsApp só depois de se identificar: o número não fica no código nem na página —
é lido dos secrets do Streamlit (WHATSAPP_NUMERO) e só aparece depois que o formulário é preenchido."""

from __future__ import annotations

import os
import re
from urllib.parse import quote

import streamlit as st

from config import EMAIL_CONTATO

ASSUNTOS = ["Anunciar / patrocinar", "Relatório ou análise para meu clube", "Parceria / projeto",
            "Corrigir um dado", "Outro assunto"]


def _numero() -> str:
    try:
        n = st.secrets.get("WHATSAPP_NUMERO", "")
    except Exception:
        n = ""
    return re.sub(r"\D", "", n or os.environ.get("WHATSAPP_NUMERO", ""))


@st.dialog("Falar com o Tchê Scout")
def _janela() -> None:
    dados = st.session_state.get("_contato_dados")
    if dados:
        st.success(f"Obrigado, {dados['nome']}! Agora você pode chamar no WhatsApp.")
        numero = _numero()
        if numero:
            texto = (f"Olá! Sou {dados['nome']}"
                     + (f" ({dados['org']})" if dados["org"] else "")
                     + f". Assunto: {dados['assunto']}. Vim pelo Tchê Scout.")
            st.link_button("💬 Abrir conversa no WhatsApp", f"https://wa.me/{numero}?text={quote(texto)}",
                           type="primary", width="stretch")
        if EMAIL_CONTATO:
            st.caption(f"Prefere e-mail? {EMAIL_CONTATO}")
        return
    st.caption("Para liberar o contato por WhatsApp, identifique-se rapidinho. "
               "Seus dados são usados só para montar a mensagem e não ficam guardados no site.")
    with st.form("form_contato", border=False):
        nome = st.text_input("Seu nome *")
        org = st.text_input("Clube / empresa / veículo (opcional)")
        email = st.text_input("Seu e-mail *")
        assunto = st.selectbox("Assunto", ASSUNTOS)
        enviar = st.form_submit_button("Liberar contato", type="primary")
    if enviar:
        if len(nome.strip()) < 3 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
            st.error("Preencha seu nome e um e-mail válido.")
            return
        st.session_state["_contato_dados"] = {"nome": nome.strip(), "org": org.strip(), "assunto": assunto}
        st.rerun(scope="fragment")


def botao_contato(rotulo: str = "💬 Falar comigo", chave: str = "contato", **kw) -> None:
    if st.button(rotulo, key=f"btn_{chave}", **kw):
        _janela()
