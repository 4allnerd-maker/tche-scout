"""Gerador de cards (PNG) do Tchê Scout: resultados, artilheiros, classificação e raio-X de time.
Tudo desenhado com Pillow, no padrão visual da marca (verde, dourado, vermelho)."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent / "assets"
FONT_B = str(ASSETS / "fonts" / "DejaVuSans-Bold.ttf")
FONT_R = str(ASSETS / "fonts" / "DejaVuSans.ttf")

VERDE, VERDE_ESC, DOURADO, VERMELHO = (14, 107, 63), (10, 61, 38), (242, 183, 5), (200, 16, 46)
BRANCO, CINZA, FUNDO = (255, 255, 255), (91, 107, 98), (243, 246, 241)
W = 1080


def fonte(tam: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT_R, tam)


def _cabe(draw, texto, fnt, largura):
    """Corta o texto com reticências para caber na largura."""
    if draw.textlength(texto, font=fnt) <= largura:
        return texto
    while len(texto) > 1 and draw.textlength(texto + "…", font=fnt) > largura:
        texto = texto[:-1]
    return texto + "…"


def _texto(draw, xy, texto, fnt, cor, ancora="la"):
    draw.text(xy, texto, font=fnt, fill=cor, anchor=ancora)


# ------------------------------------------------------------------ logo (Conceito B, desenhado à mão)
def _bezier(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
        y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts


def _escudo_pts():
    p = _bezier((100, 8), (72, 24), (42, 30), (12, 32))
    p += [(12, 116)]
    p += _bezier((12, 116), (12, 168), (50, 208), (100, 232))
    p += _bezier((100, 232), (150, 208), (188, 168), (188, 116))
    p += [(188, 32)]
    p += _bezier((188, 32), (158, 30), (128, 24), (100, 8))
    return p


def logo(altura: int) -> Image.Image:
    """Símbolo do Tchê Scout (escudo com barras e seta) como imagem RGBA com a altura pedida."""
    ss = 4
    Hh = altura * ss
    esc = Hh / 240
    Ww = int(200 * esc)
    img = Image.new("RGBA", (Ww, Hh), (0, 0, 0, 0))

    def S(pts):
        return [(x * esc, y * esc) for x, y in pts]

    mask = Image.new("L", (Ww, Hh), 0)
    ImageDraw.Draw(mask).polygon(S(_escudo_pts()), fill=255)
    base = Image.new("RGBA", (Ww, Hh), VERDE + (255,))
    d = ImageDraw.Draw(base)
    d.polygon(S([(0, 132), (200, 44), (200, 150), (0, 238)]), fill=VERMELHO + (255,))
    d.polygon(S([(0, 196), (200, 114), (200, 240), (0, 240)]), fill=DOURADO + (255,))
    img.paste(base, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.line(S(_escudo_pts() + [_escudo_pts()[0]]), fill=VERDE_ESC + (255,), width=int(8 * esc), joint="curve")
    for x, y, h in ((46, 132, 52), (76, 112, 72), (106, 94, 90), (136, 70, 114)):
        d.rectangle(S([(x, y), (x + 24, y + h)])[0] + S([(x, y), (x + 24, y + h)])[1], fill=VERDE_ESC + (255,), outline=BRANCO + (255,),
                    width=int(3 * esc))
    seta = S([(44, 124), (84, 88), (108, 104), (152, 58)])
    d.line(seta, fill=VERDE_ESC + (255,), width=int(15 * esc), joint="curve")
    d.line(seta, fill=DOURADO + (255,), width=int(9 * esc), joint="curve")
    d.polygon(S([(168, 44), (138, 50), (160, 72)]), fill=DOURADO + (255,), outline=VERDE_ESC + (255,), width=int(4 * esc))
    return img.resize((Ww // ss, altura), Image.LANCZOS)


# ------------------------------------------------------------------ moldura comum
def _fundo(altura: int) -> Image.Image:
    img = Image.new("RGB", (W, altura), VERDE_ESC)
    px = ImageDraw.Draw(img)
    for y in range(altura):  # degradê vertical
        t = y / max(altura - 1, 1)
        cor = tuple(int(VERDE_ESC[i] * (1 - t * .55) + VERDE[i] * t * .55) for i in range(3))
        px.line([(0, y), (W, y)], fill=cor)
    ov = Image.new("RGBA", (W, altura), (0, 0, 0, 0))
    o = ImageDraw.Draw(ov)
    linha = (255, 255, 255, 16)
    o.rectangle([60, 60, W - 60, altura - 60], outline=linha, width=3)
    o.line([(60, altura // 2), (W - 60, altura // 2)], fill=linha, width=3)
    o.ellipse([W // 2 - 150, altura // 2 - 150, W // 2 + 150, altura // 2 + 150], outline=linha, width=3)
    img.paste(ov, (0, 0), ov)
    return img


def _moldura(altura: int, titulo: str, subtitulo: str = "", rodape: str = "tchescout.streamlit.app") -> tuple[Image.Image, ImageDraw.ImageDraw, int]:
    img = _fundo(altura)
    d = ImageDraw.Draw(img)
    lg = logo(96)
    img.paste(lg, (64, 52), lg)
    _texto(d, (176, 62), "TCHÊ SCOUT", fonte(34), BRANCO)
    _texto(d, (176, 104), "Scout dos campeonatos gaúchos", fonte(20, False), (210, 225, 214))
    y = 190
    _texto(d, (W // 2, y), _cabe(d, titulo.upper(), fonte(50), W - 140), fonte(50), BRANCO, "ma")
    y += 68
    if subtitulo:
        _texto(d, (W // 2, y), _cabe(d, subtitulo, fonte(26, False), W - 140), fonte(26, False), DOURADO, "ma")
        y += 44
    d.rectangle([W // 2 - 60, y + 6, W // 2 + 60, y + 10], fill=DOURADO)
    # rodapé
    d.rectangle([0, altura - 78, W, altura], fill=VERDE_ESC)
    d.rectangle([0, altura - 82, W, altura - 78], fill=DOURADO)
    _texto(d, (W // 2, altura - 40), rodape + "  ·  dados: súmulas oficiais da FGF", fonte(21, False), (210, 225, 214), "mm")
    return img, d, y + 40


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


# ------------------------------------------------------------------ cards
def card_resultados(jogos: pd.DataFrame, titulo: str, subtitulo: str = "", destaque: str | None = None,
                    por_card: int = 8) -> list[bytes]:
    """jogos: colunas time_mandante, time_visitante, gols_mandante, gols_visitante (e opcional 'situacao')."""
    imagens = []
    linhas = list(jogos.itertuples())
    paginas = [linhas[i:i + por_card] for i in range(0, len(linhas), por_card)] or [[]]
    for n, pg in enumerate(paginas, 1):
        alt = 1080
        sub = subtitulo + (f"  ({n}/{len(paginas)})" if len(paginas) > 1 else "")
        img, d, y0 = _moldura(alt, titulo, sub)
        topo, base = y0, alt - 110
        h = min(96, (base - topo) // max(len(pg), 1) - 12)
        y = topo
        for r in pg:
            wo = getattr(r, "situacao", "") == "W.O."
            dest = destaque and destaque in (r.time_mandante, r.time_visitante)
            d.rounded_rectangle([70, y, W - 70, y + h], radius=18, fill=BRANCO, outline=DOURADO if dest else None, width=5)
            f = fonte(27)
            _texto(d, (W // 2 - 92, y + h // 2), _cabe(d, r.time_mandante, f, 380), f, VERDE_ESC, "rm")
            _texto(d, (W // 2 + 92, y + h // 2), _cabe(d, r.time_visitante, f, 380), f, VERDE_ESC, "lm")
            d.rounded_rectangle([W // 2 - 80, y + 10, W // 2 + 80, y + h - 10], radius=14, fill=VERDE_ESC)
            placar = f"{int(r.gols_mandante)}  x  {int(r.gols_visitante)}"
            _texto(d, (W // 2, y + h // 2), placar, fonte(36), DOURADO, "mm")
            if wo:
                _texto(d, (W - 90, y + h // 2), "W.O.", fonte(18), VERMELHO, "rm")
            y += h + 12
        if not pg:
            _texto(d, (W // 2, alt // 2), "Sem jogos para exibir", fonte(30), BRANCO, "mm")
        imagens.append(_png(img))
    return imagens


def card_artilheiros(df: pd.DataFrame, titulo: str, subtitulo: str = "", top: int = 10) -> bytes:
    """df: colunas Atleta, Time, Gols."""
    d0 = df.head(top).reset_index(drop=True)
    alt = 1350
    img, d, y0 = _moldura(alt, titulo, subtitulo)
    maxg = max(int(d0["Gols"].max()), 1) if len(d0) else 1
    linha = min(104, (alt - 110 - y0) // max(top, 1))
    y = y0
    for i, r in d0.iterrows():
        d.rounded_rectangle([70, y, W - 70, y + linha - 12], radius=16, fill=(255, 255, 255, 235) if False else BRANCO)
        d.ellipse([84, y + 12, 84 + 56, y + 68], fill=DOURADO if i == 0 else VERDE_ESC)
        _texto(d, (112, y + 40), str(i + 1), fonte(28), VERDE_ESC if i == 0 else BRANCO, "mm")
        _texto(d, (160, y + 10), _cabe(d, str(r["Atleta"]), fonte(30), 470), fonte(30), VERDE_ESC)
        _texto(d, (160, y + 50), _cabe(d, str(r["Time"]), fonte(21, False), 470), fonte(21, False), CINZA)
        bx0, bx1 = 650, W - 190
        d.rounded_rectangle([bx0, y + 28, bx1, y + 52], radius=12, fill=(225, 233, 226))
        d.rounded_rectangle([bx0, y + 28, bx0 + max(28, int((bx1 - bx0) * r["Gols"] / maxg)), y + 52], radius=12,
                            fill=VERDE if i else DOURADO)
        _texto(d, (W - 90, y + 40), str(int(r["Gols"])), fonte(44), VERDE_ESC, "rm")
        y += linha
    return _png(img)


def card_classificacao(df: pd.DataFrame, titulo: str, subtitulo: str = "", destaque: str | None = None, top: int = 12) -> bytes:
    """df: colunas Pos, Time, P, J, V, SG."""
    d0 = df.head(top).reset_index(drop=True)
    alt = 1350
    img, d, y0 = _moldura(alt, titulo, subtitulo)
    cab = fonte(22)
    xs = {"pos": 96, "time": 150, "P": 700, "J": 780, "V": 860, "SG": 960}
    _texto(d, (xs["time"], y0 - 6), "TIME", cab, DOURADO)
    for k, rot in (("P", "P"), ("J", "J"), ("V", "V"), ("SG", "SG")):
        _texto(d, (xs[k], y0 - 6), rot, cab, DOURADO, "ma")
    y = y0 + 32
    linha = min(78, (alt - 110 - y) // max(len(d0), 1))
    for i, r in d0.iterrows():
        dest = destaque and r["Time"] == destaque
        d.rounded_rectangle([70, y, W - 70, y + linha - 8], radius=14, fill=BRANCO, outline=DOURADO if dest else None, width=5)
        _texto(d, (xs["pos"], y + (linha - 8) // 2), str(int(r["Pos"])), fonte(28), VERDE_ESC, "mm")
        _texto(d, (xs["time"], y + (linha - 8) // 2), _cabe(d, str(r["Time"]), fonte(28), 500), fonte(28), VERDE_ESC, "lm")
        for k in ("P", "J", "V", "SG"):
            v = r[k]
            txt = f"{int(v):+d}" if k == "SG" else str(int(v))
            _texto(d, (xs[k], y + (linha - 8) // 2), txt, fonte(30 if k == "P" else 26), VERDE_ESC if k == "P" else CINZA, "mm")
        y += linha
    return _png(img)


def card_time(time: str, subtitulo: str, kpis: list[tuple[str, str]], forma: list[str], faixas: pd.DataFrame,
              destaques: list[str]) -> bytes:
    """Raio-X do time. kpis: [(rótulo, valor)] (até 6); forma: ['V','E','D',...]; faixas: colunas Faixa, Feitos, Sofridos."""
    alt = 1350
    img, d, y0 = _moldura(alt, time, subtitulo)
    # KPIs 3x2
    cw, ch = 300, 130
    for i, (rot, val) in enumerate(kpis[:6]):
        x = 70 + (i % 3) * (cw + 25)
        y = y0 + (i // 3) * (ch + 20)
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=18, fill=BRANCO)
        _texto(d, (x + cw // 2, y + 46), _cabe(d, val, fonte(46), cw - 20), fonte(46), VERDE, "mm")
        _texto(d, (x + cw // 2, y + 100), rot, fonte(20, False), CINZA, "mm")
    y = y0 + 2 * (ch + 20) + 6
    # forma
    _texto(d, (70, y), "FORMA RECENTE", fonte(22), DOURADO)
    cores = {"V": VERDE, "E": DOURADO, "D": VERMELHO}
    for i, l in enumerate(forma[-8:]):
        cx = 100 + i * 70
        d.ellipse([cx - 28, y + 40, cx + 28, y + 96], fill=cores.get(l, CINZA))
        _texto(d, (cx, y + 68), l, fonte(26), BRANCO if l != "E" else VERDE_ESC, "mm")
    y += 130
    # gols por faixa
    _texto(d, (70, y), "GOLS POR MINUTO", fonte(22), DOURADO)
    d.rounded_rectangle([70, y + 34, W - 70, y + 300], radius=18, fill=BRANCO)
    maxv = max(int(faixas[["Feitos", "Sofridos"]].max().max()), 1)
    gx, base = 110, y + 262
    larg = (W - 220) / len(faixas)
    for i, r in enumerate(faixas.itertuples()):
        x0 = gx + i * larg
        for k, (v, cor) in enumerate(((r.Feitos, VERDE), (r.Sofridos, VERMELHO))):
            hh = int(170 * v / maxv)
            bx = x0 + 10 + k * (larg / 2 - 6)
            d.rectangle([bx, base - hh, bx + larg / 2 - 16, base], fill=cor)
            if v:
                _texto(d, (bx + (larg / 2 - 16) / 2, base - hh - 4), str(int(v)), fonte(18), VERDE_ESC, "ms")
        _texto(d, (x0 + larg / 2, base + 14), r.Faixa, fonte(16, False), CINZA, "ma")
    d.rectangle([70 + 24, y + 322 - 12, 70 + 40, y + 322 + 4], fill=VERDE)
    _texto(d, (70 + 48, y + 320), "feitos", fonte(17, False), (210, 225, 214), "lm")
    d.rectangle([70 + 130, y + 322 - 12, 70 + 146, y + 322 + 4], fill=VERMELHO)
    _texto(d, (70 + 154, y + 320), "sofridos", fonte(17, False), (210, 225, 214), "lm")
    y += 350
    for t in destaques[:3]:
        _texto(d, (70, y), "▸ " + _cabe(d, t, fonte(23, False), W - 170), fonte(23, False), BRANCO)
        y += 40
    return _png(img)


# ------------------------------------------------------------------ campo tático (PNG para o PDF)
COR_ZONA_RGB = {"Goleiro": (122, 92, 0), "Defesa": (10, 61, 38), "Meio": (14, 107, 63), "Ataque": (200, 16, 46),
                "Variável": (91, 107, 98)}


def campo_png(pos: pd.DataFrame, titulo: str = "", largura: int = 520) -> bytes:
    """Campo em pé (ataque para cima) com os jogadores em (x, y) de 0 a 100. pos: colunas numero, nome, zona, x, y."""
    ss = 2
    w, h = largura * ss, int(largura * 1.36) * ss
    img = Image.new("RGB", (w, h), (14, 107, 63))
    d = ImageDraw.Draw(img)
    for i in range(0, 8):  # listras do gramado
        if i % 2:
            d.rectangle([0, int(h * i / 8), w, int(h * (i + 1) / 8)], fill=(17, 116, 69))
    m = int(w * 0.06)
    branco = (255, 255, 255)
    lw = 3 * ss
    d.rectangle([m, m, w - m, h - m], outline=branco, width=lw)
    d.line([(m, h // 2), (w - m, h // 2)], fill=branco, width=lw)
    r = int(w * 0.13)
    d.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], outline=branco, width=lw)
    for top in (True, False):
        y0, y1 = (m, m + int((h - 2 * m) * 0.16)) if top else (h - m - int((h - 2 * m) * 0.16), h - m)
        d.rectangle([int(w * 0.22), y0, int(w * 0.78), y1], outline=branco, width=lw)
        y0, y1 = (m, m + int((h - 2 * m) * 0.06)) if top else (h - m - int((h - 2 * m) * 0.06), h - m)
        d.rectangle([int(w * 0.38), y0, int(w * 0.62), y1], outline=branco, width=lw)
    f_num, f_nome = fonte(20 * ss), fonte(13 * ss, False)
    for r_ in pos.itertuples():
        x = m + (w - 2 * m) * (r_.x / 100)
        y = h - m - (h - 2 * m) * (r_.y / 100)  # ataque para cima
        cor = COR_ZONA_RGB.get(r_.zona, (91, 107, 98))
        rad = 22 * ss
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=cor, outline=branco, width=2 * ss)
        num = "" if r_.numero != r_.numero else str(int(r_.numero))
        d.text((x, y), num, font=f_num, fill=branco, anchor="mm")
        nome = str(r_.nome).split(" ")[0][:11]
        d.text((x + 1 * ss, y + rad + 3 * ss + 1 * ss), nome, font=f_nome, fill=(0, 0, 0), anchor="ma")
        d.text((x, y + rad + 3 * ss), nome, font=f_nome, fill=branco, anchor="ma")
    img = img.resize((largura, int(largura * 1.36)), Image.LANCZOS)
    return _png(img)
