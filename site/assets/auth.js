/* Login, sessão e acesso aos dados. A SEGURANÇA de verdade está no servidor (pasta api/): este arquivo só cuida da tela.
   No localhost existe um modo de teste (?dev=admin|premium|gratis) que NÃO funciona no site publicado. */
const DEV = ["localhost", "127.0.0.1"].includes(location.hostname);

function usuarioDev() {
  const p = new URLSearchParams(location.search).get("dev"); if (p) localStorage.setItem("dev", p);
  const v = localStorage.getItem("dev") || "admin";
  if (v === "visitante") return { logado: false };
  const base = { logado: true, nome: "Teste " + v, email: v + "@teste.local", papel: v === "admin" ? "admin" : "usuario" };
  return { ...base, premium: v !== "gratis", assinatura_ate: v === "premium" ? "2099-12-31" : null };
}

async function sessao() {
  if (DEV) return usuarioDev();
  try { const r = await fetch("api/eu.php", { credentials: "same-origin" }); return await r.json(); }
  catch (e) { return { logado: false }; }
}

async function enviar(url, corpo) {
  const r = await fetch(url, { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo || {}) });
  const j = await r.json().catch(() => ({ erro: "Resposta inválida do servidor." }));
  if (!r.ok) throw new Error(j.erro || "Não foi possível concluir. Tente novamente.");
  return j;
}

function irParaLogin() { location.href = "entrar.html?next=" + encodeURIComponent(location.pathname.split("/").pop() + location.search); }

async function exigirLogin() {
  const s = await sessao();
  if (!s.logado) { irParaLogin(); throw new Error("login"); }
  return s;
}

/* Planos: o gratuito vê uma vitrine; o servidor aplica os mesmos limites (api/dados.php). */
function limitarDev(f, d) {
  const u = usuarioDev(); if (u.premium) return d;
  if (f === "ranking") { const e = d.jogadores.filter(x => (x.min || 0) >= 900).sort((a, b) => b.ovr - a.ovr); return { ...d, jogadores: e.slice(0, CONFIG.LIMITE_GRATIS_RANKING), limitado: true, total: e.length }; }
  if (f.startsWith("jogadores/")) {
    if (f !== "jogadores/serie-a-2026") throw Object.assign(new Error("Esta liga é exclusiva do plano Premium."), { premium: true });
    return { lista: [...d].sort((a, b) => (b.min || 0) - (a.min || 0)).slice(0, 40), limitado: true, total: d.length };
  }
  return d;
}

async function dados(f) {
  if (DEV) { const d = await getJSON(`dados/${f}.json`); const r = limitarDev(f, d); return r.lista ? Object.assign(r.lista, { limitado: true, total: r.total }) : r; }
  const r = await fetch(`api/dados.php?f=${encodeURIComponent(f)}`, { credentials: "same-origin" });
  if (r.status === 401) { irParaLogin(); throw new Error("login"); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(j.erro || "Não foi possível carregar os dados."), { premium: !!j.premium });
  return j.lista ? Object.assign(j.lista, { limitado: !!j.limitado, total: j.total }) : j;
}

function bannerPremium(msg) {
  const c = CONFIG.CHECKOUT_URL ? `<a class="botao" href="${CONFIG.CHECKOUT_URL}">Assinar o Premium</a>` : `<a class="botao" href="painel.html#planos">Ver plano Premium</a>`;
  return `<div class="banner-premium"><b>🔒 ${msg}</b> ${c}</div>`;
}

async function atualizaNav() {
  const s = await sessao(), el = document.getElementById("auth-nav"); if (!el) return s;
  el.innerHTML = s.logado
    ? `<a href="painel.html">Painel</a><a href="#" id="sair">Sair</a>`
    : `<a href="entrar.html">Entrar</a><a class="cta" href="entrar.html?cadastro=1">Criar conta</a>`;
  const sair = document.getElementById("sair");
  if (sair) sair.onclick = async e => { e.preventDefault(); if (!DEV) { try { await enviar("api/logout.php"); } catch (x) { /* segue */ } } else localStorage.setItem("dev", "visitante"); location.href = "index.html"; };
  return s;
}
