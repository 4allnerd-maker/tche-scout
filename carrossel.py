"""Carrossel de classificações da página inicial: gira sozinho entre os campeonatos (estilo SofaScore),
com escudo, posição e pontos. Só CSS (sem JavaScript — o Streamlit não executa <script> em st.markdown)."""

from __future__ import annotations

import html

import pandas as pd

import escudos as es
import fases
import stats
from theme import COR

# ordem de exibição: (nome da competição, rótulo curto)
COMPETICOES = [
    ("Gauchão", "Gauchão"),
    ("Gauchão Série A2", "Série A2"),
    ("Gauchão Série B", "Série B"),
    ("Copa FGF", "Copa FGF"),
    ("Gauchão Feminino", "Feminino"),
]
SEGUNDOS_POR_SLIDE = 7
ALTURA_LINHA = 27
ALTURA_CABECALHO = 34
MAX_LINHAS = 12  # teto de linhas por slide: mantém o card compacto e os times realmente na tabela
# Pos | Escudo | Time(flexível) | P | J | V | E | D | SG
GRADE = "1.5rem 1.4rem minmax(0,1fr) 2.1rem 1.7rem 1.7rem 1.7rem 1.7rem 2.3rem"


def _linha(pos: int, time: str, pts: int, j: int, v: int, e: int, d: int, sg: int, cor_zona: str) -> str:
    nome = html.escape(str(time))

    def _num(valor, cor=COR["texto_suave"], peso=600):
        return (f'<span style="text-align:center;color:{cor};font-size:.78rem;font-weight:{peso}">'
                f'{valor}</span>')

    return (
        f'<div style="display:grid;grid-template-columns:{GRADE};align-items:center;column-gap:.4rem;'
        f'height:{ALTURA_LINHA}px;padding:0 .5rem;border-radius:6px;'
        f'background:{COR["fundo_cartao"] if pos % 2 else "transparent"}">'
        f'<span style="width:4px;height:70%;border-radius:2px;background:{cor_zona};justify-self:start"></span>'
        f'<span style="color:{COR["texto_suave"]};font-weight:700;font-size:.8rem">{pos}</span>'
        f'<span style="display:flex;align-items:center;gap:.4rem;overflow:hidden">'
        f'<img src="{es.data_uri(time, 64)}" alt="{nome}" style="width:18px;height:18px;object-fit:contain;'
        f'background:#fff;border-radius:50%;border:1px solid rgba(255,255,255,.15);flex:0 0 auto">'
        f'<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.82rem;'
        f'font-weight:600;color:{COR["texto"]}">{nome}</span></span>'
        f'{_num(pts, COR["verde"], 800)}{_num(j)}{_num(v)}{_num(e)}{_num(d)}{_num(f"{sg:+d}")}'
        f"</div>"
    )


def _cabecalho_linha() -> str:
    def _c(rotulo):
        return f'<span style="text-align:center;color:{COR["texto_suave"]};font-size:.68rem;font-weight:700">{rotulo}</span>'
    return (
        f'<div style="display:grid;grid-template-columns:{GRADE};align-items:center;column-gap:.4rem;'
        f'height:{ALTURA_CABECALHO}px;padding:0 .5rem;border-bottom:1px solid {COR["borda"]}">'
        f'<span></span><span style="color:{COR["texto_suave"]};font-size:.68rem;font-weight:700">#</span>'
        f'<span style="color:{COR["texto_suave"]};font-size:.68rem;font-weight:700">Time</span>'
        f'{_c("Pts")}{_c("J")}{_c("V")}{_c("E")}{_c("D")}{_c("SG")}</div>'
    )


def _slide(comp: str, rotulo: str, jogos: pd.DataFrame, ano: int) -> tuple[str, int] | None:
    """Retorna (html do slide, nº de linhas) ou None se não houver classificação."""
    j = jogos[(jogos["categoria"] == ("Feminino" if "Feminino" in comp else "Masculino")) &
              (jogos["ano"] == ano) & (jogos["competicao_nome"] == comp)]
    if j.empty:
        return None
    fases_disp = sorted(j["fase_nome"].dropna().unique())
    if fases_disp:
        j = j[j["fase_nome"] == fases_disp[0]]
    tabela = stats.classificacao(j)
    if tabela.empty:
        return None
    n = len(tabela)
    visivel = tabela.head(MAX_LINHAS)
    linhas = "".join(
        _linha(int(r.Pos), r.Time, int(r.P), int(r.J), int(r.V), int(r.E), int(r.D), int(r.SG),
              (fases.zona_classificacao(comp, int(r.Pos)) or (None, None, None))[0] or "transparent")
        for r in visivel.itertuples())
    rodape = (f'<div style="text-align:center;color:{COR["texto_suave"]};font-size:.72rem;padding:.35rem 0 0 0">'
              f'+{n - len(visivel)} times na tabela completa</div>') if n > len(visivel) else ""
    legenda = fases.legenda(comp)
    legenda_html = (f'<div style="text-align:center;color:{COR["texto_suave"]};font-size:.68rem;padding:.3rem 0 0 0">'
                    f'{legenda}</div>') if legenda else ""
    slide = (
        f'<div class="ts-slide"><div class="ts-slide-conteudo">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.4rem">'
        f'<span style="font-family:\'Archivo Black\',Inter;color:{COR["dourado"]};font-size:1.05rem">{html.escape(rotulo)}</span>'
        f'<span style="color:{COR["texto_suave"]};font-size:.78rem">{ano} · {n} times</span></div>'
        f'{_cabecalho_linha()}{linhas}{rodape}{legenda_html}</div></div>'
    )
    return slide, len(visivel)


