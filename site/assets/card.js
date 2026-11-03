/* Card exportável do atleta (PNG) desenhado em Canvas, sem bibliotecas externas.
   Um card por visão: AIE (ficha), VCA (dados brutos) e ETA (por 90). A foto é escolhida pelo usuário no próprio computador
   e fica guardada só neste navegador (localStorage), para reaparecer nos cards e nas formações. */
const CARD_W = 1080, CARD_H = 1440;
const FOTO_PREFIXO = "foto:";

function fotoSalva(id) { try { return localStorage.getItem(FOTO_PREFIXO + id) || null; } catch (e) { return null; } }
function salvaFoto(id, url) { try { if (url) localStorage.setItem(FOTO_PREFIXO + id, url); else localStorage.removeItem(FOTO_PREFIXO + id); } catch (e) { /* sem espaço: segue sem guardar */ } }
function carregaImagem(url) { return new Promise(res => { if (!url) return res(null); const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = url; }); }
/* Reduz a foto escolhida (proporção 3:4) para caber no localStorage. */
function lerFoto(arquivo) {
  return new Promise(res => {
    const fr = new FileReader();
    fr.onload = () => carregaImagem(fr.result).then(im => {
      if (!im) return res(null);
      const c = document.createElement("canvas"); c.width = 360; c.height = 480; const x = c.getContext("2d");
      const k = Math.max(360 / im.width, 480 / im.height), w = im.width * k, h = im.height * k;
      x.drawImage(im, (360 - w) / 2, (480 - h) * 0.3, w, h);   // enquadra puxando para o rosto (parte de cima)
      res(c.toDataURL("image/jpeg", 0.85));
    });
    fr.onerror = () => res(null); fr.readAsDataURL(arquivo);
  });
}

function rr(x, px, py, w, h, r) { x.beginPath(); x.moveTo(px + r, py); x.arcTo(px + w, py, px + w, py + h, r); x.arcTo(px + w, py + h, px, py + h, r); x.arcTo(px, py + h, px, py, r); x.arcTo(px, py, px + w, py, r); x.closePath(); }
function texto(x, t, px, py, { tam = 28, peso = 400, cor = "#E8F1EB", al = "left", max = 0 } = {}) {
  x.font = `${peso} ${tam}px "Segoe UI", Arial, sans-serif`; x.fillStyle = cor; x.textAlign = al; x.textBaseline = "alphabetic";
  let s = String(t ?? ""); if (max) while (x.measureText(s).width > max && s.length > 1) s = s.slice(0, -1); if (max && s !== String(t ?? "")) s = s.trim() + "…";
  x.fillText(s, px, py);
}
function barra(x, px, py, w, pct, cor, h = 12) { x.fillStyle = "#1B2E24"; rr(x, px, py, w, h, h / 2); x.fill(); if (pct > 0) { x.fillStyle = cor; rr(x, px, py, Math.max(h, w * Math.min(100, pct) / 100), h, h / 2); x.fill(); } }

/* Retângulo da foto (ou iniciais) com cantos arredondados. */
function desenhaFoto(x, foto, j, px, py, w, h, cor) {
  x.save(); rr(x, px, py, w, h, 28); x.clip();
  const g = x.createLinearGradient(px, py, px, py + h); g.addColorStop(0, cor + "88"); g.addColorStop(1, "#0D1B14"); x.fillStyle = g; x.fillRect(px, py, w, h);
  if (foto) { const k = Math.max(w / foto.width, h / foto.height), fw = foto.width * k, fh = foto.height * k; x.drawImage(foto, px + (w - fw) / 2, py + (h - fh) * 0.3, fw, fh); }
  else {
    texto(x, (j.nome_curto || j.nome).split(" ").map(p => p[0]).slice(0, 2).join("").toUpperCase(), px + w / 2, py + h / 2 + 40, { tam: 130, peso: 800, cor: "#ffffff55", al: "center" });
    texto(x, "foto do atleta", px + w / 2, py + h - 28, { tam: 22, cor: "#ffffff66", al: "center" });
  }
  x.restore(); x.strokeStyle = cor; x.lineWidth = 4; rr(x, px, py, w, h, 28); x.stroke();
}

