<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

$d = exigir_post_json();
limitar('login', 8, 15);

$email = strtolower(trim((string) ($d['email'] ?? '')));
$senha = (string) ($d['senha'] ?? '');

$st = pdo()->prepare('SELECT id, senha_hash FROM usuarios WHERE email = ?');
$st->execute([$email]);
$u = $st->fetch();

// Mesmo com e-mail inexistente, gasta o mesmo tempo: evita descobrir quais e-mails existem pelo tempo de resposta.
$hash = $u ? $u['senha_hash'] : password_hash(bin2hex(random_bytes(8)), PASSWORD_DEFAULT);
$ok = password_verify($senha, $hash) && $u;

if (!$ok) {
    registrar_tentativa('login');
    responder(401, ['erro' => 'E-mail ou senha incorretos.']);
}

if (password_needs_rehash($hash, PASSWORD_DEFAULT)) {
    pdo()->prepare('UPDATE usuarios SET senha_hash = ? WHERE id = ?')
        ->execute([password_hash($senha, PASSWORD_DEFAULT), $u['id']]);
}
pdo()->prepare('UPDATE usuarios SET ultimo_login = ? WHERE id = ?')->execute([date('Y-m-d H:i:s'), $u['id']]);

entrar_na_conta((int) $u['id']);
responder(200, dados_publicos(usuario_atual()));