def widget(jogos: pd.DataFrame) -> str | None:
    """HTML do carrossel (card + slides). None se não houver classificação nenhuma para montar."""
    if jogos.empty:
        return None
    ano = int(jogos[jogos["categoria"] == "Masculino"]["ano"].max())
    resultados = [s for comp, rot in COMPETICOES if (s := _slide(comp, rot, jogos, ano))]
    fem = jogos[jogos["categoria"] == "Feminino"]
    if not fem.empty:
        ano_fem = int(fem["ano"].max())
        s = _slide("Gauchão Feminino", "Feminino", jogos, ano_fem)
        if s and len(resultados) < len(COMPETICOES):
            resultados.append(s)
    if not resultados:
        return None
    slides = [s for s, _ in resultados]
    maior_tabela = max(linhas for _, linhas in resultados)
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
      0% {{ background: {COR['borda']}; }}
      {dentro:.2f}% {{ background: {COR['dourado']}; }}
      {fatia - 0.5:.2f}% {{ background: {COR['dourado']}; }}
      {fatia:.2f}% {{ background: {COR['borda']}; }}
      100% {{ background: {COR['borda']}; }}
    }}
    """
    estilo = f"""
    <style>
    .ts-carousel {{ position: relative; background:{COR['fundo_cartao']}; border:1px solid {COR['borda']};
      border-radius:14px; padding: 1rem 1.1rem .9rem 1.1rem; box-shadow: 0 1px 3px rgba(0,0,0,.25);
      transition: box-shadow .15s, transform .15s, border-color .15s; cursor: pointer; }}
    .ts-carousel:hover {{ box-shadow: 0 8px 24px rgba(0,0,0,.4); transform: translateY(-2px);
      border-color: {COR['verde']}; }}
    a.ts-carousel-link {{ position:absolute; inset:0; z-index:5; text-decoration:none; }}
    .ts-carousel .ts-cta {{ display:flex; align-items:center; justify-content:space-between; margin-top:.7rem;
      padding-top:.6rem; border-top:1px solid {COR['borda']}; color:{COR['verde']}; font-weight:700; font-size:.85rem; }}
    .ts-carousel .ts-stage {{ position: relative;
      height: {30 + ALTURA_CABECALHO + maior_tabela * ALTURA_LINHA + 44}px; }}
    .ts-carousel .ts-slide {{ position: absolute; inset: 0; opacity: 0; display:flex; flex-direction:column;
      justify-content:center; animation: tsCarrosselFade {total}s infinite; }}
    .ts-carousel .ts-slide-conteudo {{ width:100%; }}
    .ts-carousel .ts-dots {{ display:flex; gap:6px; justify-content:center; margin-top:.6rem; }}
    .ts-carousel .ts-dot {{ width:7px; height:7px; border-radius:50%; background:{COR['borda']};
      animation: tsCarrosselDot {total}s infinite; }}
    {css_slides}
    {css_pontos}
    {keyframes}
    </style>
    """
    pontos = "".join('<span class="ts-dot"></span>' for _ in range(n))
    html_final = (
        f'{estilo}<div class="ts-carousel">'
        f'<a class="ts-carousel-link" href="classificacoes" target="_self" aria-label="Ver todas as classificações"></a>'
        f'<div class="ts-stage">{"".join(slides)}</div>'
        f'<div class="ts-dots">{pontos}</div>'
        f'<div class="ts-cta"><span>🏆 Ver todas as classificações e times</span><span>→</span></div>'
        f"</div>"
    )
    # remove a indentação de cada linha: com 4+ espaços, o Markdown trataria o bloco como
    # código pré-formatado (texto puro) em vez de renderizar o HTML/CSS
    return "\n".join(linha.strip() for linha in html_final.splitlines())
