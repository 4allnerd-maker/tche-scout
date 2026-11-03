<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

// Confirmação AUTOMÁTICA de pagamento (para quando o Pix passar a ser cobrado por uma operadora, como Mercado Pago, Asaas ou Efí).
// Hoje a confirmação é manual (api/admin.php). Este arquivo é um MODELO: cada operadora manda um formato e uma assinatura própria,
// e ele precisa ser adaptado a eles. Por enquanto aceita só o formato abaixo, com o cabeçalho X-Webhook-Secret igual ao da config:
//   POST JSON  {"email": "cliente@exemplo.com", "dias": 30}

$c = cfg();
$segredo = (string) ($c['webhook_segredo'] ?? '');
$enviado = (string) ($_SERVER['HTTP_X_WEBHOOK_SECRET'] ?? '');
if ($segredo === '' || !hash_equals($segredo, $enviado)) {
    responder(403, ['erro' => 'Não autorizado.']);
}

$d = exigir_post_json();
$email = strtolower(trim((string) ($d['email'] ?? '')));
$dias = max(1, min(400, (int) ($d['dias'] ?? 30)));

$st = pdo()->prepare('SELECT id FROM usuarios WHERE email = ?');
$st->execute([$email]);
$id = $st->fetchColumn();
if (!$id) {
    responder(404, ['erro' => 'Usuário não encontrado.']);
}
responder(200, ['ok' => true, 'assinatura_ate' => liberar_dias((int) $id, $dias)]);
