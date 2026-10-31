const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (v, t = "int") => v == null ? "–" : (t === "int" ? Math.round(v).toLocaleString("pt-BR")
  : v.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
const getJSON = url => fetch(url).then(r => { if (!r.ok) throw new Error(url); return r.json(); });

function cabecalho(ativo) {
  const link = (id, href, txt, extra = "") => `<a class="${ativo === id ? "ativo" : ""}" href="${href}" ${extra}>${txt}</a>`;
  document.body.insertAdjacentHTML("afterbegin", `<header>
    <img src="assets/logo.svg" alt="Tchê Scout"><a class="marca" href="index.html">Tchê <span>Scout</span> · Geral</a>
    <nav>${link("home", "index.html", "Ligas")}${link("ranking", "ranking.html", "Ranking")}${link("jogadores", "jogadores.html", "Jogadores")}
    <a href="https://tchescout.streamlit.app" target="_blank" rel="noopener">Painel FGF ↗</a></nav></header>`);
  document.body.insertAdjacentHTML("beforeend", `<footer>Estatísticas de scout — não é conteúdo de apostas. Dados: FootyStats.
    Projeto independente, sem vínculo com federações ou clubes.</footer>`);
}
