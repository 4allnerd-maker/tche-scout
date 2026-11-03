<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

// Entrega os JSONs de dados SÓ para quem está logado, aplicando os limites do plano gratuito.
// Os arquivos ficam numa pasta FORA do site (config: pasta_dados), então ninguém os baixa direto pelo endereço.

$u = usuario_atual();
if (!$u) {
    responder(401, ['erro' => 'Entre na sua conta para ver os dados.']);
}

$f = (string) ($_GET['f'] ?? '');
if (!preg_match('#^(ranking|ligas|colunas|times|jogadores/[a-z0-9]+(-[a-z0-9]+)*)$#', $f)) {
    responder(400, ['erro' => 'Pedido inválido.']);
}

$c = cfg();
$pasta = realpath((string) $c['pasta_dados']);
$caminho = $pasta ? realpath($pasta . '/' . $f . '.json') : false;
if (!$pasta || !$caminho || strpos($caminho, $pasta . DIRECTORY_SEPARATOR) !== 0 || !is_file($caminho)) {
    responder(404, ['erro' => 'Dados não encontrados.']);
}

$premium = tem_premium($u);
header('Cache-Control: private, max-age=300');

if ($premium || $f === 'ligas' || $f === 'colunas') {
    header('Content-Type: application/json; charset=utf-8');
    readfile($caminho);
    exit;
}

// ---- plano gratuito: vitrine limitada ----
$dados = json_decode((string) file_get_contents($caminho), true);
if (!is_array($dados)) {
    responder(500, ['erro' => 'Dados indisponíveis no momento.']);
}

if ($f === 'ranking') {
    $min = (int) ($c['gratis_min_minutos'] ?? 900);
    $lista = array_values(array_filter($dados['jogadores'], fn($j) => ($j['min'] ?? 0) >= $min));
    usort($lista, fn($a, $b) => ($b['ovr'] ?? 0) <=> ($a['ovr'] ?? 0));
    $dados['jogadores'] = array_slice($lista, 0, (int) ($c['gratis_ranking'] ?? 25));
    $dados['limitado'] = true;
    $dados['total'] = count($lista);
    responder(200, $dados);
}

if (strpos($f, 'jogadores/') === 0) {
    if ($f !== 'jogadores/' . ($c['gratis_liga'] ?? 'serie-a-2026')) {
        responder(403, ['erro' => 'Esta liga é exclusiva do plano Premium.', 'premium' => true]);
    }
    usort($dados, fn($a, $b) => ($b['min'] ?? 0) <=> ($a['min'] ?? 0));
    responder(200, [
        'lista' => array_slice($dados, 0, (int) ($c['gratis_jogadores'] ?? 40)),
        'limitado' => true,
        'total' => count($dados),
    ]);
}

responder(403, ['erro' => 'Disponível no plano Premium.', 'premium' => true]);
