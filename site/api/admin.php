<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

// Painel do administrador. Só responde para quem tem papel "admin".
//   {"acao":"listar"}
//   {"acao":"liberar_demo","id":5,"minutos":30}
//   {"acao":"confirmar_pagamento","id":12}
//   {"acao":"conceder","email":"x@y.com","dias":30}

$u = usuario_atual();
if (!$u || $u['papel'] !== 'admin') {
    responder(403, ['erro' => 'Acesso restrito.']);
}
$d = exigir_post_json();
$acao = (string) ($d['acao'] ?? '');

if ($acao === 'listar') {
    $usuarios = pdo()->query(
        'SELECT id, nome, email, papel, assinatura_ate, demo_pedido_em, demo_ate, criado_em, ultimo_login
         FROM usuarios ORDER BY criado_em DESC LIMIT 500'
    )->fetchAll();
    $pagamentos = pdo()->query(
        'SELECT p.id, p.plano, p.valor, p.dias, p.status, p.criado_em, p.informado_em, u.nome, u.email
         FROM pagamentos p JOIN usuarios u ON u.id = p.usuario_id
         WHERE p.status IN (\'aguardando\', \'informado\') ORDER BY p.criado_em DESC LIMIT 200'
    )->fetchAll();
    $interesses = pdo()->query(
        'SELECT id, nome, email, tipo, organizacao, mensagem, criado_em FROM interesses ORDER BY criado_em DESC LIMIT 200'
    )->fetchAll();
    responder(200, ['agora' => date('Y-m-d H:i:s'), 'usuarios' => $usuarios, 'pagamentos' => $pagamentos, 'interesses' => $interesses]);
}

if ($acao === 'liberar_demo') {
    $id = (int) ($d['id'] ?? 0);
    $min = max(5, min(240, (int) ($d['minutos'] ?? 30)));
    $ate = date('Y-m-d H:i:s', time() + $min * 60);
    $st = pdo()->prepare('UPDATE usuarios SET demo_ate = ? WHERE id = ?');
    $st->execute([$ate, $id]);
    responder(200, ['ok' => true, 'demo_ate' => $ate]);
}

if ($acao === 'confirmar_pagamento') {
    $id = (int) ($d['id'] ?? 0);
    $st = pdo()->prepare('SELECT id, usuario_id, dias FROM pagamentos WHERE id = ? AND status IN (\'aguardando\', \'informado\')');
    $st->execute([$id]);
    $pg = $st->fetch();
    if (!$pg) {
        responder(404, ['erro' => 'Pagamento não encontrado ou já confirmado.']);
    }
    $nova = liberar_dias((int) $pg['usuario_id'], (int) $pg['dias']);
    pdo()->prepare('UPDATE pagamentos SET status = ?, confirmado_em = ? WHERE id = ?')
        ->execute(['confirmado', date('Y-m-d H:i:s'), $id]);
    responder(200, ['ok' => true, 'assinatura_ate' => $nova]);
}

if ($acao === 'conceder') {
    $email = strtolower(trim((string) ($d['email'] ?? '')));
    $dias = max(1, min(400, (int) ($d['dias'] ?? 30)));
    $st = pdo()->prepare('SELECT id FROM usuarios WHERE email = ?');
    $st->execute([$email]);
    $alvo = $st->fetchColumn();
    if (!$alvo) {
        responder(404, ['erro' => 'Usuário não encontrado.']);
    }
    if (!empty($d['vitalicio'])) {   // contrapartida para apoiadores/investidores
        pdo()->prepare('UPDATE usuarios SET assinatura_ate = ? WHERE id = ?')->execute(['2099-12-31', $alvo]);
        responder(200, ['ok' => true, 'assinatura_ate' => '2099-12-31']);
    }
    responder(200, ['ok' => true, 'assinatura_ate' => liberar_dias((int) $alvo, $dias)]);
}

responder(400, ['erro' => 'Ação inválida.']);
