@echo off
cd /d "%~dp0site"
echo Site do Tche Scout (Geral) em http://localhost:8520  -  feche esta janela para parar.
start "" http://localhost:8520
python -m http.server 8520
