"""Padronizacao de nomes de times e de atletas (as sumulas da FGF sao inconsistentes:
MAIUSCULAS/minusculas, apelidos e nomes cortados com ' ...', sufixo ' / RS', etc.)."""

from __future__ import annotations

import re
import unicodedata

PARTICULAS = {"da", "das", "de", "del", "do", "dos", "e", "di", "du", "van", "von", "la", "le"}
SIGLAS_MANTER = {"FC", "EC", "SC", "SAF", "GA", "VA", "AEF", "AD", "EE", "CT"}


def sem_acento(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def _chave(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sem_acento(s).lower()).strip()


# chave (sem acento, minuscula) -> nome canonico. O que nao estiver aqui so passa
# pela limpeza generica (tira UF e espacos duplicados).
ALIASES_TIME = {
    "gremio esportivo brasil saf": "Brasil de Pelotas",
    "brasil saf": "Brasil de Pelotas",
    "brasil": "Brasil de Pelotas",
    "brasil de pelotas": "Brasil de Pelotas",
    "gremio": "Grêmio",
    "gloria": "Glória",
    "apafut": "Apafut",
    "guarani va": "Guarani-VA",
    "guarany": "Guarany de Bagé",
    "guarany fc": "Guarany de Bagé",
    "internacional sm": "Internacional-SM",
    "monsoon fc": "Monsoon",
    "ec novo horizonte": "Novo Horizonte",
    "futebol com vida s a f": "Futebol Com Vida",
    "anp esportes parai": "ANP Esportes Paraí",
    "ga farroupilha": "GA Farroupilha",
    "ser panambi": "Panambi",
    "s e r cruz alta": "Cruz Alta",
    "fbc riograndense": "Riograndense",
    "real sc": "Real SC",
    "as mina de candiota fc": "As Mina de Candiota",
    "associacao as mina de candiota futebol clube": "As Mina de Candiota",
    "ec flamengo de sao pedro": "Flamengo de São Pedro",
    "ec uniao forquetense": "União Forquetense",
    "ec mar azul": "Mar Azul",
    "aef estrela": "AEF Estrela",
    "associacao esportiva do vale do taquari": "AE Vale do Taquari",
    "doutor salome goulart raiz": "Doutor Salomé Goulart Raiz",
}


def limpa_time(nome: str | None) -> str | None:
    if not nome:
        return nome
    n = re.sub(r"\s*/\s*[A-Za-z]{2}\s*$", "", nome).strip()
    n = re.sub(r"\s+", " ", n)
    return ALIASES_TIME.get(_chave(n), n)


def eh_truncado(s: str | None) -> bool:
    return bool(s) and s.strip().endswith("...")


def _capitaliza(palavra: str, primeira: bool) -> str:
    if palavra.upper() in SIGLAS_MANTER:
        return palavra.upper()
    baixa = palavra.lower()
    if not primeira and baixa in PARTICULAS:
        return baixa
    # partes separadas por hifen / apostrofo: "jean-pierre", "d'avila"
    return re.sub(r"[a-zà-ÿ]+", lambda m: m.group(0).capitalize(), baixa)


def nome_proprio(s: str | None) -> str:
    """'JOÃO da SILVA ...' -> 'João da Silva' (remove marcador de corte e padroniza a caixa)."""
    if not s:
        return ""
    s = re.sub(r"\s*\.\.\.\s*$", "", s.strip())
    s = re.sub(r"\s+", " ", s)
    palavras = s.split(" ")
    return " ".join(_capitaliza(p, i == 0) for i, p in enumerate(palavras))


def compativeis(curto: str, longo: str) -> bool:
    """O nome cortado ('Rodrigo Mi') e prefixo do completo ('Rodrigo Milani Souza')?"""
    a, b = _chave(curto), _chave(longo)
    return bool(a) and (b.startswith(a) or a in b)
