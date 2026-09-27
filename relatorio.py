"""Relatório de scout em PDF (A4) de um time — para comissões técnicas e departamentos de análise."""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd
from fpdf import FPDF

import cards

ASSETS = Path(__file__).resolve().parent / "assets"
VERDE, VERDE_ESC, DOURADO, VERMELHO = (14, 107, 63), (10, 61, 38), (242, 183, 5), (200, 16, 46)
CINZA, TEXTO, ZEBRA = (91, 107, 98), (22, 36, 28), (240, 245, 241)


class Relatorio(FPDF):
    def __init__(self, titulo_curto: str):
        super().__init__(format="A4")
        self.titulo_curto = titulo_curto
        self.set_auto_page_break(True, 18)
        self.add_font("DejaVu", "", str(ASSETS / "fonts" / "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", str(ASSETS / "fonts" / "DejaVuSans-Bold.ttf"))
        self.add_font("DejaVu", "I", str(ASSETS / "fonts" / "DejaVuSans-Oblique.ttf"))
        self.set_title(f"Relatório de scout — {titulo_curto}")
        self.set_author("Tchê Scout — Lucho Pahim")
        self._capa = True

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*VERDE_ESC)
        self.rect(0, 0, 210, 14, "F")
        self.set_fill_color(*DOURADO)
        self.rect(0, 14, 210, 1.2, "F")
        self.set_xy(12, 4)
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(255, 255, 255)
        self.cell(90, 6, "TCHÊ SCOUT")
        self.set_font("DejaVu", "", 8)
        self.cell(0, 6, f"Relatório de scout · {self.titulo_curto}", align="R")
        self.set_y(22)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-12)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*CINZA)
        self.cell(0, 6, "Dados: súmulas oficiais da FGF · Tchê Scout (tchescout.streamlit.app)", align="L")
        self.set_x(-30)
        self.cell(18, 6, f"Pág. {self.page_no()}", align="R")

    # ---------------- blocos
    def titulo(self, texto: str):
        self.set_font("DejaVu", "B", 15)
        self.set_text_color(*VERDE_ESC)
        self.cell(0, 9, texto, new_x="LMARGIN", new_y="NEXT")
        self.set_fill_color(*DOURADO)
        self.rect(self.get_x(), self.get_y(), 18, 1.1, "F")
        self.ln(4)

    def subtitulo(self, texto: str):
        self.ln(2)
        self.set_font("DejaVu", "B", 10.5)
        self.set_text_color(*VERDE)
        self.cell(0, 6, texto.upper(), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def paragrafo(self, texto: str, tam: float = 9.5):
        self.set_font("DejaVu", "", tam)
        self.set_text_color(*TEXTO)
        self.multi_cell(0, 5.2, texto, new_x="LMARGIN", new_y="NEXT")

    def bullet(self, texto: str):
        self.set_font("DejaVu", "", 9.5)
        self.set_text_color(*TEXTO)
        x = self.get_x()
        self.set_fill_color(*DOURADO)
        self.rect(x + 1, self.get_y() + 2, 1.8, 1.8, "F")
        self.set_x(x + 6)
        self.multi_cell(0, 5.2, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(0.8)

    def kpis(self, itens: list[tuple[str, str]]):
        larg, alt = 60, 20
        x0, y0 = self.l_margin, self.get_y()
        for i, (rot, val) in enumerate(itens[:6]):
            x = x0 + (i % 3) * (larg + 4)
            y = y0 + (i // 3) * (alt + 4)
            self.set_fill_color(*ZEBRA)
            self.rect(x, y, larg, alt, "F")
            self.set_fill_color(*VERDE)
            self.rect(x, y, 1.6, alt, "F")
            self.set_xy(x + 4, y + 2)
            self.set_font("DejaVu", "B", 14)
            self.set_text_color(*VERDE_ESC)
            self.cell(larg - 6, 8, val)
            self.set_xy(x + 4, y + 11)
            self.set_font("DejaVu", "", 7.5)
            self.set_text_color(*CINZA)
            self.cell(larg - 6, 5, rot)
        self.set_y(y0 + 2 * (alt + 4) + 2)

    def forma(self, res: list[str]):
        cor = {"V": VERDE, "E": DOURADO, "D": VERMELHO}
        x, y = self.l_margin, self.get_y()
        for i, l in enumerate(res[-10:]):
            self.set_fill_color(*cor.get(l, CINZA))
            self.ellipse(x + i * 10, y, 8, 8, "F")
            self.set_xy(x + i * 10, y + 1.4)
            self.set_font("DejaVu", "B", 8)
            self.set_text_color(255, 255, 255) if l != "E" else self.set_text_color(*VERDE_ESC)
            self.cell(8, 5, l, align="C")
        self.set_y(y + 11)

    def barras(self, rotulos: list[str], a: list[int], b: list[int], nome_a: str, nome_b: str, altura: float = 44):
        x0, y0 = self.l_margin + 6, self.get_y()
        largura = 190 - 12
        m = max(max(a + b, default=1), 1)
        base = y0 + altura
        passo = largura / len(rotulos)
        for i, rot in enumerate(rotulos):
            bx = x0 + i * passo + passo * .12
            larg = passo * .34
            for k, (v, cor) in enumerate(((a[i], VERDE), (b[i], VERMELHO))):
                h = altura * v / m
                self.set_fill_color(*cor)
                self.rect(bx + k * (larg + 1.2), base - h, larg, h, "F")
                if v:
                    self.set_xy(bx + k * (larg + 1.2) - 2, base - h - 4.2)
                    self.set_font("DejaVu", "B", 7.5)
                    self.set_text_color(*VERDE_ESC)
                    self.cell(larg + 4, 4, str(v), align="C")
            self.set_xy(x0 + i * passo, base + 1)
            self.set_font("DejaVu", "", 7.5)
            self.set_text_color(*CINZA)
            self.cell(passo, 4, rot, align="C")
        self.set_draw_color(200, 210, 202)
        self.line(x0, base, x0 + largura, base)
        self.set_y(base + 8)
        self.set_font("DejaVu", "", 7.5)
        self.set_fill_color(*VERDE)
        self.rect(x0, self.get_y() + 1, 3, 3, "F")
        self.set_xy(x0 + 4.5, self.get_y())
        self.set_text_color(*CINZA)
        self.cell(24, 5, nome_a)
        self.set_fill_color(*VERMELHO)
        self.rect(x0 + 32, self.get_y() + 1, 3, 3, "F")
        self.set_xy(x0 + 36.5, self.get_y())
        self.cell(24, 5, nome_b, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def tabela(self, df: pd.DataFrame, larguras: list[float], alinh: list[str] | None = None, alt: float = 5.6, fonte: float = 8):
        if df is None or df.empty:
            self.paragrafo("Sem dados nesta seleção.")
            return
        alinh = alinh or ["L"] + ["C"] * (len(df.columns) - 1)
        self.set_fill_color(*VERDE_ESC)
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "B", fonte)
        for c, w, a in zip(df.columns, larguras, alinh):
            self.cell(w, alt + .6, str(c), fill=True, align=a)
        self.ln()
        self.set_font("DejaVu", "", fonte)
        for i, row in enumerate(df.itertuples(index=False)):
            if self.get_y() > 270:
                self.add_page()
            self.set_fill_color(*(ZEBRA if i % 2 else (255, 255, 255)))
            self.set_text_color(*TEXTO)
            for v, w, a in zip(row, larguras, alinh):
                txt = "" if (v is None or (isinstance(v, float) and pd.isna(v))) else (f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v))
                while txt and self.get_string_width(txt) > w - 1.6:
                    txt = txt[:-1]
                self.cell(w, alt, txt, fill=True, align=a)
            self.ln()
        self.ln(2)


def gerar_pdf_time(ctx: dict) -> bytes:
    """ctx: time, comps, ano, recorte, r(resumo), forma(list), insights(list[str]), faixas(df), tempos(df),
    primeiro(df), quadro(df), casa_fora(df), elenco(df), cartoes(dict), jogos(df), autor, funcao"""
    pdf = Relatorio(ctx["time"])

    # ---------------- capa
    pdf.add_page()
    pdf.set_fill_color(*VERDE_ESC)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.set_fill_color(*VERDE)
    pdf.rect(0, 190, 210, 107, "F")
    pdf.set_fill_color(*DOURADO)
    pdf.rect(0, 188.5, 210, 1.5, "F")
    buf = io.BytesIO()
    cards.logo(360).save(buf, "PNG")
    buf.seek(0)
    pdf.image(buf, x=20, y=30, h=42)
    pdf.set_xy(78, 38)
    pdf.set_font("DejaVu", "B", 26)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "TCHÊ SCOUT")
    pdf.set_xy(78, 52)
    pdf.set_font("DejaVu", "", 11)
    pdf.set_text_color(210, 225, 214)
    pdf.cell(0, 6, "Scout dos campeonatos gaúchos")
    pdf.set_xy(20, 110)
    pdf.set_font("DejaVu", "", 13)
    pdf.set_text_color(*DOURADO)
    pdf.cell(0, 8, "RELATÓRIO DE SCOUT")
    pdf.set_xy(20, 122)
    pdf.set_font("DejaVu", "B", 30)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(170, 13, ctx["time"].upper(), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(20)
    pdf.set_font("DejaVu", "", 12)
    pdf.set_text_color(210, 225, 214)
    pdf.multi_cell(170, 7, f"{', '.join(ctx['comps'])} · {ctx['ano']}\nRecorte: {ctx['recorte']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(20, 205)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 6, f"Emitido em {date.today():%d/%m/%Y}")
    pdf.set_xy(20, 214)
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(0, 6, ctx["autor"])
    pdf.set_xy(20, 220)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(210, 225, 214)
    pdf.cell(0, 6, ctx["funcao"])

    # ---------------- resumo
    pdf.add_page()
    r = ctx["r"]
    pdf.titulo("Resumo da campanha")
    pdf.kpis([("Jogos", f"{r['J']}  ({r['V']}V {r['E']}E {r['D']}D)"), ("Aproveitamento", f"{r['aprov']}%"),
              ("Gols pró por jogo", f"{r['gp_j']}"), ("Gols contra por jogo", f"{r['gc_j']}"),
              ("Saldo de gols", f"{r['SG']:+d}"), ("Jogos sem sofrer gol", f"{r['sem_sofrer']} ({r['pct_sem_sofrer']}%)")])
    pdf.subtitulo("Forma recente (mais antigo → mais recente)")
    pdf.forma(ctx["forma"])
    pdf.subtitulo("Principais insights")
    for t in ctx["insights"]:
        pdf.bullet(t)

    # ---------------- gols e minutagem
    pdf.add_page()
    pdf.titulo("Gols e minutagem")
    f = ctx["faixas"]
    pdf.subtitulo("Gols por faixa de 15 minutos")
    pdf.barras(list(f["Faixa"]), [int(x) for x in f["Feitos"]], [int(x) for x in f["Sofridos"]], "Feitos", "Sofridos")
    pdf.subtitulo("1º tempo × 2º tempo")
    pdf.tabela(ctx["tempos"], [50, 40, 40])
    if ctx.get("primeiro") is not None and len(ctx["primeiro"]):
        pdf.subtitulo("Quem abre o placar")
        pdf.tabela(ctx["primeiro"], [55, 30, 30, 30, 30])
    if ctx.get("quadro") is not None and len(ctx["quadro"]):
        pdf.subtitulo("Situação no intervalo × resultado final")
        pdf.tabela(ctx["quadro"], [50, 30, 30, 30, 30])
    if ctx.get("formacoes") is not None and len(ctx["formacoes"]):
        pdf.subtitulo("Formações registradas (informadas manualmente)")
        f_ = ctx["formacoes"][["Formação", "Jogos", "V", "E", "D", "GP", "GC", "Aproveitamento (%)"]]
        pdf.tabela(f_, [40, 18, 14, 14, 14, 16, 16, 40])
    pdf.subtitulo("Casa × fora")
    pdf.tabela(ctx["casa_fora"], [24, 18, 22, 20, 22, 14, 14, 26, 26], fonte=7.2)

    # ---------------- escalação e campo tático
    if ctx.get("campos"):
        pdf.add_page()
        pdf.titulo("Escalação e campo tático")
        y0 = pdf.get_y()
        larg = 88
        alt = larg * 1.36
        for i, c in enumerate(ctx["campos"][:2]):
            x = 12 + i * 96
            pdf.set_xy(x, y0)
            pdf.set_font("DejaVu", "B", 8.5)
            pdf.set_text_color(*VERDE_ESC)
            pdf.multi_cell(larg, 4.4, c["titulo"], new_x="LEFT", new_y="NEXT")
            pdf.set_x(x)
            pdf.set_font("DejaVu", "", 8)
            pdf.set_text_color(*VERDE)
            pdf.cell(larg, 5, c["subtitulo"], new_x="LEFT", new_y="NEXT")
            pdf.image(io.BytesIO(c["png"]), x=x, y=pdf.get_y() + 1, w=larg)
        pdf.set_y(y0 + 18 + alt + 4)
        for c in ctx["campos"][:2]:
            pdf.set_font("DejaVu", "I", 7.8)
            pdf.set_text_color(*CINZA)
            pdf.multi_cell(0, 4.2, f"• {c['titulo'].split(' — ')[0]}: {c['legenda']}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        pdf.set_font("DejaVu", "", 7.8)
        pdf.set_text_color(*CINZA)
        pdf.multi_cell(0, 4.2, "Cores: goleiro (dourado escuro), defesa (verde escuro), meio (verde), ataque (vermelho). "
                               "Camisas seguem a convenção brasileira; a posição real do atleta pode ser diferente.",
                       new_x="LMARGIN", new_y="NEXT")

    # ---------------- elenco e disciplina
    pdf.add_page()
    pdf.titulo("Elenco e disciplina")
    ct = ctx["cartoes"]
    pdf.paragrafo(f"Cartões amarelos: {ct.get('amarelos', 0)} ({ct.get('amarelos_jogo', 0):.2f} por jogo) · "
                  f"Cartões vermelhos: {ct.get('vermelhos', 0)} ({ct.get('diretos', 0)} diretos, {ct.get('segundo_amarelo', 0)} por 2º amarelo).")
    pdf.subtitulo("Atletas mais utilizados")
    pdf.tabela(ctx["elenco"], [40, 36, 14, 16, 16, 12, 18, 16], fonte=7.2)
    pdf.set_font("DejaVu", "I", 7.5)
    pdf.set_text_color(*CINZA)
    pdf.multi_cell(0, 4.2, "Posição: 'provável' = estimada pela camisa; 'Não confirmada' = a base ainda não sabe. "
                   "A súmula oficial não informa posições.", new_x="LMARGIN", new_y="NEXT")

    # ---------------- jogo a jogo
    pdf.add_page()
    pdf.titulo("Jogo a jogo")
    pdf.tabela(ctx["jogos"], [22, 14, 16, 60, 14, 14, 14, 14, 12], alinh=["L", "C", "C", "L", "C", "C", "C", "C", "C"], fonte=7.4)
    pdf.set_font("DejaVu", "I", 7.5)
    pdf.set_text_color(*CINZA)
    pdf.multi_cell(0, 4.2, "Fonte: súmulas oficiais publicadas pela Federação Gaúcha de Futebol (FGF). Relatório gerado pelo Tchê Scout; "
                           "minutagem de gols e cartões conforme registrado pela arbitragem. Estatística de desempenho — sem "
                           "finalidade de apostas.", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
