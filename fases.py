"""Regras de formato dos campeonatos: quem classifica para o mata-mata e a partir de que posição.
Os números aqui não são inventados — foram conferidos nos confrontos reais já sorteados/publicados
pela FGF (ver README/commit): ex. Série A2 2026, os 8 primeiros da Classificatória são exatamente
os 8 times que caíram nas Quartas de Final. Competição/fase sem regra confirmada não recebe destaque."""

from __future__ import annotations

# competição -> lista de (até a posição, cor, rótulo curto, rótulo longo)
ZONAS: dict[str, list[tuple[int, str, str, str]]] = {
    "Gauchão": [
        (8, "#0E6B3F", "Quartas", "Classificado para as quartas de final"),
        (12, "#8AA091", "Quadrang.", "Quadrangular do 9º ao 12º lugar"),
    ],
    "Gauchão Série A2": [
        (8, "#0E6B3F", "Quartas", "Classificado para as quartas de final"),
    ],
    "Copa FGF": [
        (4, "#0E6B3F", "Semifinal", "Classificado para a semifinal"),
    ],
}

PALAVRAS_MATA_MATA = ("quartas", "semifinal", "final", "oitavas", "quadrangular", "troféu farroupilha")


def eh_mata_mata(fase: str | None) -> bool:
    """True se o nome da fase indica uma etapa eliminatória/mata-mata (e não uma tabela de pontos corridos)."""
    if not fase:
        return False
    f = fase.lower()
    return any(p in f for p in PALAVRAS_MATA_MATA)


def zona_classificacao(competicao: str, pos: int) -> tuple[str, str, str] | None:
    """(cor, rótulo curto, rótulo longo) para a posição `pos` na fase classificatória de `competicao`,
    ou None se não há regra de corte confirmada para essa competição."""
    regras = ZONAS.get(competicao)
    if not regras:
        return None
    for limite, cor, curto, longo in regras:
        if pos <= limite:
            return cor, curto, longo
    return None


def legenda(competicao: str) -> str | None:
    """Legenda HTML curta (bolinha colorida) explicando os cortes, p/ uso em st.markdown(unsafe_allow_html=True)."""
    regras = ZONAS.get(competicao)
    if not regras:
        return None
    itens = []
    anterior = 0
    for limite, cor, curto, _ in regras:
        itens.append(f'<span style="color:{cor}">●</span> {curto} ({anterior + 1}º–{limite}º)')
        anterior = limite
    return " · ".join(itens)


def legenda_texto(competicao: str) -> str | None:
    """Mesma legenda, em texto simples (sem HTML), p/ uso em st.caption()."""
    regras = ZONAS.get(competicao)
    if not regras:
        return None
    itens = []
    anterior = 0
    for limite, _, curto, _ in regras:
        itens.append(f"{curto} ({anterior + 1}º–{limite}º)")
        anterior = limite
    return " · ".join(itens)
