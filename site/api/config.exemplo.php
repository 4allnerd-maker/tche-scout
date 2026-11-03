<?php
// COPIE este arquivo para FORA da pasta pública, com o nome  config_tchescout.php  (veja geral/HOSPEDAGEM.md) e preencha.
// Nunca suba o arquivo preenchido para o GitHub nem para dentro de public_html.
return [
    // Banco MySQL criado no hPanel (Bancos de dados > MySQL)
    'db_host' => 'localhost',
    'db_nome' => 'uXXXX_tchescout',
    'db_usuario' => 'uXXXX_tchescout',
    'db_senha' => 'SENHA-DO-BANCO',

    // Administrador (criado uma vez por api/instalar.php). Use uma senha forte e longa (12+ caracteres).
    'admin_email' => 'luchopahim@tchescout.com.br',
    'admin_senha' => 'TROQUE-ESTA-SENHA',
    'token_instalacao' => 'GERE-UM-TEXTO-LONGO-E-ALEATORIO-1',

    // Segredo que o gateway de pagamento envia no cabeçalho X-Webhook-Secret (api/webhook.php)
    'webhook_segredo' => 'GERE-UM-TEXTO-LONGO-E-ALEATORIO-2',

    // Pasta FORA do site onde ficam os JSONs gerados por geral/importar.py (ranking.json, ligas.json, times.json, jogadores/...)
    'pasta_dados' => '/home/uXXXX/dados_tchescout',

    // Pix (pagamento adiantado, sem cartão). Use uma chave aleatória ou o CNPJ para não expor CPF/telefone.
    'pix_chave' => '',
    'pix_nome' => 'TCHE SCOUT',     // nome do recebedor (até 25 letras, sem acento)
    'pix_cidade' => 'PELOTAS',      // cidade (até 15 letras, sem acento)
    'preco_mensal' => 150.00,       // 30 dias
    'preco_anual' => 999.00,        // 365 dias

    // Limites do plano gratuito
    'gratis_ranking' => 25,
    'gratis_min_minutos' => 900,
    'gratis_liga' => 'serie-a-2026',
    'gratis_jogadores' => 40,
];
