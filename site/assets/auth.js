/* Login, sessão e acesso aos dados. A SEGURANÇA de verdade está no servidor (pasta api/): este arquivo só cuida da tela.
   No localhost existe um modo de teste (?dev=admin|premium|gratis|demo|pedida|visitante) que NÃO funciona no site publicado. */
const DEV = ["localhost", "127.0.0.1"].includes(location.hostname);

function usuarioDev() {
  const p = new URLSearchParams(location.search).get("dev"); if (p) localStorage.setItem("dev", p);
  const v = localStorage.getItem("dev") || "admin";
  if (v === "visitante") return { logado: false };
  const demo = v === "demo";
  return { logado: true, nome: "Teste " + v, email: v + "@teste.local", papel: v === "admin" ? "admin" : "usuario",
    premium: ["admin", "premium", "demo"].includes(v), assinatura_ate: v === "premium" ? new Date(Date.now() + 3 * 86400000).toISOString().slice(0, 10) : null,
    dias_restantes: v === "premium" ? 3 : null, demo_ate: demo ? new Date(Date.now() + 25 * 60000).toISOString() : null,
    demo_pedida: v === "pedida" || demo, demo_usada: demo };
}

async function sessao() {
  if (DEV) return usuarioDev();
  try { const r = await fetch("api/eu.php", { credentials: "same-origin" }); return await r.json(); }
  catch (e) { return { logado: false }; }
}

function mockDev(url, corpo) {
  if (url.includes("pix.php")) return corpo.acao === "criar"
    ? { id: 1, plano: corpo.plano, valor: CONFIG.PLANOS[corpo.plano].valor, dias: CONFIG.PLANOS[corpo.plano].dias,
        copia_cola: "00020126360014br.gov.bcb.pix0114+5500000000005204000053039865406150.005802BR5909TCHE SCOUT6007PELOTAS62110507TS0000016304EXEMPLO", referencia: "TS00000001" }
    : { ok: true, mensagem: "Recebemos o seu aviso. Assim que o Pix for conferido, o acesso é liberado." };
  if (url.includes("demo.php")) { localStorage.setItem("dev", "pedida"); return { ok: true, mensagem: "Pedido enviado! Você será avisado quando a demonstração for liberada." }; }
  if (url.includes("admin.php")) return corpo.acao === "listar"
    ? { agora: new Date().toISOString(), usuarios: [
        { id: 7, nome: "Maria Teste", email: "maria@exemplo.com", papel: "usuario", assinatura_ate: null, demo_pedido_em: "2026-11-02 10:15:00", demo_ate: null, criado_em: "2026-11-01 09:00:00", ultimo_login: "2026-11-02 10:10:00" },
        { id: 8, nome: "João Assinante", email: "joao@exemplo.com", papel: "usuario", assinatura_ate: "2026-11-20", demo_pedido_em: null, demo_ate: null, criado_em: "2026-10-20 18:00:00", ultimo_login: null }],
      interesses: [{ id: 1, nome: "Carlos Empresário", email: "carlos@exemplo.com", tipo: "investidor", organizacao: "Agência X", mensagem: "Tenho interesse em apoiar com um aporte maior.", criado_em: "2026-11-02 08:00:00" }],
      pagamentos: [{ id: 3, plano: "mensal", valor: "150.00", dias: 30, status: "informado", criado_em: "2026-11-02 09:40:00", informado_em: "2026-11-02 09:45:00", nome: "Pedro Cliente", email: "pedro@exemplo.com" }] }
    : { ok: true };
  return { ok: true, mensagem: "Recebemos o seu contato. Responderemos por e-mail em breve. Obrigado!" };
}

async function enviar(url, corpo) {
  if (DEV && url.startsWith("api/")) return mockDev(url, corpo || {});
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
  return `<div class="banner-premium"><b>🔒 ${msg}</b> <a class="botao" href="painel.html#planos">Ver planos e demonstração</a></div>`;
}

async function atualizaNav() {
  const s = await sessao(), el = document.getElementById("auth-nav"); if (!el) return s;
  el.innerHTML = s.logado
    ? `${s.papel === "admin" ? '<a href="admin.html">Admin</a>' : ""}<a href="painel.html">Painel</a><a href="#" id="sair">Sair</a>`
    : `<a href="entrar.html">Entrar</a><a class="cta" href="entrar.html?cadastro=1">Criar conta</a>`;
  const sair = document.getElementById("sair");
  if (sair) sair.onclick = async e => { e.preventDefault(); if (!DEV) { try { await enviar("api/logout.php"); } catch (x) { /* segue */ } } else localStorage.setItem("dev", "visitante"); location.href = "index.html"; };
  if (s.logado && s.demo_ate) {   // contagem regressiva da demonstração
    const fim = new Date(String(s.demo_ate).replace(" ", "T")).getTime();
    const faixa = document.createElement("div"); faixa.className = "faixa-demo"; document.body.prepend(faixa);
    const t = () => { const m = Math.max(0, Math.round((fim - Date.now()) / 60000)); faixa.innerHTML = m > 0 ? `⏱ Demonstração completa ativa: <b>${m} min</b> restantes. <a href="painel.html#planos">Assinar</a>` : `Sua demonstração terminou. <a href="painel.html#planos">Ver planos</a>`; };
    t(); setInterval(t, 30000);
  }
  return s;
}
