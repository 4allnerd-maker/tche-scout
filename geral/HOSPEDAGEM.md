# Publicar o site com login na Hostinger (plano Premium: PHP + MySQL)

> O servidor de login (pasta `site/api/`) foi escrito mas **ainda não foi testado num servidor PHP**. Faça o passo 7 antes de divulgar.

## Estrutura no servidor
```
/home/uXXXX/                      <- pasta da conta (fora do site)
├── config_tchescout.php          <- configuração com senhas (NUNCA dentro de public_html)
├── dados_tchescout/              <- JSONs de dados (fora do site: ninguém baixa direto)
│   ├── ranking.json  ligas.json  times.json
│   └── jogadores/  serie-a-2026.json ...
└── public_html/                  <- conteúdo da pasta  site/  (sem a pasta site/dados)
```

## Passo a passo
1. **Banco:** hPanel → Bancos de dados → MySQL → criar banco e usuário. Anote nome, usuário e senha.
2. **Configuração:** copie `site/api/config.exemplo.php` para `/home/uXXXX/config_tchescout.php` (Gerenciador de Arquivos) e preencha. Gere textos longos e aleatórios para `token_instalacao` e `webhook_segredo`, e defina uma `admin_senha` forte (12+ caracteres). Ajuste `pasta_dados` para `/home/uXXXX/dados_tchescout`.
3. **Dados:** rode `python geral/importar.py` no seu computador e suba o conteúdo de `site/dados/` para `/home/uXXXX/dados_tchescout/` (não para o public_html).
4. **Site:** suba o conteúdo de `site/` para `public_html/`, **exceto** a pasta `dados/` e o arquivo `liga.html` se não quiser a página de times. Ative o SSL em hPanel → Segurança → SSL.
5. **Instalar:** abra `https://tchescout.com.br/api/instalar.php?token=SEU_TOKEN`. Deve aparecer "Tabelas prontas" e "Administrador criado".
6. **Apagar** `api/instalar.php` do servidor e remova a `admin_senha` do arquivo de configuração (a senha já está gravada com criptografia no banco).
7. **Testar** (obrigatório): criar uma conta de teste, entrar e sair; abrir `https://tchescout.com.br/api/dados.php?f=ranking` **sem estar logado** (deve dar 401, nunca os dados); entrar como administrador e ver o ranking completo; entrar como conta comum e ver só o top 25.

## Assinatura paga
- Escolha o gateway (Mercado Pago, Stripe, Kiwify, Hotmart, Asaas...). Crie o produto "Premium" lá, copie o link de pagamento para `CHECKOUT_URL` em `site/assets/config.js` e o preço em `PRECO`.
- Configure no gateway o aviso (webhook) para `https://tchescout.com.br/api/webhook.php`. O arquivo é um **modelo**: precisa ser adaptado ao formato e à assinatura oficial do gateway escolhido.
- Para liberar alguém manualmente (cortesia ou teste), no phpMyAdmin: `UPDATE usuarios SET assinatura_ate = '2026-12-31' WHERE email = 'pessoa@exemplo.com';`

## Teste local sem servidor
`abrir_site_geral.bat` mostra o site com um modo de teste só no localhost: adicione `?dev=admin`, `?dev=premium`, `?dev=gratis` ou `?dev=visitante` ao endereço de qualquer página. Esse modo não existe no site publicado.

## Cuidados
- Faça backup periódico do banco (hPanel → Backups).
- Cadastros guardam nome e e-mail: mantenha as políticas de privacidade e termos atualizados (`site/legal/`).
- Confira nos termos do FootyStats se é permitido exibir os dados em produto pago antes de cobrar.
