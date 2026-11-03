const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (v, t = "int") => v == null ? "–" : (t === "int" ? Math.round(v).toLocaleString("pt-BR")
  : v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
const getJSON = url => fetch(url).then(r => { if (!r.ok) throw new Error(url); return r.json(); });

/* ativo: "home" | "painel" | "ranking" | "jogadores" | "" */
function cabecalho(ativo) {
  const link = (id, href, txt) => `<a class="${ativo === id ? "ativo" : ""}" href="${href}">${txt}</a>`;
  document.body.insertAdjacentHTML("afterbegin", `<header>
    <img src="assets/logo.svg" alt="Tchê Scout"><a class="marca" href="index.html">Tchê <span>Scout</span></a>
    <nav>${link("home", "index.html", "Início")}${link("ranking", "ranking.html", "AIE · Ranking")}${link("vca", "tabela.html?modo=vca", "VCA · Dados brutos")}${link("eta", "tabela.html?modo=eta", "ETA · Por 90")}${link("apoie", "apoie.html", "Apoie")}
    <a href="${CONFIG.URL_FGF}" target="_blank" rel="noopener">Módulo FGF ↗</a><span id="auth-nav" class="auth-nav"></span></nav></header>`);
  document.body.insertAdjacentHTML("beforeend", `<footer>Estatísticas de scout — não é conteúdo de apostas. Dados: súmulas oficiais da FGF e FootyStats.
    Projeto independente, sem vínculo com federações ou clubes.<br>
    <a href="legal.html?doc=privacidade">Privacidade</a> · <a href="legal.html?doc=cookies">Cookies</a> · <a href="legal.html?doc=termos">Termos de uso</a> · ${CONFIG.EMAIL}</footer>`);
  if (typeof atualizaNav === "function") atualizaNav();
}
