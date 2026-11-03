/* Configurações editáveis do site (textos comerciais e links). Nada secreto aqui: este arquivo é público.
   Os preços que valem de verdade (cobrança) ficam no servidor: api/ (config_tchescout.php). Mantenha os dois iguais. */
const CONFIG = {
  PLANOS: {
    mensal: { nome: "Mensal", valor: 150, dias: 30 },
    anual: { nome: "Anual", valor: 999, dias: 365 },
  },
  DEMO_MINUTOS: 30,
  URL_FGF: "https://tchescout.streamlit.app",
  EMAIL: "luchopahim@tchescout.com.br",
  LIMITE_GRATIS_RANKING: 25,  // linhas do ranking que o plano gratuito enxerga (o servidor aplica o mesmo limite em api/dados.php)
};
const brl = v => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: v % 1 ? 2 : 0 });
const economiaAnual = () => CONFIG.PLANOS.mensal.valor * 12 - CONFIG.PLANOS.anual.valor;
const descontoAnual = () => Math.round(100 * economiaAnual() / (CONFIG.PLANOS.mensal.valor * 12));
