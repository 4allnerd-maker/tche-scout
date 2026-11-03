<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

// Pagamento via Pix (sem cartão, sem renovação automática): o usuário escolhe o plano, recebe o "copia e cola",
// paga no app do banco e clica em "Já paguei". O administrador confere o Pix no banco e confirma (api/admin.php).
//   POST {"acao":"criar","plano":"mensal"|"anual"}   -> cria o pedido e devolve o código Pix
//   POST {"acao":"avisar","id":123}                  -> usuário avisa que pagou (fica "em análise")

$u = usuario_atual();
if (!$u) {
    responder(401, ['erro' => 'Entre na sua conta para assinar.']);
}
$d = exigir_post_json();
$c = cfg();
$acao = (string) ($d['acao'] ?? '');

$planos = [
    'mensal' => ['valor' => (float) ($c['preco_mensal'] ?? 150.00), 'dias' => 30],
    'anual' => ['valor' => (float) ($c['preco_anual'] ?? 999.00), 'dias' => 365],
];

if ($acao === 'criar') {
    limitar('pix', 10, 60);
    registrar_tentativa('pix');
    $plano = (string) ($d['plano'] ?? '');
    if (!isset($planos[$plano])) {
        responder(422, ['erro' => 'Plano inválido.']);
    }
    if (empty($c['pix_chave'])) {
        responder(503, ['erro' => 'O pagamento ainda não está disponível. Fale com luchopahim@tchescout.com.br.']);
    }
    $p = $planos[$plano];
    pdo()->prepare(
        'INSERT INTO pagamentos (usuario_id, plano, valor, dias, status, criado_em) VALUES (?, ?, ?, ?, ?, ?)'
    )->execute([$u['id'], $plano, $p['valor'], $p['dias'], 'aguardando', date('Y-m-d H:i:s')]);
    $id = (int) pdo()->lastInsertId();
    $txid = 'TS' . str_pad((string) $id, 8, '0', STR_PAD_LEFT) . strtoupper(substr($plano, 0, 1));
    responder(201, [
        'id' => $id,
        'plano' => $plano,
        'valor' => $p['valor'],
        'dias' => $p['dias'],
        'copia_cola' => pix_copia_cola(
            (string) $c['pix_chave'],
            (string) ($c['pix_nome'] ?? 'TCHE SCOUT'),
            (string) ($c['pix_cidade'] ?? 'PELOTAS'),
            $p['valor'],
            $txid
        ),
        'referencia' => $txid,
    ]);
}

if ($acao === 'avisar') {
    $id = (int) ($d['id'] ?? 0);
    $st = pdo()->prepare('SELECT id, plano, valor FROM pagamentos WHERE id = ? AND usuario_id = ? AND status = ?');
    $st->execute([$id, $u['id'], 'aguardando']);
    $pg = $st->fetch();
    if (!$pg) {
        responder(404, ['erro' => 'Pedido não encontrado ou já informado.']);
    }
    pdo()->prepare('UPDATE pagamentos SET status = ?, informado_em = ? WHERE id = ?')
        ->execute(['informado', date('Y-m-d H:i:s'), $id]);
    avisar_admin(
        'Tchê Scout: Pix informado por ' . $u['nome'],
        $u['nome'] . ' (' . $u['email'] . ') informou o pagamento do plano ' . $pg['plano'] . ' (R$ ' . number_format((float) $pg['valor'], 2, ',', '.')
        . '). Confira no banco e confirme em /admin.html.'
    );
    responder(200, ['ok' => true, 'mensagem' => 'Recebemos o seu aviso. Assim que o Pix for conferido, o acesso é liberado.']);
}

responder(400, ['erro' => 'Ação inválida.']);
