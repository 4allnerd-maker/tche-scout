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
    $st = pdo()->prepare(
        'SELECT id, nome, email, papel, assinatura_ate, demo_pedido_em, demo_ate FROM usuarios WHERE id = ?'
    );
    $st->execute([(int) $_SESSION['uid']]);
    $u = $st->fetch();
    return $u ?: null;
}

function em_demo(array $u): bool
{
    return !empty($u['demo_ate']) && $u['demo_ate'] > date('Y-m-d H:i:s');
}

function tem_premium(array $u): bool
{
    return $u['papel'] === 'admin'
        || (!empty($u['assinatura_ate']) && $u['assinatura_ate'] >= date('Y-m-d'))
        || em_demo($u);
}

function dados_publicos(array $u): array
{
    $dias = null;
    if (!empty($u['assinatura_ate']) && $u['assinatura_ate'] >= date('Y-m-d')) {
        $dias = (int) floor((strtotime($u['assinatura_ate']) - strtotime(date('Y-m-d'))) / 86400);
    }
    return [
        'logado' => true,
        'nome' => $u['nome'],
        'email' => $u['email'],
        'papel' => $u['papel'],
        'premium' => tem_premium($u),
        'assinatura_ate' => $u['assinatura_ate'],
        'dias_restantes' => $dias,
        'demo_ate' => em_demo($u) ? $u['demo_ate'] : null,
        'demo_pedida' => !empty($u['demo_pedido_em']),
        'demo_usada' => !empty($u['demo_ate']),
    ];
}

function entrar_na_conta(int $id): void
{
    iniciar_sessao();
    session_regenerate_id(true);
    $_SESSION['uid'] = $id;
}

/** Soma dias ao acesso do usuário (a partir de hoje, ou do fim do acesso atual se ainda estiver ativo). */
function liberar_dias(int $uid, int $dias): string
{
    $st = pdo()->prepare('SELECT assinatura_ate FROM usuarios WHERE id = ?');
    $st->execute([$uid]);
    $atual = (string) $st->fetchColumn();
    $base = ($atual !== '' && $atual > date('Y-m-d')) ? $atual : date('Y-m-d');
    $nova = date('Y-m-d', strtotime($base . ' +' . $dias . ' days'));
    pdo()->prepare('UPDATE usuarios SET assinatura_ate = ? WHERE id = ?')->execute([$nova, $uid]);
    return $nova;
}

/** Aviso por e-mail ao administrador (falha em silêncio: o aviso também aparece no painel). */
function avisar_admin(string $assunto, string $mensagem): void
{
    $para = (string) (cfg()['admin_email'] ?? '');
    if ($para === '') {
        return;
    }
    @mail($para, '=?UTF-8?B?' . base64_encode($assunto) . '?=', $mensagem, "Content-Type: text/plain; charset=UTF-8\r\n");
}

// ---------------------------------------------------------------- Pix (BR Code estático, "copia e cola")

function pix_tlv(string $id, string $valor): string
{
    return $id . str_pad((string) strlen($valor), 2, '0', STR_PAD_LEFT) . $valor;
}

function pix_crc16(string $dados): string
{
    $crc = 0xFFFF;
    $n = strlen($dados);
    for ($i = 0; $i < $n; $i++) {
        $crc ^= ord($dados[$i]) << 8;
        for ($b = 0; $b < 8; $b++) {
            $crc = ($crc & 0x8000) ? (($crc << 1) ^ 0x1021) : ($crc << 1);
            $crc &= 0xFFFF;
        }
    }
    return strtoupper(str_pad(dechex($crc), 4, '0', STR_PAD_LEFT));
}

function pix_texto(string $s, int $max): string
{
    $s = strtr($s, [
        'á' => 'a', 'à' => 'a', 'ã' => 'a', 'â' => 'a', 'é' => 'e', 'ê' => 'e', 'í' => 'i', 'ó' => 'o', 'õ' => 'o', 'ô' => 'o',
        'ú' => 'u', 'ç' => 'c', 'Á' => 'A', 'À' => 'A', 'Ã' => 'A', 'Â' => 'A', 'É' => 'E', 'Ê' => 'E', 'Í' => 'I',
        'Ó' => 'O', 'Õ' => 'O', 'Ô' => 'O', 'Ú' => 'U', 'Ç' => 'C',
    ]);
    $s = preg_replace('/[^A-Za-z0-9 ]/', '', $s) ?? '';
    return substr(strtoupper(trim($s)), 0, $max);
}

function pix_copia_cola(string $chave, string $nome, string $cidade, float $valor, string $txid): string
{
    $conta = pix_tlv('00', 'br.gov.bcb.pix') . pix_tlv('01', $chave);
    $payload = pix_tlv('00', '01')
        . pix_tlv('01', '11')
        . pix_tlv('26', $conta)
        . pix_tlv('52', '0000')
        . pix_tlv('53', '986')
        . pix_tlv('54', number_format($valor, 2, '.', ''))
        . pix_tlv('58', 'BR')
        . pix_tlv('59', pix_texto($nome, 25))
        . pix_tlv('60', pix_texto($cidade, 15))
        . pix_tlv('62', pix_tlv('05', $txid))
        . '6304';
    return $payload . pix_crc16($payload);
}
