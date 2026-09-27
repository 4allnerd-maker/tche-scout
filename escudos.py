"""Escudos dos clubes: baixados de fontes abertas (Wikipedia/Wikimedia Commons) e catalogados em
data/manual/escudos.json (time -> arquivo em assets/escudos/ + página de origem). Cobre os times mais
frequentes do Gauchão e da Série A2; quem ainda não tem escudo cadastrado recebe um distintivo com as
iniciais do nome, gerado na hora, para o layout nunca ficar sem símbolo.

Os escudos são marcas dos respectivos clubes — usados aqui só para identificação visual (como em
qualquer site de resultados esportivos), não como afirmação de vínculo oficial com o Tchê Scout."""

from __future__ import annotations

import base64
import io
import json
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent / "assets"
PASTA = ASSETS / "escudos"
CATALOGO = Path(__file__).resolve().parent / "data" / "manual" / "escudos.json"

CORES_RESERVA = [(14, 107, 63), (10, 61, 38), (200, 16, 46), (91, 107, 98), (122, 92, 0), (0, 92, 122)]


@lru_cache(maxsize=1)
def _catalogo() -> dict:
    if not CATALOGO.exists():
        return {}
    try:
        return json.loads(CATALOGO.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def tem_escudo(time: str) -> bool:
    return time in _catalogo()


def fonte_do_escudo(time: str) -> str | None:
    info = _catalogo().get(time)
    return info.get("wiki_title") if info else None


def caminho(time: str) -> Path | None:
    info = _catalogo().get(time)
    if not info:
        return None
    p = PASTA / info["arquivo"]
    return p if p.exists() else None


def _iniciais(time: str) -> str:
    palavras = [p for p in re.split(r"[\s-]+", time) if p and p.lower() not in
                {"de", "da", "do", "dos", "das", "e", "ec", "fc", "sc", "saf", "va"}]
    if not palavras:
        palavras = [time]
    if len(palavras) == 1:
        return palavras[0][:2].upper()
    return (palavras[0][0] + palavras[-1][0]).upper()


def _cor_reserva(time: str) -> tuple:
    return CORES_RESERVA[sum(map(ord, time)) % len(CORES_RESERVA)]


@lru_cache(maxsize=256)
def badge(time: str, tamanho: int = 96) -> Image.Image:
    """Distintivo com as iniciais do time (usado quando não há escudo cadastrado)."""
    ss = 3
    s = tamanho * ss
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cor = _cor_reserva(time)
    d.ellipse([0, 0, s, s], fill=cor + (255,), outline=(255, 255, 255, 255), width=max(2, s // 30))
    fnt = ImageFont.truetype(str(ASSETS / "fonts" / "DejaVuSans-Bold.ttf"), int(s * 0.36))
    d.text((s / 2, s / 2), _iniciais(time), font=fnt, fill=(255, 255, 255, 255), anchor="mm")
    return img.resize((tamanho, tamanho), Image.LANCZOS)


@lru_cache(maxsize=256)
def imagem(time: str, tamanho: int = 96) -> Image.Image:
    """Escudo do time em RGBA, redimensionado (lado maior = `tamanho`), ou o distintivo de reserva."""
    p = caminho(time)
    if not p:
        return badge(time, tamanho)
    try:
        img = Image.open(p).convert("RGBA")
    except OSError:
        return badge(time, tamanho)
    img.thumbnail((tamanho, tamanho), Image.LANCZOS)
    quadro = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    quadro.paste(img, ((tamanho - img.width) // 2, (tamanho - img.height) // 2), img)
    return quadro


def png_bytes(time: str, tamanho: int = 96) -> bytes:
    buf = io.BytesIO()
    imagem(time, tamanho).save(buf, "PNG")
    return buf.getvalue()


@lru_cache(maxsize=512)
def data_uri(time: str, tamanho: int = 32) -> str:
    """PNG do escudo (ou distintivo de reserva) como 'data:image/png;base64,...' — funciona em qualquer
    lugar (colunas de tabela, HTML embutido) sem depender de servir arquivo, inclusive no Streamlit Cloud."""
    return "data:image/png;base64," + base64.b64encode(png_bytes(time, tamanho)).decode()


def img_tag(time: str, altura: int = 28) -> str:
    """Tag <img> pronta para colar em HTML (st.markdown), já com o escudo embutido."""
    nome = time.replace('"', "")
    return (f'<img src="{data_uri(time, altura * 3)}" alt="{nome}" title="{nome}" '
            f'style="height:{altura}px;width:{altura}px;vertical-align:middle;border-radius:50%;'
            f'object-fit:contain;background:#fff;border:1px solid #DCE5DD;">')


def inserir_coluna(df: pd.DataFrame, coluna_time: str, nome_coluna: str = "Escudo", tamanho: int = 32) -> pd.DataFrame:
    """Retorna uma cópia de `df` com uma coluna de imagens (data URI) inserida logo antes de `coluna_time`."""
    if df is None or df.empty or coluna_time not in df.columns:
        return df
    df2 = df.copy()
    pos = df2.columns.get_loc(coluna_time)
    df2.insert(pos, nome_coluna, df2[coluna_time].map(lambda t: data_uri(str(t), tamanho) if pd.notna(t) else None))
    return df2


def cobertura(times_totais) -> tuple[int, int]:
    """(quantos desses times têm escudo cadastrado, total de times informado)."""
    times_totais = list(times_totais)
    return sum(1 for t in times_totais if tem_escudo(t)), len(times_totais)