/* Cabeçalho comum a todos os cards (foto, OVR, nome, clube, dados). Devolve o y onde o conteúdo começa. */
function cabecalhoCard(x, j, foto, titulo) {
  const cor = COR_POS[j.posicao] || "#9FB3A6";
  const fundo = x.createLinearGradient(0, 0, 0, CARD_H); fundo.addColorStop(0, "#102319"); fundo.addColorStop(1, "#08110C"); x.fillStyle = fundo; x.fillRect(0, 0, CARD_W, CARD_H);
  x.fillStyle = cor; x.fillRect(0, 0, CARD_W, 18);
  desenhaFoto(x, foto, j, 56, 60, 390, 520, cor);
  const px = 490;
  texto(x, j.ovr ?? "—", px, 190, { tam: 150, peso: 800, cor: corNota(j.ovr) });
  texto(x, "OVR", px + 4, 232, { tam: 30, peso: 600, cor: "#9FB3A6" });
  x.fillStyle = cor; rr(x, 900, 80, 124, 64, 14); x.fill(); texto(x, j.posicao.slice(0, 3).toUpperCase(), 962, 126, { tam: 38, peso: 800, cor: "#0D1B14", al: "center" });
  x.fillStyle = (({ A: "#2ECC71", B: "#3FA7FF", C: "#F2C230", D: "#FF9F43" })[j.classe] || "#9FB3A6"); rr(x, 900, 160, 124, 56, 14); x.fill();
  texto(x, "Classe " + j.classe, 962, 199, { tam: 28, peso: 800, cor: "#0D1B14", al: "center" });
  texto(x, j.nome_curto || j.nome, px, 306, { tam: 54, peso: 800, max: 530 });
  if (j.nome_curto && j.nome_curto !== j.nome) texto(x, j.nome, px, 342, { tam: 24, cor: "#9FB3A6", max: 530 });
  texto(x, j.clube, px, 392, { tam: 36, peso: 700, cor: cor, max: 530 });
  texto(x, `${j.liga} ${j.temporada}`, px, 428, { tam: 26, cor: "#9FB3A6", max: 530 });
  if (j.papel) texto(x, `${j.papel} · ${j.pct_minutos}% dos minutos do time`, px, 466, { tam: 24, peso: 600, cor: PAPEL_COR[j.papel] || "#9FB3A6", max: 530 });
  const dados = [["Idade", j.idade], ["Jogos", j.jogos], ["Minutos", j.min?.toLocaleString("pt-BR")], ["Gols", j.gols], ["Assist.", j.assist], ["Amarelos", j.amarelos]].filter(d => d[1] != null && d[1] !== "");
  dados.slice(0, 6).forEach((d, i) => { const cx = px + (i % 3) * 180, cy = 510 + Math.floor(i / 3) * 60; texto(x, d[0], cx, cy, { tam: 20, cor: "#7F9587" }); texto(x, d[1], cx, cy + 30, { tam: 30, peso: 700 }); });
  x.fillStyle = "#16281F"; rr(x, 56, 616, CARD_W - 112, 56, 14); x.fill();
  texto(x, titulo, 80, 654, { tam: 28, peso: 800, cor: "#2ECC71" });
  return 700;
}
function rodapeCard(x) { texto(x, "TCHÊ SCOUT · tchescout.com.br", CARD_W / 2, CARD_H - 34, { tam: 24, peso: 700, cor: "#4F6B5B", al: "center" }); }

