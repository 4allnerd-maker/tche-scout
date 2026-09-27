"""
Le as sumulas (PDF ou cache em data/parsed/), padroniza nomes de times e atletas e
gera os datasets que o app consome, em data/processed/:

  jogos.json              1 linha por jogo COM resultado (sumula ou W.O.)
  calendario.json         todos os jogos do site (realizados, W.O., cancelados, futuros)
  jogadores_partida.json  1 linha por atleta relacionado em cada jogo (jogou, minutos,
                          gols, cartoes, entrou/saiu...)
  atletas.json            cadastro dos atletas (nome padronizado, chave = registro CBF)
  gols.json / cartoes.json / substituicoes.json   eventos, ja ligados ao atleta
  meta.json               data da geracao e contagens

O cache data/parsed/{id}.json evita reler os PDFs a cada execucao (o robo diario so
processa as sumulas novas).

Uso: python scraper/build_dataset.py
"""

from __future__ import annotations

import json

import pandas as pd
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import posicoes as posicoes_mod  # noqa: E402
from nomes import compativeis, eh_truncado, limpa_time, nome_proprio, pessoa
from parse_sumula import parse_sumula_pdf

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "data" / "raw" / "games_index.json"
SUMULAS_DIR = ROOT / "data" / "raw" / "sumulas"
CACHE_DIR = ROOT / "data" / "parsed"
OUT_DIR = ROOT / "data" / "processed"

IDS_FEMININO = {59, 564, 708, 803}
DURACAO = 90
PARSER_VERSAO = 6  # aumente ao mudar parse_sumula.py: invalida o cache data/parsed


def minuto_absoluto(tempo, periodo) -> float | None:
    """'35:00' + periodo 1/2/'1T'/'2T'/'INT' -> minuto absoluto (0-90+). '+06:00' = acrescimo."""
    p = str(periodo).strip().upper()
    if p == "INT":
        return 45.0
    m = re.match(r"^\+?(\d+):(\d+)$", str(tempo or "").strip())
    if not m:
        return None
    minutos = int(m.group(1)) + int(m.group(2)) / 60
    segundo = p in ("2", "2T")
    if str(tempo).strip().startswith("+"):
        return (90 if segundo else 45) + minutos
    return (45 if segundo else 0) + minutos


def _parse_e_grava(sid: str):
    pdf = SUMULAS_DIR / f"{sid}.pdf"
    try:
        parsed = parse_sumula_pdf(pdf)
    except Exception as e:  # noqa: BLE001
        return sid, None, str(e)
    parsed["_v"] = PARSER_VERSAO
    (CACHE_DIR / f"{sid}.json").write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")
    return sid, parsed, None


def _cache_valido(sid: str) -> bool:
    cache = CACHE_DIR / f"{sid}.json"
    if not cache.exists():
        return False
    try:
        return json.loads(cache.read_text(encoding="utf-8")).get("_v") == PARSER_VERSAO
    except ValueError:
        return False


