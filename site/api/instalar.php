<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

// Roda UMA vez: cria as tabelas e a conta de administrador. DEPOIS DE USAR, APAGUE ESTE ARQUIVO DO SERVIDOR.
// Uso: abra  https://seusite/api/instalar.php?token=SEU_TOKEN_DA_CONFIG

header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: no-store');

$c = cfg();
$token = (string) ($_GET['token'] ?? '');
if (empty($c['token_instalacao']) || !hash_equals((string) $c['token_instalacao'], $token)) {
    http_response_code(403);
    exit('Não autorizado.');
}

$db = pdo();
$db->exec(
    'CREATE TABLE IF NOT EXISTS usuarios (
        id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(80) NOT NULL,
        email VARCHAR(120) NOT NULL,
        senha_hash VARCHAR(255) NOT NULL,
        papel ENUM(\'usuario\',\'admin\') NOT NULL DEFAULT \'usuario\',
        assinatura_ate DATE NULL,
        aceite_em DATETIME NOT NULL,
        criado_em DATETIME NOT NULL,
        ultimo_login DATETIME NULL,
        UNIQUE KEY uq_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
);
$db->exec(
    'CREATE TABLE IF NOT EXISTS tentativas (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
        ip VARCHAR(45) NOT NULL,
        tipo VARCHAR(20) NOT NULL,
        criado_em DATETIME NOT NULL,
        KEY idx_busca (ip, tipo, criado_em)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci'
);
echo "Tabelas prontas.\n";

$email = strtolower(trim((string) ($c['admin_email'] ?? '')));
$senha = (string) ($c['admin_senha'] ?? '');
if ($email === '' || strlen($senha) < 12 || $senha === 'TROQUE-ESTA-SENHA') {
    exit("Administrador NÃO criado: defina admin_email e uma admin_senha forte (12+ caracteres) na config e rode de novo.\n");
}
$st = $db->prepare('SELECT id FROM usuarios WHERE email = ?');
$st->execute([$email]);
if ($st->fetch()) {
    exit("Administrador já existe ($email). Nada a fazer.\n");
}
$agora = date('Y-m-d H:i:s');
$db->prepare('INSERT INTO usuarios (nome, email, senha_hash, papel, aceite_em, criado_em) VALUES (?, ?, ?, ?, ?, ?)')
    ->execute(['Administrador', $email, password_hash($senha, PASSWORD_DEFAULT), 'admin', $agora, $agora]);
echo "Administrador criado: $email\n\nAGORA APAGUE api/instalar.php do servidor e troque/remova a admin_senha da config.\n";
