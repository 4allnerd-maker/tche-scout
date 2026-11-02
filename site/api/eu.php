<?php
declare(strict_types=1);
require __DIR__ . '/_base.php';

$u = usuario_atual();
responder(200, $u ? dados_publicos($u) : ['logado' => false]);
