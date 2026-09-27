"""Numeração de camisas: a súmula não informa a posição, mas o futebol brasileiro tem convenções fortes.
Aqui a convenção é usada como PISTA (com o quanto os dados a confirmam), nunca como fato."""

from __future__ import annotations

import pandas as pd

# Convenção tradicional (titulares 1–11) e usos frequentes de reservas (12+).
CONVENCAO = {
    1: ("Goleiro", "Goleiro"),
    2: ("Defesa", "Lateral direito"),
    3: ("Defesa", "Zagueiro"),
    4: ("Defesa", "Zagueiro"),
    5: ("Meio", "Volante"),
    6: ("Defesa", "Lateral esquerdo"),
    7: ("Ataque", "Ponta / extremo"),
    8: ("Meio", "Meia"),
    9: ("Ataque", "Centroavante"),
    10: ("Meio", "Meia armador"),
    11: ("Ataque", "Ponta / extremo"),
    12: ("Goleiro", "Goleiro reserva"),
    13: ("Defesa", "Zagueiro / lateral"),
    14: ("Defesa", "Lateral / zagueiro"),
    15: ("Defesa", "Zagueiro / volante"),
    16: ("Defesa", "Lateral esquerdo"),
    17: ("Ataque", "Ponta / atacante"),
    18: ("Meio", "Meia"),
    19: ("Ataque", "Atacante"),
    20: ("Meio", "Meia / atacante"),
    21: ("Ataque", "Atacante"),
    22: ("Variável", "Reserva (numeração livre)"),
}
ZONAS = ["Goleiro", "Defesa", "Meio", "Ataque"]
COR_ZONA = {"Goleiro": "#7A5C00", "Defesa": "#0A3D26", "Meio": "#0E6B3F", "Ataque": "#C8102E", "Variável": "#5B6B62"}


def zona(numero, goleiro: bool = False) -> str:
    if goleiro:
        return "Goleiro"
    try:
        n = int(numero)
    except (TypeError, ValueError):
        return "Variável"
    z = CONVENCAO.get(n, ("Variável", ""))[0]
    return "Defesa" if (z == "Goleiro" and not goleiro) else z  # camisa de goleiro usada por atleta de linha


def funcao_provavel(numero) -> str:
    try:
        return CONVENCAO.get(int(numero), ("Variável", "Numeração livre"))[1]
    except (TypeError, ValueError):
        return "—"


def perfil_camisas(partidas: pd.DataFrame, minimo_jogos: int = 20) -> pd.DataFrame:
    """Assinatura estatística de cada número: quem costuma vestir, quanto joga, marca e é advertido."""
    p = partidas[partidas["numero"].notna() & partidas["jogou"]].copy()
    if p.empty:
        return pd.DataFrame()
    p["numero"] = p["numero"].astype(int)
    g = p.groupby("numero")
    t = g.agg(Jogos=("jogo_id", "count"), Titular=("titular", "mean"), Goleiro=("goleiro", "mean"),
              Gols=("gols", "sum"), Amarelos=("amarelos", "sum"), Minutos=("minutos", "mean"),
              Atletas=("atleta_id", "nunique")).reset_index()
    t = t[t["Jogos"] >= minimo_jogos]
    t["% titular"] = (t["Titular"] * 100).round(0)
    t["% goleiro"] = (t["Goleiro"] * 100).round(0)
    t["Gols/jogo"] = (t["Gols"] / t["Jogos"]).round(3)
    t["Amarelos/jogo"] = (t["Amarelos"] / t["Jogos"]).round(3)
    t["Minutos médios"] = t["Minutos"].round(0)
    t["Zona (convenção)"] = t["numero"].map(lambda n: CONVENCAO.get(n, ("Variável", ""))[0])
    t["Função provável"] = t["numero"].map(funcao_provavel)
    # o que os dados dizem: zona pelo comportamento (goleiro pelo flag; resto por gols e cartões)
    med_g, med_a = t["Gols/jogo"].median(), t["Amarelos/jogo"].median()

    def leitura(r):
        if r["% goleiro"] >= 50:
            return "Goleiro"
        if r["Gols/jogo"] >= max(med_g * 1.6, 0.12):
            return "Ataque"
        if r["Amarelos/jogo"] >= med_a * 1.15 and r["Gols/jogo"] < med_g * 1.2:
            return "Defesa/Meio marcador"
        return "Meio / misto"
    t["Leitura dos dados"] = t.apply(leitura, axis=1)
    cols = ["numero", "Função provável", "Zona (convenção)", "Jogos", "Atletas", "% titular", "Minutos médios", "% goleiro",
            "Gols/jogo", "Amarelos/jogo", "Leitura dos dados"]
    return t[cols].rename(columns={"numero": "Camisa"}).sort_values("Camisa").reset_index(drop=True)


