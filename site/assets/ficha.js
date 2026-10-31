/* Ficha do jogador estilo "menu de videogame". Usa os campos gerados por geral/skills.py. */
const COR_POS = { Goleiro: "#F2C230", Defensor: "#3FA7FF", Meia: "#2ECC71", Atacante: "#FF5468" };
const CATS = {
  finalizacao: ["Finalização", ["gols_90", "xg_90", "chutes_90", "chutes_alvo_pct"]],
  criacao: ["Criação", ["assist_90", "xa_90", "passes_chave_90", "chances_criadas_90"]],
  passe: ["Passe", ["passes_90", "passes_pct", "passes_prog_90", "passes_longos_90"]],
  drible: ["Drible e posse", ["dribles_90", "dribles_pct", "faltas_sofridas_90", "perdas_90"]],
  defesa: ["Defesa", ["desarmes_90", "interceptacoes_90", "cortes_90", "bloqueios_90", "recuperacoes_90"]],
  duelos: ["Duelos e físico", ["duelos_pct", "duelos_90", "aereos_90", "distancia_90", "pressoes_90"]],
  goleiro: ["Goleiro", ["defesas_pct", "sem_sofrer_pct", "sofridos_90"]],
  agressividade: ["Agressividade", ["faltas_90", "cartoes_90"]],
};
const ATTR = {
  gols_90: "Gols/90", xg_90: "xG/90", chutes_90: "Chutes/90", chutes_alvo_pct: "Chutes no alvo %", assist_90: "Assistências/90", xa_90: "xA/90",
  passes_chave_90: "Passes-chave/90", chances_criadas_90: "Chances criadas/90", passes_90: "Passes/90", passes_pct: "Passes certos %",
  passes_prog_90: "Passes progressivos/90", passes_longos_90: "Passes longos/90", dribles_90: "Dribles certos/90", dribles_pct: "Dribles certos %",
  faltas_sofridas_90: "Faltas sofridas/90", perdas_90: "Perdas de bola/90 ↓", desarmes_90: "Desarmes/90", interceptacoes_90: "Interceptações/90",
  cortes_90: "Cortes/90", bloqueios_90: "Bloqueios/90", recuperacoes_90: "Recuperações/90", duelos_pct: "Duelos ganhos %", duelos_90: "Duelos ganhos/90",
  aereos_90: "Bolas aéreas/90", distancia_90: "Distância/90 (km)", pressoes_90: "Pressões/90", defesas_pct: "Defesas %", sem_sofrer_pct: "Jogos sem sofrer %",
  sofridos_90: "Gols sofridos/90 ↓", cartoes_90: "Cartões ponderados/90", faltas_90: "Faltas cometidas/90", participacao_gols_90: "Gols + assistências/90",
};
const INDICES = { ofensividade: "Ofensividade", defensividade: "Defensividade", construcao: "Construção", agressividade: "Agressividade" };
const COMPOSICAO = { ofensividade: "gols, xG, chutes, gols+assistências, assistências, xA, chances criadas, passes-chave, acerto de passe e passes progressivos",
  defensividade: "desarmes, interceptações, cortes, bloqueios, recuperações, duelos, bolas aéreas e pressões", construcao: "passes, acerto, progressivos, longos, dribles e perdas de bola (menos é melhor)",
  agressividade: "faltas cometidas e cartões (amarelo vale 1, vermelho vale 3). Nota alta = mais agressivo, não necessariamente melhor" };
const corAgress = n => n == null ? "#6F8577" : n >= 70 ? "#FF7A45" : n >= 40 ? "#FFB020" : "#8FD3FF";
const ORDEM_CATS = ["finalizacao", "criacao", "passe", "drible", "defesa", "duelos"];
const PAPEL_COR = { "Titular absoluto": "#2ECC71", "Titular": "#9BE564", "Rodízio": "#F2C230", "Reserva": "#FF9F43", "Elenco": "#9FB3A6" };
const CLASSE_TXT = { A: "Série A e Copa do Brasil", B: "Série B", C: "Série C", D: "Série D, estaduais e demais" };

const corNota = n => n == null ? "#6F8577" : n >= 85 ? "#2ECC71" : n >= 70 ? "#9BE564" : n >= 55 ? "#F2C230" : n >= 40 ? "#FF9F43" : "#FF5468";
const selo = c => `<span class="selo classe-${c}" title="Classe da competição: ${CLASSE_TXT[c] || ""}">${c}</span>`;

