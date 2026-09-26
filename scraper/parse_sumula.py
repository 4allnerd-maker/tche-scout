"""
Extrai dados estruturados de uma sumula on-line da FGF (PDF) para um dict.

Estrategia: a sumula e gerada por um template fixo do sistema da FGF, com
tabelas bem demarcadas por bordas. Usamos pdfplumber.extract_tables() (nao
regex sobre texto corrido) porque a "Relacao de Jogadores" e outras secoes
sao duas colunas lado a lado (mandante | visitante) que o extract_text()
simples embaralha.

Cada "caixa" com borda no PDF vira uma tabela separada para o pdfplumber —
por isso cartoes (amarelos/vermelhos) aparecem como varias mini-tabelas (uma
por cartao, por causa da linha de "Motivo" dentro da propria caixa). O parser
trata isso com uma maquina de estados: percorre todas as tabelas de todas as
paginas em ordem e alterna de "secao" sempre que encontra uma tabela cuja
primeira linha e um titulo conhecido (celula unica nao-nula).

Limitacao conhecida da fonte: "Nome Completo" na Relacao de Jogadores vem
truncado ("Davi Carlos da Costa ...") pela largura da coluna no PDF. O
"Apelido" costuma vir completo e o "CBF" (numero de registro na CBF) e
estavel -> usar CBF como chave primaria de jogador entre jogos/temporadas,
nao o nome.
"""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path

import pdfplumber

SECTION_TITLES = {
    "Arbitragem",
    "Cronologia",
    "Relação de Jogadores",
    "Comissão Técnica",
    "Gols",
    "Cartões Amarelos",
    "Cartões Vermelhos",
    "Ocorrências / Observações",
    "Observações Eventuais",
    "Substituições",
}

JOGADOR_HEADER = {"Nº", "Apelido", "Nome Completo", "T/R", "P/A", "CBF"}
CARTAO_HEADER = {"Tempo", "1T/2T", "Nº", "Nome do Jogador", "Equipe"}
GOL_HEADER = {"Tempo", "1T/2T", "Nº", "Tipo", "Nome do Jogador", "Equipe"}
SUB_HEADER = {"Tempo", "1T/2T", "Equipe", "Entrou", "Saiu"}


def _clean(s) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _is_title_row(row) -> str | None:
    non_null = [c for c in row if c not in (None, "")]
    if len(non_null) == 1 and _clean(non_null[0]) in SECTION_TITLES:
        return _clean(non_null[0])
    return None


def _is_header_row(row, header_set) -> bool:
    cells = {_clean(c) for c in row if c not in (None, "")}
    return bool(cells) and cells.issubset(header_set) and len(cells) >= 2


def _split_entrada(texto: str) -> tuple:
    m = re.match(r"\s*(\d+)\s*-\s*(.+)", texto or "")
    if m:
        return int(m.group(1)), _clean(m.group(2))
    return None, _clean(texto)


_TR_RE = re.compile(r"^[TR](\(g\))?$")


def _roster_por_palavras(pdf_path, mandante, visitante):
    """Relê a 'Relação de Jogadores' pela POSIÇÃO das palavras na página (alguns PDFs quebram a tabela em
    duas e perdem a coluna CBF). Retorna [] se o resultado não parecer uma escalação válida."""
    jogadores = []
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            linhas = {}
            for w in pg.extract_words():
                linhas.setdefault(round(w["top"] / 3), []).append(w)
            chaves = sorted(linhas)
            cab = None
            for k in chaves:
                ws = sorted(linhas[k], key=lambda w: w["x0"])
                if " ".join(w["text"] for w in ws).startswith("Nº Apelido Nome Completo T/R P/A CBF Nº"):
                    cab = (k, ws)
                    break
            if not cab:
                continue
            k0, ws0 = cab
            corte = [w["x0"] for w in ws0 if w["text"] == "Nº"][1] - 6
            for k in chaves:
                if k <= k0:
                    continue
                ws = sorted(linhas[k], key=lambda w: w["x0"])
                if re.match(r"^(Comissão Técnica|Gols|Cartões|Substituições|Ocorrências|T = Titular)",
                            " ".join(w["text"] for w in ws)):
                    break
                for lado, equipe in ((0, mandante), (1, visitante)):
                    toks = [w for w in ws if (w["x0"] < corte if lado == 0 else w["x0"] >= corte)]
                    if len(toks) < 3:
                        continue
                    cbf = pa = tr = None
                    if re.fullmatch(r"\d{4,9}", toks[-1]["text"]):
                        cbf = toks.pop()["text"]
                    if toks and toks[-1]["text"] in ("P", "A"):
                        pa = toks.pop()["text"]
                    if toks and _TR_RE.match(toks[-1]["text"]):
                        tr = toks.pop()["text"]
                    if not tr:
                        continue
                    numero = None
                    if toks and re.fullmatch(r"\d{1,3}", toks[0]["text"]):
                        numero = int(toks.pop(0)["text"])
                    corte_nome = len(toks)
                    if len(toks) > 1:
                        gaps = [toks[i + 1]["x0"] - toks[i]["x1"] for i in range(len(toks) - 1)]
                        m = max(range(len(gaps)), key=lambda i: gaps[i])
                        if gaps[m] > 3.6:
                            corte_nome = m + 1
                    apelido = " ".join(t["text"] for t in toks[:corte_nome])
                    nome = " ".join(t["text"] for t in toks[corte_nome:])
                    jogadores.append({
                        "equipe": equipe, "numero": numero, "apelido": _clean(apelido), "nome_completo": _clean(nome),
                        "titular": tr.startswith("T"), "goleiro": "(g)" in tr,
                        "categoria": "Profissional" if pa == "P" else "Amador", "cbf_id": cbf,
                    })
    # validação: cada time precisa ter de 9 a 12 titulares
    for equipe in (mandante, visitante):
        n = sum(1 for j in jogadores if j["equipe"] == equipe and j["titular"])
        if not 9 <= n <= 12:
            return []
    return jogadores


