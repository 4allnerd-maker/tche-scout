<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

// Pedido de demonstração completa (o administrador libera por 30 minutos em api/admin.php). Uma vez por conta.

$u = usuario_atual();
if (!$u) {
    responder(401, ['erro' => 'Entre na sua conta para pedir a demonstração.']);
}
exigir_post_json();

if (tem_premium($u) && $u['papel'] !== 'admin' && !em_demo($u)) {
    responder(409, ['erro' => 'Você já tem o acesso Premium ativo.']);
}
if (!empty($u['demo_ate'])) {
    responder(409, ['erro' => 'A demonstração já foi usada nesta conta.']);
}
if (!empty($u['demo_pedido_em'])) {
    responder(200, ['ok' => true, 'mensagem' => 'Seu pedido já foi enviado. Você será avisado quando for liberado.']);
}

limitar('demo', 5, 60);
registrar_tentativa('demo');
pdo()->prepare('UPDATE usuarios SET demo_pedido_em = ? WHERE id = ?')->execute([date('Y-m-d H:i:s'), $u['id']]);
avisar_admin(
    'Tchê Scout: pedido de demonstração de ' . $u['nome'],
    $u['nome'] . ' (' . $u['email'] . ') pediu a demonstração completa de 30 minutos. Libere em /admin.html.'
);
responder(200, ['ok' => true, 'mensagem' => 'Pedido enviado! Você será avisado quando a demonstração for liberada.']);