function abrirFicha(j) {
  const cor = COR_POS[j.posicao] || "#9FB3A6", n = j.notas, cats = n ? n.categorias : {}, at = n ? n.atributos : {};
  const cats_exibir = j.posicao === "Goleiro" ? ["goleiro", "passe", "agressividade"] : [...ORDEM_CATS, "agressividade"];
  const val = (a) => { const v = j.valores?.[a]; if (v == null) return "–"; return a.endsWith("_pct") ? Math.round(v) + "%" : v.toLocaleString("pt-BR", { maximumFractionDigits: 2 }); };
  const bloco = c => {
    const [nome, attrs] = CATS[c]; const nota = cats[c]; const cn = c === "agressividade" ? corAgress : corNota;
    return `<div class="cat"><div class="cat-topo"><b style="color:${cn(nota)}">${nota ?? "–"}</b><span>${nome.toUpperCase()}</span></div>` +
      attrs.map(a => `<div class="at"><span>${ATTR[a]}</span><em>${val(a)}</em><b style="color:${cn(at[a])}">${at[a] ?? "–"}</b>
        <i class="barra-at"><u style="width:${at[a] ?? 0}%;background:${cn(at[a])}"></u></i></div>`).join("") + "</div>";
  };
  const idx = n ? Object.entries(INDICES).filter(([k]) => j.indices?.[k] != null).map(([k, nm]) =>
    `<div class="ind" title="${nm}: ${COMPOSICAO[k]}"><span>${nm}</span><i><u style="width:${j.indices[k]}%;background:${(k === "agressividade" ? corAgress : corNota)(j.indices[k])}"></u></i><b>${j.indices[k]}</b></div>`).join("") : "";
  const rk = j.ranks ? `<div class="chips"><span>#${j.ranks.geral} <small>de ${j.ranks.n_geral} no geral</small></span>
    <span>#${j.ranks.posicao} <small>de ${j.ranks.n_posicao} ${j.posicao.toLowerCase()}s</small></span>
    <span>#${j.ranks.liga} <small>de ${j.ranks.n_liga} na liga</small></span><span>#${j.ranks.classe} <small>de ${j.ranks.n_classe} na classe ${j.classe}</small></span></div>` : "";
  const dado = (n, v) => v == null || v === "" ? "" : `<div><span>${n}</span><b>${v}</b></div>`;
  $("fichaCorpo").innerHTML = `<div class="fifa">
    <aside style="border-top:6px solid ${cor}">
      <div class="topo"><div><div class="ovr" style="color:${corNota(j.ovr)}">${j.ovr ?? "—"}</div><small>OVR</small></div>
        <div class="posbox" style="background:${cor}">${esc(j.posicao.slice(0, 3).toUpperCase())}</div></div>
      <div class="avatar" style="background:linear-gradient(160deg,${cor}55,#0D1B14)">${esc((j.nome_curto || j.nome).split(" ").map(p => p[0]).slice(0, 2).join(""))}</div>
      <h3>${esc(j.nome_curto || j.nome)}</h3>
      ${j.nome_curto !== j.nome ? `<p class="completo">${esc(j.nome)}</p>` : ""}
      <p class="clube">${esc(j.clube)} ${selo(j.classe)}</p>
      ${j.papel ? `<p class="papel" style="border-color:${PAPEL_COR[j.papel]};color:${PAPEL_COR[j.papel]}" title="Participação nos minutos do time na competição">${j.papel}</p>
        <div class="minutos"><i><u style="width:${j.pct_minutos}%;background:${PAPEL_COR[j.papel]}"></u></i><small>${j.pct_minutos}% dos minutos do time${j.pct_titular != null ? ` · titular em ${j.pct_titular}% dos jogos` : ""} (${j.jogos_time} jogos do time)</small></div>` : ""}<p class="clube"><small>${esc(j.liga)} ${j.temporada}</small></p>
      <div class="dados">${dado("Idade", j.idade)}${dado("Nascimento", j.nascimento)}${dado("Nacionalidade", j.nacionalidade)}${dado("Camisa", j.camisa)}
        ${dado("Jogos", j.jogos)}${dado("Titular", j.titular)}${dado("Minutos", j.min?.toLocaleString("pt-BR"))}${dado("Gols", j.gols)}${dado("Assist.", j.assist)}
        ${dado("Amarelos", j.amarelos)}${dado("Vermelhos", j.vermelhos)}</div>
    </aside>
    <section>
      ${n && (j.min || 0) < 900 ? `<p class="aviso" style="color:var(--ouro)">⚠ Amostra pequena (${j.min} minutos): a nota é mais instável. Use com cautela.</p>` : ""}
      ${n ? `<div class="idx">${idx}</div>${rk}` : `<p class="aviso">Sem nota: o jogador tem menos de 450 minutos ou a fonte não trouxe estatísticas avançadas. Os números por 90 abaixo ficam disponíveis quando existirem.</p>`}
      <div class="cats">${cats_exibir.map(bloco).join("")}</div>
      ${n ? `<p class="aviso">Notas de 30 a 99: posição do jogador entre os de mesma função (${j.posicao.toLowerCase()}s) em todas as ligas do banco, com 450+ minutos. O OVR é a média das categorias com pesos por função.
        ↓ = quanto menor, melhor. <b>Este OVR foi obtido numa competição de classe ${j.classe} (${CLASSE_TXT[j.classe]}); em competições de classe mais alta, a mesma nota pode ser menor.</b></p>` : ""}
    </section></div>`;
  $("ficha").showModal();
}
