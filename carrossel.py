"""Carrossel de classificações da página inicial: gira sozinho entre os campeonatos (estilo SofaScore),
com escudo, posição e pontos. Só CSS (sem JavaScript — o Streamlit não executa <script> em st.markdown)."""

from __future__ import annotations

import html

import pandas as pd

import escudos as es
import stats

# ordem de exibição: (nome da competição, rótulo curto)
COMPETICOES = [
    ("Gauchão", "Gauchão"),
    ("Gauchão Série A2", "Série A2"),
    ("Gauchão Série B", "Série B"),
    ("Copa FGF", "Copa FGF"),
    ("Gauchão Feminino", "Feminino"),
]
TOP_N = 6
SEGUNDOS_POR_SLIDE = 6


def _linha(pos: int, time: str, pts: int, j: int, sg: int, zona: str) -> str:
    cor_zona = {"g1": "#0E6B3F", "g2": "#F2B705", "rz": "#C8102E"}.get(zona, "transparent")
    nome = html.escape(str(time))
    return (
        f'<div style="display:flex;align-items:center;gap:.55rem;padding:.4rem .5rem;border-radius:8px;'
        f'background:{"#F3F6F1" if pos % 2 else "#fff"}">'
        f'<span style="width:4px;align-self:stretch;border-radius:2px;background:{cor_zona};flex:0 0 auto"></span>'
        f'<span style="width:1.3rem;color:#5B6B62;font-weight:700;font-size:.85rem;flex:0 0 auto">{pos}</span>'
        f'<img src="{es.data_uri(time, 64)}" alt="{nome}" style="width:22px;height:22px;object-fit:contain;'
        f'background:#fff;border-radius:50%;border:1px solid #DCE5DD;flex:0 0 auto">'
        f'<span style="flex:1 1 auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.88rem;'
        f'font-weight:600;color:#16241C">{nome}</span>'
        f'<span style="width:1.7rem;text-align:center;color:#5B6B62;font-size:.8rem;flex:0 0 auto;'
        f'margin-right:.35rem">{j}</span>'
        f'<span style="width:2.1rem;text-align:center;color:#5B6B62;font-size:.8rem;flex:0 0 auto;'
        f'margin-right:.35rem">{sg:+d}</span>'
        f'<span style="width:2rem;text-align:right;font-weight:800;color:#0A3D26;flex:0 0 auto">{pts}</span>'
        f"</div>"
    )


def _slide(comp: str, rotulo: str, jogos: pd.DataFrame, ano: int) -> str | None:
    j = jogos[(jogos["categoria"] == ("Feminino" if "Feminino" in comp else "Masculino")) &
              (jogos["ano"] == ano) & (jogos["competicao_nome"] == comp)]
    if j.empty:
        return None
    fases = sorted(j["fase_nome"].dropna().unique())
    if fases:
        j = j[j["fase_nome"] == fases[0]]
    tabela = stats.classificacao(j)
    if tabela.empty:
        return None
    tabela = tabela.head(TOP_N)
    n = len(tabela)
    linhas = "".join(
        _linha(int(r.Pos), r.Time, int(r.P), int(r.J), int(r.SG),
              "g1" if r.Pos == 1 else ("g2" if r.Pos <= 4 else ("rz" if r.Pos > n - 2 else "")))
        for r in tabela.itertuples())
    return (
        f'<div class="ts-slide">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.5rem">'
        f'<span style="font-family:\'Archivo Black\',Inter;color:#0A3D26;font-size:1.05rem">{html.escape(rotulo)}</span>'
        f'<span style="color:#5B6B62;font-size:.78rem">{ano} · J · SG · Pts</span></div>'
        f'{linhas}</div>'
    )


