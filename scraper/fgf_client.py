"""Cliente HTTP simples para o site da FGF (fgf.com.br) — descoberta e download."""

from __future__ import annotations

import re
import time
import requests

BASE = "https://fgf.com.br"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BrasilFarroupilhaBI/1.0 "
                  "(uso pessoal, analista de desempenho do clube; contato via app)"
}
TIMEOUT = 20
DELAY = 0.4  # segundos entre requisicoes, para nao sobrecarregar o site da FGF

# competicoes/profissional/{id}
COMPETICOES_PROFISSIONAL = {
    23: "Gauchão",
    24: "Gauchão Série A2",
    25: "Gauchão Série B",
    26: "Copa FGF",
    27: "Recopa Gaúcha",
}

# competicoes/feminino/{id}
COMPETICOES_FEMININO = {
    59: "Gauchão Feminino",
    803: "Gauchão Feminino Sub 20",
    564: "Gauchão Feminino Sub 17",
    708: "Gauchão Feminino Sub 15",
}

SOBRE_JOGO_RE = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>\s*SOBRE O JOGO\s*</a>', re.I)
def _fase_link_re(categoria: str):
    return re.compile(
        r'<a[^>]+href="(https?://fgf\.com\.br/competicoes/' + categoria + r'/\d+/\d+/(\d+))"[^>]*>\s*([^<]+?)\s*</a>'
    )
# A FGF hospedou sumulas em dois lugares diferentes ao longo do tempo:
# fgf.com.br/public/sumulas/{id}.pdf (mais antigo) e, a partir de meados de
# 2026, conteudo.cbf.com.br/federacoes/16/sumulas/{ano}/{id}.pdf (mudanca de
# plataforma). Aceitamos os dois.
SUMULA_PDF_RE_FGF = re.compile(r'https?://(?:www\.)?fgf\.com\.br/public/sumulas/(\d+)\.pdf')
SUMULA_PDF_RE_CBF = re.compile(r'https?://conteudo\.cbf\.com\.br/federacoes/16/sumulas/\d+/(\d+)\.pdf')

# Terceiro formato (jogos antigos/remarcados): fgf.com.br/Layout/sumulas/{id}{id}.pdf
# ou {id}{id}_merged.pdf (o id aparece repetido no nome do arquivo)
SUMULA_PDF_RE_LAYOUT = re.compile(r'https?://(?:www\.)?fgf\.com\.br/Layout/sumulas/(\d+?)\1(?:_merged)?\.pdf')
BORDERO_RE = re.compile(r'https?://(?:www\.)?fgf\.com\.br/public/borderos/(\d+)b\.pdf')


_session = requests.Session()
_session.headers.update(HEADERS)


def get(url: str) -> str:
    resp = _session.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    time.sleep(DELAY)
    return resp.text


def discover_phases(competicao_id: int, ano: int, categoria: str = "profissional") -> list[dict]:
    """Retorna as fases (Classificatoria, Quartas, etc) de uma competicao/ano.
    Se nao houver abas de fase, retorna uma fase 'unica' apontando pra propria URL base."""
    url = f"{BASE}/competicoes/{categoria}/{competicao_id}/{ano}"
    html = get(url)
    fases = []
    seen = set()
    for full_url, fase_id, nome in _fase_link_re(categoria).findall(html):
        if fase_id in seen:
            continue
        seen.add(fase_id)
        fases.append({"fase_id": int(fase_id), "fase_nome": nome.strip(), "url": full_url})
    if not fases:
        fases.append({"fase_id": None, "fase_nome": "Única", "url": url})
    return fases


def discover_games_in_page(url: str) -> list[str]:
    """Retorna as URLs de jogo (/jogo/slug) encontradas numa pagina de fase."""
    html = get(url)
    hrefs = SOBRE_JOGO_RE.findall(html)
    return sorted(set(hrefs))


def discover_sumula(jogo_url: str) -> tuple[str | None, str | None]:
    """Retorna (sumula_id, sumula_url) procurando nos dois hosts possiveis."""
    html = get(jogo_url)
    m = SUMULA_PDF_RE_FGF.search(html)
    if m:
        return m.group(1), m.group(0)
    m = SUMULA_PDF_RE_CBF.search(html)
    if m:
        return m.group(1), m.group(0)
    m = SUMULA_PDF_RE_LAYOUT.search(html)
    if m:
        return m.group(1), m.group(0)
    # Sem link de sumula na pagina, mas o borderô ({id}b.pdf) revela o id do jogo:
    # tenta os hosts conhecidos com esse id (achado em jogos remarcados).
    b = BORDERO_RE.search(html)
    if b:
        sid = b.group(1)
        ano = jogo_url.rstrip("/")[-4:]
        for cand in (f"{BASE}/public/sumulas/{sid}.pdf",
                     f"https://conteudo.cbf.com.br/federacoes/16/sumulas/{ano}/{sid}.pdf"):
            try:
                r = _session.get(cand, timeout=TIMEOUT)
            except requests.RequestException:
                continue
            time.sleep(DELAY)
            if r.status_code == 200 and r.content.startswith(b"%PDF"):
                return sid, cand
    return None, None


def discover_sumula_id(jogo_url: str) -> str | None:
    """Mantido por compatibilidade; prefira discover_sumula()."""
    sid, _ = discover_sumula(jogo_url)
    return sid


def download_sumula(sumula_id: str, dest_path: str, sumula_url: str | None = None) -> bool:
    url = sumula_url or f"{BASE}/public/sumulas/{sumula_id}.pdf"
    resp = _session.get(url, timeout=TIMEOUT)
    time.sleep(DELAY)
    if resp.status_code != 200 or not resp.content.startswith(b"%PDF"):
        return False
    with open(dest_path, "wb") as f:
        f.write(resp.content)
    return True
