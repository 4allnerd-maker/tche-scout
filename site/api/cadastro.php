<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

$d = exigir_post_json();
limitar('cadastro', 5, 60);

$nome = trim((string) ($d['nome'] ?? ''));
$email = strtolower(trim((string) ($d['email'] ?? '')));
$senha = (string) ($d['senha'] ?? '');

if (mb_strlen($nome) < 2 || mb_strlen($nome) > 80) {
    responder(422, ['erro' => 'Informe seu nome (2 a 80 caracteres).']);
}
if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 120) {
    responder(422, ['erro' => 'Informe um e-mail válido.']);
}
if (strlen($senha) < 8 || strlen($senha) > 72) {
    responder(422, ['erro' => 'A senha deve ter de 8 a 72 caracteres.']);
}
if (empty($d['aceite'])) {
    responder(422, ['erro' => 'É preciso aceitar os termos de uso e a política de privacidade.']);
}

registrar_tentativa('cadastro');
$agora = date('Y-m-d H:i:s');
try {
    $st = pdo()->prepare(
        'INSERT INTO usuarios (nome, email, senha_hash, papel, aceite_em, criado_em) VALUES (?, ?, ?, ?, ?, ?)'
    );
    $st->execute([$nome, $email, password_hash($senha, PASSWORD_DEFAULT), 'usuario', $agora, $agora]);
} catch (PDOException $e) {
    if ($e->getCode() === '23000') {
        responder(409, ['erro' => 'Este e-mail já está cadastrado. Entre com a sua senha.']);
    }
    error_log('cadastro: ' . $e->getMessage());
    responder(500, ['erro' => 'Não foi possível criar a conta agora. Tente novamente.']);
}

entrar_na_conta((int) pdo()->lastInsertId());
responder(201, dados_publicos(usuario_atual()));