def preparar_cache(sids: list[str]) -> dict:
    """Le em paralelo os PDFs sem cache valido. Retorna {sid: mensagem_de_erro}."""
    pendentes = [s for s in sids if not _cache_valido(s) and (SUMULAS_DIR / f"{s}.pdf").exists()]
    erros = {}
    if not pendentes:
        return erros
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    from concurrent.futures import ProcessPoolExecutor
    import os
    workers = max(1, min(8, (os.cpu_count() or 2) - 1))
    print(f"Lendo {len(pendentes)} PDFs novos/atualizados com {workers} processos...", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, (sid, parsed, erro) in enumerate(ex.map(_parse_e_grava, pendentes, chunksize=4), 1):
            if erro:
                erros[sid] = erro
            if i % 100 == 0:
                print(f"  ... {i}/{len(pendentes)} PDFs lidos", flush=True)
    return erros


def parse_cacheado(sid: str) -> dict | None:
    cache = CACHE_DIR / f"{sid}.json"
    return json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else None


def grava(nome: str, registros: list | dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if isinstance(registros, list):  # um registro por linha: diffs do git legiveis
        texto = "[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in registros) + "\n]\n"
    else:
        texto = json.dumps(registros, ensure_ascii=False, indent=1)
    (OUT_DIR / f"{nome}.json").write_text(texto, encoding="utf-8")


def categoria_do(meta: dict) -> str:
    return "Feminino" if meta["competicao_id"] in IDS_FEMININO or meta.get("categoria") == "feminino" else "Masculino"


def main():
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    entradas = list(index.values())

    jogos, calendario = [], []
    partidas, gols_out, cartoes_out, subs_out = [], [], [], []
    ident = defaultdict(lambda: {"apelidos": Counter(), "apelidos_trunc": Counter(), "nomes_evento": Counter(),
                                  "nomes_roster": Counter(), "nomes_trunc": Counter(), "equipes": Counter(),
                                  "categorias": Counter(), "goleiro": Counter()})
    erros = [(sid, msg) for sid, msg in preparar_cache([e["sumula_id"] for e in entradas if e.get("sumula_id")]).items()]

    for n, meta in enumerate(entradas, 1):
        sid = meta.get("sumula_id")
        categoria = categoria_do(meta)
        base_cal = {
            "competicao_id": meta["competicao_id"], "competicao_nome": meta["competicao_nome"],
            "categoria": categoria, "ano": meta["ano"], "fase_nome": meta["fase_nome"], "slug": meta["slug"],
        }

        if not sid:  # sem sumula: W.O., cancelado, futuro...
            sit = meta.get("situacao")
            if sit == "SEM_DADOS" or not sit:
                continue
            mand, visit = limpa_time(meta.get("mandante")), limpa_time(meta.get("visitante"))
            cal = {**base_cal, "jogo_id": f"s-{meta['slug']}", "rodada": None, "data": meta.get("data"),
                   "hora": meta.get("hora"), "estadio": meta.get("estadio"),
                   "time_mandante": mand, "time_visitante": visit,
                   "gols_mandante": meta.get("placar_mandante"), "gols_visitante": meta.get("placar_visitante"),
                   "situacao": {"A_REALIZAR": "A realizar", "WO": "W.O.", "CANCELADO": "Cancelado",
                                "SEM_SUMULA": "Realizado (sem súmula)"}.get(sit, sit)}
            calendario.append(cal)
            if sit == "WO":  # W.O.: vitoria por 3x0 para quem compareceu — conta na classificacao
                jogos.append({**{k: cal[k] for k in ("jogo_id", "competicao_id", "competicao_nome", "categoria", "ano",
                                                       "fase_nome", "rodada", "data", "hora", "estadio",
                                                       "time_mandante", "time_visitante", "gols_mandante", "gols_visitante")},
                              "gols_1t_mandante": None, "gols_1t_visitante": None, "arbitro": None, "situacao": "W.O.", "sumula_url": None})
            continue

        try:
            d = parse_cacheado(sid)
        except Exception as e:
            erros.append((sid, str(e)))
            continue
        if not d or not d.get("time_mandante"):
            erros.append((sid, "sem dados/times"))
            continue

        mand, visit = limpa_time(d["time_mandante"]), limpa_time(d["time_visitante"])
        jogo = {
            "jogo_id": sid, "competicao_id": meta["competicao_id"], "competicao_nome": meta["competicao_nome"],
            "categoria": categoria, "ano": meta["ano"], "fase_nome": meta["fase_nome"], "rodada": d.get("rodada"),
            "data": d["data"], "hora": d.get("horario"), "estadio": d.get("estadio"),
            "time_mandante": mand, "time_visitante": visit,
            "gols_mandante": d["resultado_final_mandante"], "gols_visitante": d["resultado_final_visitante"],
            "gols_1t_mandante": d["resultado_1t_mandante"], "gols_1t_visitante": d["resultado_1t_visitante"],
            "situacao": "Realizado", "sumula_url": meta.get("sumula_url") or f"https://fgf.com.br/public/sumulas/{sid}.pdf",
            "acrescimo_1t": d.get("acrescimo_1t"), "acrescimo_2t": d.get("acrescimo_2t"),
        }
        arb = d.get("arbitragem") or {}
        for campo, papel in (("arbitro", "Árbitro"), ("assistente1", "Assistente 1"), ("assistente2", "Assistente 2"),
                             ("quarto_arbitro", "Quarto Árbitro"), ("var", "VAR"), ("avar", "AVAR")):
            nome, vinc = pessoa(arb.get(papel))
            jogo[campo] = nome
            if campo == "arbitro":
                jogo["arbitro_vinculo"] = vinc
        jogo["tem_var"] = bool(jogo["var"])
        jogos.append(jogo)
        calendario.append({**base_cal, **{k: jogo[k] for k in ("jogo_id", "rodada", "data", "hora", "estadio",
                                                               "time_mandante", "time_visitante",
                                                               "gols_mandante", "gols_visitante")},
                           "situacao": "Realizado"})

        # ---- atletas do jogo, indexados por (equipe, numero) ----
        roster = {}
        for j in d["jogadores"]:
            eq = limpa_time(j["equipe"])
            if not j.get("cbf_id") and len((j["apelido"] or "").strip()) < 2:
                continue  # linha lixo da tabela do PDF
            aid = j.get("cbf_id") or f"{eq}|{nome_proprio(j['apelido'])}"
            if any(r["atleta_id"] == aid and r["equipe"] == eq for r in roster.values()):
                continue  # linha repetida na sumula
            reg = {"jogo_id": sid, "atleta_id": aid, "equipe": eq, "numero": j["numero"],
                   "titular": bool(j["titular"]), "goleiro": bool(j["goleiro"]), "categoria": j.get("categoria"),
                   "entrou": False, "saiu": False, "min_entrada": 0.0 if j["titular"] else None, "min_saida": None,
                   "gols": 0, "gols_contra": 0, "amarelos": 0, "vermelhos": 0,
                   "_apelido": j["apelido"], "_nome": j["nome_completo"]}
            roster[(eq, j["numero"])] = reg
            partidas.append(reg)
            info = ident[aid]
            (info["apelidos_trunc"] if eh_truncado(j["apelido"]) else info["apelidos"])[nome_proprio(j["apelido"])] += 1
            (info["nomes_trunc"] if eh_truncado(j["nome_completo"]) else info["nomes_roster"])[nome_proprio(j["nome_completo"])] += 1
            info["equipes"][eq] += 1
            info["categorias"][j.get("categoria")] += 1
            info["goleiro"][bool(j["goleiro"])] += 1

        def acha(eq, numero, nome_evento=None):
            reg = roster.get((eq, numero))
            if reg is not None and nome_evento:
                ident[reg["atleta_id"]]["nomes_evento"][nome_proprio(nome_evento)] += 1
            return reg

        # ---- gols (trata gol contra: o time creditado e o adversario do atleta) ----
        for g in d["gols"]:
            eq = limpa_time(g["equipe"])
            outro = visit if eq == mand else mand
            contra = str(g["tipo"]).strip().upper() in ("CT", "GC") or "CONTRA" in str(g["tipo"]).upper()
            eq_atleta = eq
            if contra:  # a sumula pode listar o time do atleta ou o time creditado: confere pelo nome
                for cand in (eq, outro):
                    r = roster.get((cand, g["numero"]))
                    if r and any(compativeis(a, b) or compativeis(b, a) for a in (nome_proprio(r["_nome"]), nome_proprio(r["_apelido"]))
                                 for b in (nome_proprio(g["jogador"]),)):
                        eq_atleta = cand
                        break
            reg = acha(eq_atleta, g["numero"], g["jogador"])
            atleta_eq = reg["equipe"] if reg else eq
            creditada = (mand if atleta_eq == visit else visit) if contra else atleta_eq
            minuto = minuto_absoluto(g["tempo"], g["periodo"])
            if reg:
                reg["gols_contra" if contra else "gols"] += 1
            gols_out.append({"jogo_id": sid, "atleta_id": reg["atleta_id"] if reg else None,
                             "jogador": nome_proprio(g["jogador"]), "equipe": atleta_eq, "equipe_creditada": creditada,
                             "tipo": g["tipo"], "contra": contra, "minuto": minuto,
                             "periodo": 2 if str(g["periodo"]) in ("2", "2T") else 1})

        # ---- cartoes ----
        for chave, tipo in (("cartoes_amarelos", "amarelo"), ("cartoes_vermelhos", "vermelho")):
            for c in d[chave]:
                eq = limpa_time(c["equipe"])
                reg = acha(eq, c["numero"], c["jogador"])
                minuto = minuto_absoluto(c["tempo"], c["periodo"])
                if reg:
                    reg["amarelos" if tipo == "amarelo" else "vermelhos"] += 1
                    if tipo == "vermelho" and minuto is not None:
                        reg["min_saida"] = minuto if reg["min_saida"] is None else min(reg["min_saida"], minuto)
                cartoes_out.append({"jogo_id": sid, "atleta_id": reg["atleta_id"] if reg else None,
                                    "jogador": nome_proprio(c["jogador"]), "equipe": eq, "tipo": tipo, "minuto": minuto,
                                    "periodo": 2 if str(c["periodo"]) in ("2", "2T") else 1,
                                    "motivo": re.sub(r"^Motivo:\s*", "", c.get("motivo") or "").strip() or None,
                                    "detalhe": c.get("detalhe") or None, "comissao": c["numero"] is None})

        # ---- substituicoes ----
        for s in d["substituicoes"]:
            eq = limpa_time(s["equipe"])
            minuto = minuto_absoluto(s["tempo"], s["periodo"])
            ent = acha(eq, s["entrou_numero"], s["entrou"])
            sai = acha(eq, s["saiu_numero"], s["saiu"])
            if ent:
                ent["entrou"], ent["min_entrada"] = True, minuto
            if sai:
                sai["saiu"] = True
                sai["min_saida"] = minuto if sai["min_saida"] is None else min(sai["min_saida"], minuto or DURACAO)
            subs_out.append({"jogo_id": sid, "equipe": eq, "minuto": minuto,
                             "entrou_id": ent["atleta_id"] if ent else None, "entrou": nome_proprio(s["entrou"]),
                             "saiu_id": sai["atleta_id"] if sai else None, "saiu": nome_proprio(s["saiu"])})

        if n % 100 == 0:
            print(f"  ... {n}/{len(entradas)}", flush=True)

    # ---- cadastro padronizado de atletas ----
    atletas = []
    nome_de, exib_de = {}, {}
    for aid, info in ident.items():
        completos = info["nomes_evento"] or info["nomes_roster"] or info["nomes_trunc"]
        nome_completo = max(completos.items(), key=lambda kv: (len(kv[0].split()), kv[1], len(kv[0])))[0] if completos else ""
        cand = info["apelidos"] or info["apelidos_trunc"]
        # descarta variantes que sao so o comeco (cortado) de outra variante mais longa
        finais = {a: c for a, c in cand.items()
                  if not any(o != a and len(o) > len(a) and o.lower().startswith(a.lower()) for o in cand)}
        exibicao = max(finais.items(), key=lambda kv: (kv[1], len(kv[0])))[0] if finais else nome_completo
        if not info["apelidos"] and nome_completo:  # todos os apelidos vieram cortados
            palavras = nome_completo.split()
            exibicao = exibicao if compativeis(exibicao, nome_completo) and len(exibicao) > 12 else \
                (f"{palavras[0]} {palavras[-1]}" if len(palavras) > 1 else nome_completo)
        nome_de[aid], exib_de[aid] = nome_completo or exibicao, exibicao
        atletas.append({"atleta_id": aid, "nome": exibicao, "nome_completo": nome_completo or exibicao,
                        "equipe_principal": info["equipes"].most_common(1)[0][0],
                        "equipes": sorted(info["equipes"]), "goleiro": info["goleiro"].most_common(1)[0][0],
                        "categoria": info["categorias"].most_common(1)[0][0]})
    atletas.sort(key=lambda a: a["nome"].lower())

    # ---- finaliza jogador-partida (minutos jogados) ----
    for r in partidas:
        r["jogou"] = r["titular"] or r["entrou"]
        ini = r["min_entrada"] if r["min_entrada"] is not None else None
        fim = r["min_saida"] if r["min_saida"] is not None else DURACAO
        r["minutos"] = round(max(0.0, min(fim, DURACAO + 15) - ini), 1) if (r["jogou"] and ini is not None) else 0.0
        r["nome"] = exib_de.get(r["atleta_id"]) or nome_proprio(r["_apelido"])
        del r["_apelido"], r["_nome"]
    for lista in (gols_out, cartoes_out):
        for r in lista:
            if r["atleta_id"]:
                r["jogador"] = exib_de.get(r["atleta_id"], r["jogador"])

    jogos.sort(key=lambda j: (datetime.strptime(j["data"], "%d/%m/%Y") if j["data"] else datetime.max, j["jogo_id"]))
    calendario.sort(key=lambda j: (datetime.strptime(j["data"], "%d/%m/%Y") if j["data"] else datetime.max, j["jogo_id"]))
    for nome, dados in (("jogos", jogos), ("calendario", calendario), ("jogadores_partida", partidas),
                        ("atletas", atletas), ("gols", gols_out), ("cartoes", cartoes_out), ("substituicoes", subs_out)):
        grava(nome, dados)
    pos_df = posicoes_mod.consolidar(pd.DataFrame(partidas))
    grava("posicoes", pos_df.where(pos_df.notna(), None).to_dict("records"))
    grava("meta", {"gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"), "jogos": len(jogos),
                   "calendario": len(calendario), "atletas": len(atletas), "gols": len(gols_out),
                   "cartoes": len(cartoes_out), "substituicoes": len(subs_out)})

    print(f"OK: {len(jogos)} jogos com resultado | {len(calendario)} no calendario | {len(atletas)} atletas | "
          f"{len(gols_out)} gols | {len(cartoes_out)} cartoes | {len(subs_out)} substituicoes")
    if erros:
        print(f"Erros/pulos: {len(erros)}")
        for sid, msg in erros[:20]:
            print(f"  {sid}: {msg}")


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
