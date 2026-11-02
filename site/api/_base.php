<?php
declare(strict_types=1);

date_default_timezone_set('America/Sao_Paulo');

function responder(int $codigo, array $dados): never
{
    http_response_code($codigo);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($dados, JSON_UNESCAPED_UNICODE);
    exit;
}

function cfg(): array
{
    static $c = null;
    if ($c === null) {
        $arquivo = dirname(__DIR__, 2) . '/config_tchescout.php';
        if (!is_file($arquivo)) {
            error_log('config_tchescout.php não encontrado em ' . $arquivo);
            responder(500, ['erro' => 'Servidor não configurado.']);
        }
        $c = require $arquivo;
    }
    return $c;
}

function pdo(): PDO
{
    static $p = null;
    if ($p === null) {
        $c = cfg();
        try {
            $p = new PDO(
                'mysql:host=' . $c['db_host'] . ';dbname=' . $c['db_nome'] . ';charset=utf8mb4',
                $c['db_usuario'],
                $c['db_senha'],
                [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false,
                ]
            );
        } catch (Throwable $e) {
            error_log('db: ' . $e->getMessage());
            responder(500, ['erro' => 'Serviço indisponível. Tente novamente em instantes.']);
        }
    }
    return $p;
}

function iniciar_sessao(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    $https = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
    session_name('tchescout');
    session_set_cookie_params([
        'lifetime' => 60 * 60 * 24 * 14,
        'path' => '/',
        'secure' => $https,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    session_start();
}

/** Só aceita POST com JSON vindo do próprio site (protege contra requisições de outros sites). */
function exigir_post_json(): array
{
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
        responder(405, ['erro' => 'Método não permitido.']);
    }
    if (stripos($_SERVER['CONTENT_TYPE'] ?? '', 'application/json') !== 0) {
        responder(415, ['erro' => 'Formato inválido.']);
    }
    $origem = $_SERVER['HTTP_ORIGIN'] ?? '';
    if ($origem !== '') {
        $host_origem = (string) parse_url($origem, PHP_URL_HOST);
        $host_site = explode(':', $_SERVER['HTTP_HOST'] ?? '')[0];
        if (strcasecmp($host_origem, $host_site) !== 0) {
            responder(403, ['erro' => 'Origem não permitida.']);
        }
    }
    $corpo = json_decode((string) file_get_contents('php://input'), true);
    if (!is_array($corpo)) {
        responder(400, ['erro' => 'Dados inválidos.']);
    }
    return $corpo;
}

function ip_cliente(): string
{
    return substr((string) ($_SERVER['REMOTE_ADDR'] ?? '0.0.0.0'), 0, 45);
}

function limitar(string $tipo, int $maximo, int $janela_min): void
{
    $desde = date('Y-m-d H:i:s', time() - $janela_min * 60);
    $st = pdo()->prepare('SELECT COUNT(*) FROM tentativas WHERE ip = ? AND tipo = ? AND criado_em > ?');
    $st->execute([ip_cliente(), $tipo, $desde]);
    if ((int) $st->fetchColumn() >= $maximo) {
        responder(429, ['erro' => 'Muitas tentativas. Aguarde alguns minutos e tente de novo.']);
    }
}

function registrar_tentativa(string $tipo): void
{
    pdo()->prepare('INSERT INTO tentativas (ip, tipo, criado_em) VALUES (?, ?, ?)')
        ->execute([ip_cliente(), $tipo, date('Y-m-d H:i:s')]);
}

function usuario_atual(): ?array
{
    iniciar_sessao();
    if (empty($_SESSION['uid'])) {
        return null;
    }
    $st = pdo()->prepare('SELECT id, nome, email, papel, assinatura_ate FROM usuarios WHERE id = ?');
    $st->execute([(int) $_SESSION['uid']]);
    $u = $st->fetch();
    return $u ?: null;
}

function tem_premium(array $u): bool
{
    return $u['papel'] === 'admin'
        || (!empty($u['assinatura_ate']) && $u['assinatura_ate'] >= date('Y-m-d'));
}

function dados_publicos(array $u): array
{
    return [
        'logado' => true,
        'nome' => $u['nome'],
        'email' => $u['email'],
        'papel' => $u['papel'],
        'premium' => tem_premium($u),
        'assinatura_ate' => $u['assinatura_ate'],
    ];
}

function entrar_na_conta(int $id): void
{
    iniciar_sessao();
    session_regenerate_id(true);
    $_SESSION['uid'] = $id;
}
