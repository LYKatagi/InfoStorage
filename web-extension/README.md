# Extensão InfoStorage

Extensão Chromium Manifest V3 para solicitar a geração de senhas à API InfoStorage.

## Instalação local

1. Inicie a API conforme `docs/web-api.md`.
2. Abra `chrome://extensions` ou `edge://extensions`.
3. Ative o modo de desenvolvedor e escolha **Carregar sem compactação**.
4. Selecione a pasta `web-extension`.
5. Abra a extensão, informe o endereço base da API e entre com sua conta InfoStorage.

A URL padrão é `http://127.0.0.1:8000`. Para endereços remotos, a extensão exige HTTPS e pede acesso ao host escolhido. O token é mantido em armazenamento de sessão do navegador; a senha mestra não é armazenada.

Abra o popup no site e clique em **Ativar neste site** para conceder acesso àquele domínio. A extensão então detecta formulários HTML de login e cadastro nas páginas desse site. Quando um formulário com senha é enviado, salva a credencial na API InfoStorage; se já houver uma credencial para o mesmo domínio e usuário, atualiza a senha existente. O popup mostra uma confirmação. Use **Desativar** para parar a detecção e remover a permissão do site quando ela não for compartilhada com o endereço da API.

O acesso ao site é concedido por domínio e pode ser revogado nas configurações da extensão. A extensão só captura campos quando um formulário com senha é enviado. Formulários personalizados sem elemento `<form>` podem não ser detectados. Se a API estiver indisponível ou a sessão tiver expirado, a credencial fica pendente na sessão do navegador e pode ser salva no popup depois de reconectar.

O gerador chama `POST /api/v1/passwords/generate` e oferece cópia da senha resultante. A permissão da API e a permissão de detecção dos sites são solicitadas separadamente.