def widget(jogos: pd.DataFrame) -> str | None:
    """HTML do carrossel (card + slides). None se não houver classificação nenhuma para montar."""
    if jogos.empty:
        return None
    ano = int(jogos[jogos["categoria"] == "Masculino"]["ano"].max())
    slides = [s for comp, rot in COMPETICOES if (s := _slide(comp, rot, jogos, ano))]
    fem = jogos[jogos["categoria"] == "Feminino"]
    if not fem.empty:
        ano_fem = int(fem["ano"].max())
        s = _slide("Gauchão Feminino", "Feminino", jogos, ano_fem)
        if s and len(slides) < len(COMPETICOES):
            slides.append(s)
    if not slides:
        return None
    n = len(slides)
    total = n * SEGUNDOS_POR_SLIDE
    fatia = 100 / n
    dentro = max(1.0, fatia * 0.12)  # % do ciclo gasto no fade in/out
    css_slides = "\n".join(
        f".ts-carousel .ts-slide:nth-child({i + 1}) {{ animation-delay: {-(i * SEGUNDOS_POR_SLIDE)}s; }}"
        for i in range(n))
    css_pontos = "\n".join(
        f".ts-carousel .ts-dot:nth-child({i + 1}) {{ animation-delay: {-(i * SEGUNDOS_POR_SLIDE)}s; }}"
        for i in range(n))
    keyframes = f"""
    @keyframes tsCarrosselFade {{
      0% {{ opacity: 0; z-index: 1; }}
      {dentro:.2f}% {{ opacity: 1; z-index: 2; }}
      {fatia - dentro:.2f}% {{ opacity: 1; z-index: 2; }}
      {fatia:.2f}% {{ opacity: 0; z-index: 1; }}
      100% {{ opacity: 0; z-index: 1; }}
    }}
    @keyframes tsCarrosselDot {{
      0% {{ background: #DCE5DD; }}
      {dentro:.2f}% {{ background: #F2B705; }}
      {fatia - 0.5:.2f}% {{ background: #F2B705; }}
      {fatia:.2f}% {{ background: #DCE5DD; }}
      100% {{ background: #DCE5DD; }}
    }}
    """
    estilo = f"""
    <style>
    a.ts-carousel-link {{ text-decoration:none; color:inherit; display:block; }}
    .ts-carousel {{ position: relative; background:#fff; border:1px solid #DCE5DD; border-radius:12px;
      padding: 1rem 1.1rem .9rem 1.1rem; box-shadow: 0 1px 2px rgba(10,61,38,.05);
      transition: box-shadow .15s, transform .15s, border-color .15s; cursor: pointer; }}
    a.ts-carousel-link:hover .ts-carousel {{ box-shadow: 0 6px 18px rgba(10,61,38,.14); transform: translateY(-2px);
      border-color: #B9CBBD; }}
    .ts-carousel .ts-cta {{ display:flex; align-items:center; justify-content:space-between; margin-top:.7rem;
      padding-top:.6rem; border-top:1px solid #EEF2EE; color:#0E6B3F; font-weight:700; font-size:.85rem; }}
    .ts-carousel .ts-stage {{ position: relative; height: {40 + TOP_N * 34}px; }}
    .ts-carousel .ts-slide {{ position: absolute; inset: 0; opacity: 0;
      animation: tsCarrosselFade {total}s infinite; }}
    .ts-carousel .ts-dots {{ display:flex; gap:6px; justify-content:center; margin-top:.6rem; }}
    .ts-carousel .ts-dot {{ width:7px; height:7px; border-radius:50%; background:#DCE5DD;
      animation: tsCarrosselDot {total}s infinite; }}
    {css_slides}
    {css_pontos}
    {keyframes}
    </style>
    """
    pontos = "".join('<span class="ts-dot"></span>' for _ in range(n))
    html_final = (
        f'{estilo}<a class="ts-carousel-link" href="classificacoes" target="_self">'
        f'<div class="ts-carousel"><div class="ts-stage">{"".join(slides)}</div>'
        f'<div class="ts-dots">{pontos}</div>'
        f'<div class="ts-cta"><span>🏆 Ver todas as classificações e times</span><span>→</span></div>'
        f"</div></a>"
    )
    # remove a indentação de cada linha: com 4+ espaços, o Markdown trataria o bloco como
    # código pré-formatado (texto puro) em vez de renderizar o HTML/CSS
    return "\n".join(linha.strip() for linha in html_final.splitlines())
