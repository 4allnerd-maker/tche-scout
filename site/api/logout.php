<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

exigir_post_json();
iniciar_sessao();
$_SESSION = [];
if (ini_get('session.use_cookies')) {
    $p = session_get_cookie_params();
    setcookie(session_name(), '', [
        'expires' => time() - 3600,
        'path' => $p['path'],
        'secure' => $p['secure'],
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
}
session_destroy();
responder(200, ['logado' => false]);
