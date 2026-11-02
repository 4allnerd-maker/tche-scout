<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

// Recebe o aviso de pagamento do gateway e libera ou encerra a assinatura.
// MODELO: cada gateway (Mercado Pago, Stripe, Kiwify, Hotmart, Asaas...) manda um formato diferente e uma assinatura própria.
// Quando você escolher o gateway, este arquivo é adaptado para ler o formato dele e validar a assinatura oficial.
// Enquanto isso, ele aceita apenas o formato abaixo e exige o cabeçalho X-Webhook-Secret igual ao segredo da config:
//   POST JSON  {"email": "cliente@exemplo.com", "evento": "pago" | "cancelado", "dias": 31}

$c = cfg();
$segredo = (string) ($c['webhook_segredo'] ?? '');
$enviado = (string) ($_SERVER['HTTP_X_WEBHOOK_SECRET'] ?? '');
if ($segredo === '' || !hash_equals($segredo, $enviado)) {
    responder(403, ['erro' => 'Não autorizado.']);
}

$d = exigir_post_json();
$email = strtolower(trim((string) ($d['email'] ?? '')));
$evento = (string) ($d['evento'] ?? '');
$dias = max(1, min(400, (int) ($d['dias'] ?? 31)));

$st = pdo()->prepare('SELECT id, assinatura_ate FROM usuarios WHERE email = ?');
$st->execute([$email]);
$u = $st->fetch();
if (!$u) {
    responder(404, ['erro' => 'Usuário não encontrado.']);
}

if ($evento === 'pago') {
    $base = (!empty($u['assinatura_ate']) && $u['assinatura_ate'] > date('Y-m-d')) ? $u['assinatura_ate'] : date('Y-m-d');
    $nova = date('Y-m-d', strtotime($base . ' +' . $dias . ' days'));
    pdo()->prepare('UPDATE usuarios SET assinatura_ate = ? WHERE id = ?')->execute([$nova, $u['id']]);
    responder(200, ['ok' => true, 'assinatura_ate' => $nova]);
}
if ($evento === 'cancelado') {
    // Cancelar não tira o que já foi pago: o acesso vale até assinatura_ate. Reembolso/chargeback: use o evento 'encerrado'.
    responder(200, ['ok' => true]);
}
if ($evento === 'encerrado') {
    pdo()->prepare('UPDATE usuarios SET assinatura_ate = NULL WHERE id = ?')->execute([$u['id']]);
    responder(200, ['ok' => true]);
}
responder(400, ['erro' => 'Evento desconhecido.']);