def parse_sumula_pdf(pdf_path) -> dict:
    with pdfplumber.open(pdf_path) as pdf:
        all_tables = []
        for page in pdf.pages:
            all_tables.extend(page.extract_tables())

    jogo_id = Path(pdf_path).stem
    data = {
        "jogo_id": jogo_id,
        "campeonato": None,
        "rodada": None,
        "time_mandante": None,
        "time_visitante": None,
        "data": None,
        "horario": None,
        "estadio": None,
        "arbitragem": {},
        "resultado_1t_mandante": None,
        "resultado_1t_visitante": None,
        "resultado_final_mandante": None,
        "resultado_final_visitante": None,
        "jogadores": [],
        "comissao_tecnica": [],
        "gols": [],
        "cartoes_amarelos": [],
        "cartoes_vermelhos": [],
        "substituicoes": [],
    }

    if not all_tables:
        return data

    # ---- Tabela 0 (sem titulo): Campeonato/Rodada, Jogo, Data/Horario/Estadio ----
    for row in all_tables[0]:
        cells = [c for c in row if c not in (None, "")]
        joined = " ".join(_clean(c) for c in cells)
        if joined.startswith("Campeonato:"):
            m = re.search(r"Campeonato:\s*(.+?)\s+Rodada:\s*(\S+)", joined)
            if m:
                data["campeonato"] = m.group(1).strip()
                data["rodada"] = m.group(2).strip()
        elif joined.startswith("Jogo:"):
            m = re.search(r"Jogo:\s*(.+?)\s+X\s+(.+)", joined)
            if m:
                data["time_mandante"] = m.group(1).strip()
                data["time_visitante"] = m.group(2).strip()
        elif joined.startswith("Data:"):
            m = re.search(
                r"Data:\s*(\d{2}/\d{2}/\d{4})\s+Hor[aá]rio:\s*(\d{2}:\d{2})\s+Est[aá]dio:\s*(.+)",
                joined,
            )
            if m:
                data["data"], data["horario"], data["estadio"] = (
                    m.group(1),
                    m.group(2),
                    m.group(3).strip(),
                )

    section = None
    cartao_equipe_idx = {}  # secao -> bool se ha coluna Equipe
    equipe_atual = None  # layout B da relacao de jogadores (um time por tabela)
    roster_b = False     # True se a tabela de jogadores veio quebrada (layout B): relê por posição das palavras

    for table in all_tables[1:]:
        if not table:
            continue
        title = _is_title_row(table[0])
        rows = table[1:] if title else table
        if title:
            section = title
        if section is None or not rows:
            continue

        if section == "Arbitragem":
            for row in rows:
                cells = [c for c in row if c not in (None, "")]
                if len(cells) >= 2:
                    label = _clean(cells[0]).rstrip(":")
                    data["arbitragem"][label] = _clean(cells[1])

        elif section == "Cronologia":
            for row in rows:
                joined = " ".join(_clean(c) for c in row if c not in (None, ""))
                if joined.startswith("Resultado do 1"):
                    m = re.search(
                        r"Resultado do 1[ºo] Tempo:\s*(\d+)\s*X\s*(\d+).*?"
                        r"Resultado Final:\s*(\d+)\s*X\s*(\d+)",
                        joined,
                    )
                    if m:
                        data["resultado_1t_mandante"] = int(m.group(1))
                        data["resultado_1t_visitante"] = int(m.group(2))
                        data["resultado_final_mandante"] = int(m.group(3))
                        data["resultado_final_visitante"] = int(m.group(4))

        elif section == "Relação de Jogadores":
            def _add_jogador(equipe_nome, cols):
                numero, apelido, nome_completo, t_r, p_a, cbf = (list(cols) + [None] * 6)[:6]
                # jogador sem numero na sumula (acontece): mantem se tiver nome ou registro CBF
                if not numero and not (_clean(cbf) or len(_clean(apelido)) > 1):
                    return
                numero = numero or ""
                titular_raw = _clean(t_r)
                data["jogadores"].append({
                    "equipe": equipe_nome,
                    "numero": int(_clean(numero)) if _clean(numero).isdigit() else None,
                    "apelido": _clean(apelido),
                    "nome_completo": _clean(nome_completo),
                    "titular": titular_raw.startswith("T"),
                    "goleiro": "(g)" in titular_raw,
                    "categoria": "Profissional" if _clean(p_a) == "P" else "Amador",
                    "cbf_id": _clean(cbf) or None,
                })

            for row in rows:
                non_null_idx = [i for i, c in enumerate(row) if c not in (None, "")]
                if not non_null_idx:
                    continue
                # Layout B (visto em ~13% das sumulas, sobretudo 2024-25): 1 tabela POR TIME, 7 colunas
                # com a 1a vazia: [None, Nº, Apelido, Nome, T/R, P/A, CBF]; o nome do time vem numa linha propria.
                if len(row) == 5:  # metade do time quebrada em outra tabela, sem coluna CBF
                    roster_b = True
                    continue
                if len(row) == 7 and not _clean(row[0]):
                    roster_b = True
                    if len(non_null_idx) == 1:
                        equipe_atual = _clean(row[non_null_idx[0]])
                        continue
                    if _is_header_row(row, JOGADOR_HEADER):
                        continue
                    _add_jogador(equipe_atual or data["time_mandante"], row[1:7])
                    continue
                if _is_header_row(row, JOGADOR_HEADER):
                    continue
                # linha com nomes dos times (2 celulas de texto, nao numericas)
                if len(non_null_idx) == 2 and not re.match(r"^\d+$", _clean(row[non_null_idx[0]])):
                    data["time_mandante"] = data["time_mandante"] or _clean(row[non_null_idx[0]])
                    data["time_visitante"] = data["time_visitante"] or _clean(row[non_null_idx[1]])
                    continue
                ncols = len(row)
                half = ncols // 2
                for equipe_nome, cols in (
                    (data["time_mandante"], row[:half]),
                    (data["time_visitante"], row[half:]),
                ):
                    if not any(c not in (None, "") for c in cols):
                        continue
                    _add_jogador(equipe_nome, cols)

        elif section == "Comissão Técnica":
            for row in rows:
                non_null_idx = [i for i, c in enumerate(row) if c not in (None, "")]
                if not non_null_idx:
                    continue
                if len(non_null_idx) == 2 and _clean(row[non_null_idx[0]]) in (
                    data["time_mandante"], data["time_visitante"]
                ):
                    continue
                ncols = len(row)
                half = ncols // 2
                for equipe_nome, cols in (
                    (data["time_mandante"], row[:half]),
                    (data["time_visitante"], row[half:]),
                ):
                    if len(cols) < 2 or not cols[0]:
                        continue
                    data["comissao_tecnica"].append({
                        "equipe": equipe_nome,
                        "funcao": _clean(cols[0]).rstrip(":"),
                        "nome": _clean(cols[1]),
                    })

        elif section == "Gols":
            for row in rows:
                if _is_header_row(row, GOL_HEADER):
                    continue
                cells = [_clean(c) for c in row]
                if len(cells) < 6 or not cells[0] or cells[0].upper().startswith("NÃO HOUVE"):
                    continue
                tempo, periodo, numero, tipo, jogador, equipe = cells[:6]
                data["gols"].append({
                    "tempo": tempo,
                    "periodo": periodo,
                    "numero": int(numero) if numero.isdigit() else None,
                    "tipo": tipo,
                    "jogador": jogador,
                    "equipe": equipe,
                })

        elif section in ("Cartões Amarelos", "Cartões Vermelhos"):
            key = "cartoes_amarelos" if section == "Cartões Amarelos" else "cartoes_vermelhos"
            for row in rows:
                if _is_header_row(row, CARTAO_HEADER):
                    continue
                cells = [_clean(c) for c in row]
                non_empty = [c for c in cells if c]
                if len(non_empty) == 1 and non_empty[0].upper().startswith("NÃO HOUVE"):
                    continue
                # linha de "Motivo: ..." -> continuacao do ultimo cartao
                if not cells[0] and len(non_empty) == 1:
                    if data[key]:
                        prev = data[key][-1].get("motivo", "")
                        data[key][-1]["motivo"] = (prev + " " + non_empty[0]).strip()
                    continue
                if not cells[0] or len(cells) < 3:
                    continue
                # Vermelhos: a linha 2 do cartao traz o TIPO na 1a celula ("Cartão Vermelho Direto" /
                # "2º Cartão Amarelo") e o "Motivo: ..." na 4a — nao e um novo cartao.
                if not re.match(r"^\+?\d+:\d+$", cells[0]):
                    if data[key]:
                        data[key][-1]["detalhe"] = cells[0]
                        resto = " ".join(c for c in cells[1:] if c)
                        if resto:
                            data[key][-1]["motivo"] = (data[key][-1].get("motivo", "") + " " + resto).strip()
                    continue
                tempo, periodo, numero = cells[0], cells[1], cells[2]
                jogador = cells[3] if len(cells) > 3 else None
                equipe = cells[4] if len(cells) > 4 else None
                if jogador and not equipe and " - " in jogador:  # vermelhos: "Nome - Equipe" na mesma celula
                    jogador, equipe = [p.strip() for p in jogador.rsplit(" - ", 1)]
                data[key].append({
                    "tempo": tempo,
                    "periodo": periodo,
                    "numero": int(numero) if numero.isdigit() else None,
                    "jogador": jogador,
                    "equipe": equipe,
                    "motivo": "",
                    "detalhe": "",
                })

        elif section == "Substituições":
            for row in rows:
                if _is_header_row(row, SUB_HEADER):
                    continue
                cells = [_clean(c) for c in row]
                if len(cells) < 5 or not cells[0]:
                    continue
                tempo, periodo, equipe, entrou_raw, saiu_raw = cells[:5]
                entrou_num, entrou_nome = _split_entrada(entrou_raw)
                saiu_num, saiu_nome = _split_entrada(saiu_raw)
                data["substituicoes"].append({
                    "tempo": tempo,
                    "periodo": periodo,
                    "equipe": equipe,
                    "entrou_numero": entrou_num,
                    "entrou": entrou_nome,
                    "saiu_numero": saiu_num,
                    "saiu": saiu_nome,
                })

    if roster_b:
        novo = _roster_por_palavras(pdf_path, data["time_mandante"], data["time_visitante"])
        if novo:
            data["jogadores"] = novo

    _normalize_equipes(data)
    return data