def numeracao_dos_atletas(partidas: pd.DataFrame) -> pd.DataFrame:
    """Número mais usado por atleta e o quanto ele é 'fixo' (% dos jogos com aquela camisa)."""
    p = partidas[partidas["numero"].notna() & partidas["jogou"]].copy()
    p["numero"] = p["numero"].astype(int)
    g = p.groupby(["atleta_id", "numero"]).size().rename("n").reset_index()
    tot = g.groupby("atleta_id")["n"].sum().rename("total")
    top = g.sort_values("n", ascending=False).drop_duplicates("atleta_id").set_index("atleta_id")
    out = top.join(tot)
    out["fixo_pct"] = (out["n"] / out["total"] * 100).round(0)
    out["numeros_usados"] = g.groupby("atleta_id")["numero"].nunique()
    return out.reset_index().rename(columns={"numero": "camisa_principal"})[
        ["atleta_id", "camisa_principal", "fixo_pct", "numeros_usados", "total"]]


# ---------------------------------------------------------------- padrão de numeração e campo (leitura da súmula)
LADO = {6: 0, 11: 0, 16: 0, 14: 1, 12: 2, 4: 3, 10: 4, 5: 4, 9: 5, 8: 5, 18: 5, 19: 5, 20: 5, 21: 5, 3: 6, 15: 6,
        13: 7, 17: 8, 7: 9, 2: 9}
Y_ZONA = {"Goleiro": 9, "Defesa": 29, "Meio": 54, "Ataque": 79}


def formacao(escalacao: pd.DataFrame) -> dict:
    """Conta as zonas (defesa/meio/ataque) pela numeração dos 10 titulares de linha. ATENÇÃO: com a numeração
    tradicional o resultado é sempre 4-3-3 — mede o padrão de camisas, não o desenho tático. Retorna {'desenho': '4-3-3', 'confianca': 90, 'nivel': 'Alta', 'convencionais': 9}."""
    linha = escalacao[(escalacao["titular"]) & (~escalacao["goleiro"])]
    if len(linha) < 8:
        return {"desenho": "—", "confianca": 0, "nivel": "Sem dados", "convencionais": 0}
    zonas = linha["numero"].map(lambda n: zona(n, False))
    z = zonas.value_counts()
    d, m, a, v = int(z.get("Defesa", 0)), int(z.get("Meio", 0)), int(z.get("Ataque", 0)), int(z.get("Variável", 0))
    conv = int(linha["numero"].apply(lambda n: pd.notna(n) and 2 <= int(n) <= 11).sum())
    conf = round(conv / len(linha) * 100)
    nivel = "Alta" if conf >= 90 else "Média" if conf >= 70 else "Baixa"
    desenho = f"{d}-{m}-{a}" + (f" (+{v})" if v else "")
    return {"desenho": desenho, "confianca": conf, "nivel": nivel, "convencionais": conv}


def posicoes_no_campo(escalacao: pd.DataFrame) -> pd.DataFrame:
    """Coordenadas (x 0-100 esquerda→direita, y 0-100 do próprio gol ao gol adversário) de cada titular."""
    t = escalacao[escalacao["titular"]].copy()
    t["zona"] = t.apply(lambda r: zona(r["numero"], bool(r["goleiro"])), axis=1)
    t["ordem_x"] = t["numero"].map(lambda n: LADO.get(int(n), 5) if pd.notna(n) else 5)
    linhas = []
    for z, y in Y_ZONA.items():
        g = t[t["zona"] == z].sort_values(["ordem_x", "numero"])
        n = len(g)
        for i, r in enumerate(g.itertuples()):
            x = 50 if n == 1 else 12 + i * (76 / (n - 1))
            linhas.append({"numero": r.numero, "nome": r.nome, "zona": z, "x": x, "y": y})
    resto = t[t["zona"] == "Variável"].sort_values("numero")
    for i, r in enumerate(resto.itertuples()):  # fora da convenção: faixa lateral inferior
        linhas.append({"numero": r.numero, "nome": r.nome, "zona": "Variável", "x": 8 + i * 12, "y": 41})
    return pd.DataFrame(linhas)


def padrao_de_numeracao(escalacao: pd.DataFrame) -> dict:
    """Quanto a escalação segue a numeração tradicional (camisas 2–11 entre os 10 titulares de linha).
    NÃO indica o desenho tático: ver campo.py."""
    f = formacao(escalacao)
    linha = escalacao[(escalacao["titular"]) & (~escalacao["goleiro"])]
    z = linha["numero"].map(lambda n: zona(n, False)).value_counts()
    dist = " · ".join(f"{int(z.get(k, 0))} {k.lower()}" for k in ("Defesa", "Meio", "Ataque"))
    if int(z.get("Variável", 0)):
        dist += f" · {int(z.get('Variável', 0))} fora da convenção"
    return {"nivel": f["nivel"], "convencionais": f["convencionais"], "total": len(linha), "distribuicao": dist}
