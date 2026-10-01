"""Campo tático (Plotly) com os titulares posicionados pela numeração de camisa.
ATENÇÃO: é uma leitura da súmula pela convenção de camisas, NÃO a formação tática real do jogo."""

from __future__ import annotations

import plotly.graph_objects as go

import camisas as cm

COR_LINHA = "rgba(255,255,255,.65)"


def _campo(fig: go.Figure) -> None:
    fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, line=dict(color=COR_LINHA, width=2), fillcolor="#0E6B3F", layer="below")
    fig.add_shape(type="line", x0=0, y0=50, x1=100, y1=50, line=dict(color=COR_LINHA, width=1.5))
    fig.add_shape(type="circle", x0=38, y0=38, x1=62, y1=62, line=dict(color=COR_LINHA, width=1.5))
    for y0, y1 in ((0, 16), (84, 100)):
        fig.add_shape(type="rect", x0=22, y0=y0, x1=78, y1=y1, line=dict(color=COR_LINHA, width=1.5))
    for y0, y1 in ((0, 6), (94, 100)):
        fig.add_shape(type="rect", x0=38, y0=y0, x1=62, y1=y1, line=dict(color=COR_LINHA, width=1.5))


def figura_campo(pos, titulo: str = "", altura: int = 520) -> go.Figure:
    """pos: DataFrame de camisas.posicoes_no_campo()."""
    fig = go.Figure()
    _campo(fig)
    for zona, g in pos.groupby("zona"):
        fig.add_trace(go.Scatter(
            x=g["x"], y=g["y"], mode="markers+text", name=zona,
            marker=dict(size=34, color=cm.COR_ZONA.get(zona, "#5B6B62"), line=dict(color="white", width=2)),
            text=g["numero"].map(lambda n: "" if n != n else str(int(n))), textfont=dict(color="white", size=14, family="Inter"),
            hovertext=g["nome"] + " · camisa " + g["numero"].map(lambda n: "" if n != n else str(int(n))), hoverinfo="text",
            showlegend=False))
        for r in g.itertuples():
            fig.add_annotation(x=r.x, y=r.y - 6.6, text=str(r.nome).split(" ")[0][:12], showarrow=False,
                               font=dict(color="white", size=11, family="Inter"))
    fig.update_xaxes(range=[-2, 102], visible=False)
    fig.update_yaxes(range=[-3, 103], visible=False, scaleanchor="x", scaleratio=1.15)
    fig.update_layout(height=altura, margin=dict(l=0, r=0, t=34, b=0), title=dict(text=titulo, font=dict(size=15)),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig
