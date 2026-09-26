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


def formacao_por_numeracao(escalacao: pd.DataFrame) -> str:
    """Estimativa do desenho ('4-3-3') a partir das camisas dos 10 titulares de linha (convenção)."""
    linha = escalacao[(escalacao["titular"]) & (~escalacao["goleiro"])]
    if len(linha) < 8:
        return "—"
    z = linha.apply(lambda r: zona(r["numero"], False), axis=1).value_counts()
    d, m, a = int(z.get("Defesa", 0)), int(z.get("Meio", 0)), int(z.get("Ataque", 0))
    resto = int(z.get("Variável", 0))
    return f"{d}-{m}-{a}" + (f" (+{resto} fora da convenção)" if resto else "")


def insights_camisas(perfil: pd.DataFrame) -> list[str]:
    """Frases automáticas sobre o que a numeração revela nos dados."""
    if perfil.empty:
        return []
    out = []
    tit = perfil[perfil["Camisa"] <= 11]
    gk = perfil[perfil["% goleiro"] >= 90]
    if len(gk):
        out.append("**Goleiros:** camisa(s) " + ", ".join(str(n) for n in gk["Camisa"]) + " — "
                   f"a 1 é goleiro em {perfil.loc[perfil['Camisa'] == 1, '% goleiro'].max():.0f}% das vezes.")
    if len(tit):
        top = tit.sort_values("Gols/jogo", ascending=False).iloc[0]
        base = tit[tit["Camisa"].isin([2, 3, 4, 6])]["Gols/jogo"].mean()
        mult = f" — {top['Gols/jogo'] / base:.0f}× mais que a média dos defensores (2, 3, 4 e 6)" if base and base > 0 else ""
        out.append(f"**Quem mais marca:** a camisa {int(top['Camisa'])} ({top['Gols/jogo']:.2f} gols por jogo){mult}.")
        cart = tit[tit["% goleiro"] < 50].sort_values("Amarelos/jogo", ascending=False).iloc[0]
        out.append(f"**Mais advertida:** a camisa {int(cart['Camisa'])} ({cart['Amarelos/jogo']:.2f} amarelos por jogo).")
    res = perfil[(perfil["Camisa"] >= 12) & (perfil["Camisa"] <= 22)]
    if len(res):
        out.append(f"**Reservas:** as camisas 12–22 começam o jogo em média em {res['% titular'].mean():.0f}% das vezes; "
                   f"as 1–11, em {tit['% titular'].mean():.0f}%.")
    livres = perfil[perfil["Camisa"] >= 23]
    if len(livres):
        out.append("**Numeração livre (23+):** aparecem com frequência, mas não seguem a convenção de posição — "
                   "por isso a convenção vale sobretudo para as camisas 1 a 22.")
    return out