function cardAIE(x, j, y0) {
  const n = j.notas;
  if (!n) { texto(x, "Sem nota: menos de 450 minutos ou sem estatísticas avançadas.", 80, y0 + 30, { tam: 26, cor: "#FF9F43" }); return; }
  Object.entries(INDICES).filter(([k]) => j.indices?.[k] != null).forEach(([k, nm], i) => {
    const cx = 56 + (i % 2) * 508, cy = y0 + Math.floor(i / 2) * 64, v = j.indices[k], cor = (k === "agressividade" ? corAgress : corNota)(v);
    texto(x, nm, cx, cy + 24, { tam: 24, cor: "#B5C7BB" }); barra(x, cx + 190, cy + 8, 240, v, cor, 16); texto(x, v, cx + 508 - 56 - 4, cy + 28, { tam: 30, peso: 800, cor, al: "right" });
  });
  let y = y0 + 150;
  if (j.ranks) { [`#${j.ranks.geral} de ${j.ranks.n_geral} no geral`, `#${j.ranks.posicao} de ${j.ranks.n_posicao} ${j.posicao.toLowerCase()}s`, `#${j.ranks.liga} na liga`, `#${j.ranks.classe} na classe ${j.classe}`]
    .forEach((t, i) => { const cx = 56 + (i % 2) * 508, cy = y + Math.floor(i / 2) * 56; x.fillStyle = "#16281F"; rr(x, cx, cy, 480, 44, 22); x.fill(); texto(x, t, cx + 240, cy + 31, { tam: 24, peso: 600, al: "center" }); }); y += 130; }
  const cats = j.posicao === "Goleiro" ? ["goleiro", "passe", "agressividade"] : [...ORDEM_CATS, "agressividade"];
  cats.forEach((c, i) => {
    const cx = 56 + (i % 2) * 508, cy = y + Math.floor(i / 2) * 100, v = n.categorias[c], cor = (c === "agressividade" ? corAgress : corNota)(v);
    texto(x, CATS[c][0].toUpperCase(), cx, cy + 24, { tam: 24, peso: 700, cor: "#B5C7BB" }); texto(x, v ?? "–", cx + 480, cy + 30, { tam: 44, peso: 800, cor, al: "right" });
    barra(x, cx, cy + 46, 480, v ?? 0, cor, 18);
  });
  texto(x, `Nota 30–99 entre ${j.posicao.toLowerCase()}s do banco · OVR obtido na classe ${j.classe}`, CARD_W / 2, CARD_H - 76, { tam: 20, cor: "#6F8577", al: "center" });
}

/* VCA e ETA: lista dos principais números, até 22, distribuídos por grupo. */
function cardLista(x, j, y0, def, modo) {
  const arr = modo === "vca" ? j.vca : j.eta, d = modo === "vca" ? def.vca : def.eta;
  if (!arr) { texto(x, "Sem dados para este atleta.", 80, y0 + 30, { tam: 26, cor: "#FF9F43" }); return; }
  const itens = []; [...grupos(d)].filter(([g]) => !(g === "Goleiro" && j.posicao !== "Goleiro")).forEach(([g, ids]) => {
    const com = ids.filter(i => arr[i] != null && !(modo === "vca" && arr[i] === 0 && d[i].tipo !== "pct")); itens.push({ g, ids: com.slice(0, 3) }); });
  const linhas = []; itens.filter(o => o.ids.length).forEach(o => { linhas.push({ g: o.g }); o.ids.forEach(i => linhas.push({ i })); });
  linhas.length = Math.min(linhas.length, 32); const meio = Math.ceil(linhas.length / 2), colunas = [linhas.slice(0, meio), linhas.slice(meio)];
  colunas.forEach((col, ci) => { let y = y0; const cx = 56 + ci * 508;
    col.forEach(l => {
      if (l.g) { texto(x, l.g.toUpperCase(), cx, y + 22, { tam: 22, peso: 800, cor: "#2ECC71" }); y += 38; return; }
      const c = d[l.i], v = arr[l.i], p = modo === "eta" && j.eta_pct ? j.eta_pct[l.i] : null, cor = p != null ? corNota(p) : "#E8F1EB";
      texto(x, c.rotulo + (c.menos_melhor ? " ↓" : ""), cx, y + 22, { tam: 22, cor: "#B5C7BB", max: 300 });
      texto(x, fmtV(v, c.tipo), cx + 410, y + 22, { tam: 26, peso: 700, al: "right" });
      if (p != null) { barra(x, cx + 424, y + 8, 40, p, cor, 12); }
      else if (c.tipo === "pct") barra(x, cx + 424, y + 8, 40, v, "#2ECC71", 12);
      y += 38; }); });
  if (modo === "eta") texto(x, j.eta_pct ? `Barra = posição entre os ${j.posicao.toLowerCase()}s do banco (verde = melhor) · ↓ menos é melhor` : "Menos de 450 minutos: sem comparação com a função.", CARD_W / 2, CARD_H - 76, { tam: 20, cor: "#6F8577", al: "center" });
  else texto(x, "Totais e porcentagens da temporada, sem ajuste por minutos", CARD_W / 2, CARD_H - 76, { tam: 20, cor: "#6F8577", al: "center" });
}

