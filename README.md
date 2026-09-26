# Tchê Scout

Scout dos campeonatos gaúchos (FGF) a partir das súmulas oficiais: calendário, classificações,
perfil dos times, gols por minuto e base de atletas. **Não é um produto de apostas.**

## Rodar localmente

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python.exe scraper\atualizar.py      # coleta + processa (1a vez demora: le ~900 PDFs)
venv\Scripts\streamlit.exe run app.py
```

## Automático

`.github/workflows/atualizar_dados.yml` roda todo dia (e a cada 4h aos sábados/domingos), busca súmulas novas,
reprocessa e faz commit dos dados. Publicando o repositório no **Streamlit Community Cloud** (arquivo principal
`app.py`), o site se atualiza sozinho a cada commit do robô.

## Estrutura

- `scraper/discover_all.py` — lista jogos de todas as competições (profissional + feminino) e acha o PDF da súmula
  (3 formatos de link + fallback pelo borderô).
- `scraper/download_sumulas.py` — baixa os PDFs (`data/raw/sumulas/{id}.pdf`).
- `scraper/classificar_sem_sumula.py` — jogos sem súmula: **W.O.** (cancelado com 3x0), cancelado, futuro.
- `scraper/build_dataset.py` — lê os PDFs (cache em `data/parsed/`), padroniza nomes (`scraper/nomes.py`) e gera `data/processed/*.json`.
- `scraper/organizar_2026.py` — copia as súmulas com nomes legíveis (`2026-08-27 - Bra P x Bra F (R5).pdf`).
- `app.py` + `pages/` — site (início, calendário, classificações, jogadores, análise de time, anuncie); `analise.py` = motor de métricas/insights; `ui.py` = tabelas com ordenação. Contato/textos em `config.py`.
