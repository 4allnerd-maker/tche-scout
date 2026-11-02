/* Configurações editáveis do site (textos comerciais e links). Nada secreto aqui: este arquivo é público. */
const CONFIG = {
  PRECO: "Em breve",          // ex.: "R$ 29,90" — mostrado no card do plano Premium
  PERIODO: "",                // ex.: "/mês"
  CHECKOUT_URL: "",           // link de pagamento do gateway escolhido (Mercado Pago, Stripe, Kiwify...). Vazio = "lista de espera"
  URL_FGF: "https://tchescout.streamlit.app",
  EMAIL: "luchopahim@tchescout.com.br",
  LIMITE_GRATIS_RANKING: 25,  // linhas do ranking que o plano gratuito enxerga (o servidor aplica o mesmo limite em api/dados.php)
};