def _normalize_equipes(data: dict) -> None:
    """As colunas 'Equipe' de gols/cartoes/substituicoes vem truncadas pela
    largura da coluna no PDF (ex: 'Gremio Esportivo Brasil SAF -' ou
    'Gremio Esportivo Brasil SAF ...'). Aqui trocamos pelo nome completo do
    mandante/visitante (extraido do cabecalho, sempre completo)."""
    mandante, visitante = data["time_mandante"], data["time_visitante"]
    if not mandante or not visitante:
        return

    def match(raw: str | None) -> str | None:
        if not raw:
            return raw
        base = re.sub(r"[\s./\-]+$", "", raw)
        base = re.sub(r"\s*\.\.\.$", "", base).strip()
        if not base:
            return raw
        if mandante.startswith(base) or base.startswith(mandante.split(" /")[0].split(" -")[0]):
            return mandante
        if visitante.startswith(base) or base.startswith(visitante.split(" /")[0].split(" -")[0]):
            return visitante
        return raw

    for lst_key in ("gols", "cartoes_amarelos", "cartoes_vermelhos", "substituicoes"):
        for item in data[lst_key]:
            item["equipe"] = match(item.get("equipe"))


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/sumulas/56412.pdf"
    result = parse_sumula_pdf(path)
    out_path = Path("scratch_parsed.json")
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK -> {out_path} ({len(result['jogadores'])} jogadores, {len(result['gols'])} gols, "
          f"{len(result['cartoes_amarelos'])} amarelos, {len(result['substituicoes'])} subs)")
