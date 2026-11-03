<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

// Formulário "Apoie o projeto": guarda o interesse e avisa o administrador por e-mail. Não exige login.

$d = exigir_post_json();
limitar('interesse', 5, 60);

$nome = trim((string) ($d['nome'] ?? ''));
$email = strtolower(trim((string) ($d['email'] ?? '')));
$tipo = (string) ($d['tipo'] ?? '');
$org = trim((string) ($d['organizacao'] ?? ''));
$msg = trim((string) ($d['mensagem'] ?? ''));

if (mb_strlen($nome) < 2 || mb_strlen($nome) > 80) {
    responder(422, ['erro' => 'Informe seu nome.']);
}
if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 120) {
    responder(422, ['erro' => 'Informe um e-mail válido.']);
}
if (!in_array($tipo, ['apoiador', 'colaborador', 'investidor', 'clube'], true)) {
    responder(422, ['erro' => 'Escolha o tipo de contato.']);
}
if (mb_strlen($org) > 120 || mb_strlen($msg) > 1500) {
    responder(422, ['erro' => 'Texto muito longo.']);
}
if (empty($d['aceite'])) {
    responder(422, ['erro' => 'É preciso aceitar a política de privacidade.']);
}

registrar_tentativa('interesse');
pdo()->prepare(
    'INSERT INTO interesses (nome, email, tipo, organizacao, mensagem, criado_em) VALUES (?, ?, ?, ?, ?, ?)'
)->execute([$nome, $email, $tipo, $org, $msg, date('Y-m-d H:i:s')]);

avisar_admin(
    'Tchê Scout: novo contato (' . $tipo . ') de ' . $nome,
    "Nome: $nome\nE-mail: $email\nTipo: $tipo\nOrganização: $org\n\nMensagem:\n$msg\n"
);
responder(201, ['ok' => true, 'mensagem' => 'Recebemos o seu contato. Responderemos por e-mail em breve. Obrigado!']);