const TITULO_CARD = { aie: "AIE · FICHA DO ATLETA", vca: "VCA · DADOS BRUTOS DA TEMPORADA", eta: "ETA · RENDIMENTO POR 90 MINUTOS" };
function desenhaCard(canvas, j, modo, def, foto) {
  canvas.width = CARD_W; canvas.height = CARD_H; const x = canvas.getContext("2d");
  const y0 = cabecalhoCard(x, j, foto, TITULO_CARD[modo]);
  if (modo === "aie") cardAIE(x, j, y0); else cardLista(x, j, y0, def, modo);
  rodapeCard(x);
}

/* Janela do card: escolher/trocar a foto, trocar a visão e baixar o PNG. */
async function abrirCard(j, modo) {
  const def = await colunasDef();
  let dlg = document.getElementById("cardDlg");
  if (!dlg) {
    dlg = document.createElement("dialog"); dlg.id = "cardDlg"; dlg.className = "larga";
    dlg.innerHTML = `<div class="abas" id="cardAbas"><button data-a="aie">Card AIE</button><button data-a="vca">Card VCA</button><button data-a="eta">Card ETA</button></div>
      <canvas id="cardCanvas" style="width:min(100%,540px);aspect-ratio:3/4;display:block;margin:.6rem auto;border-radius:10px"></canvas>
      <p style="display:flex;gap:.5rem;flex-wrap:wrap;justify-content:center;margin:.4rem 0">
        <button id="cardFoto">📷 Escolher foto do atleta</button><button id="cardSemFoto">Remover foto</button><button id="cardBaixar" class="primario">⬇ Baixar PNG</button><button id="cardFechar">Fechar</button></p>
      <input type="file" id="cardArq" accept="image/*" hidden>
      <p class="aviso" style="text-align:center">A foto fica só neste navegador (não é enviada a lugar nenhum) e reaparece nas formações.</p>`;
    document.body.appendChild(dlg);
  }
  let foto = await carregaImagem(fotoSalva(j.id)), atual = modo || "aie";
  const redesenha = () => { desenhaCard($("cardCanvas"), j, atual, def, foto); dlg.querySelectorAll("#cardAbas button").forEach(b => b.classList.toggle("ativo", b.dataset.a === atual)); };
  dlg.querySelectorAll("#cardAbas button").forEach(b => b.onclick = () => { atual = b.dataset.a; redesenha(); });
  $("cardFoto").onclick = () => $("cardArq").click();
  $("cardArq").onchange = async e => { const f = e.target.files[0]; e.target.value = ""; if (!f) return; const url = await lerFoto(f); if (url) { salvaFoto(j.id, url); foto = await carregaImagem(url); redesenha(); } };
  $("cardSemFoto").onclick = () => { salvaFoto(j.id, null); foto = null; redesenha(); };
  $("cardFechar").onclick = () => dlg.close();
  $("cardBaixar").onclick = () => { const a = document.createElement("a"); a.download = `tchescout-${(j.nome_curto || j.nome).toLowerCase().normalize("NFD").replace(/[^a-z0-9]+/g, "-")}-${atual}.png`; a.href = $("cardCanvas").toDataURL("image/png"); a.click(); };
  redesenha(); if (!dlg.open) dlg.showModal();
}
