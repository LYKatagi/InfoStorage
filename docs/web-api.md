# API Web

A API HTTP expõe o cofre InfoStorage com contas isoladas, sessões Bearer e rotas para credenciais e notas. Os dados continuam criptografados no disco pelo `Vault` existente.

## Instalação e execução

Na raiz do repositório, instale as dependências:

```powershell
py -m pip install -r requirements.txt
```

Inicie a API localmente:

```powershell
py -m uvicorn --app-dir python info_storage.web.main:app --host 127.0.0.1 --port 8000
```

Documentação interativa: `http://127.0.0.1:8000/docs`.

Em outro terminal, inicie a interface Flask:

```powershell
py -m web_frontend
```

A interface fica em `http://127.0.0.1:5000` e envia as operações para a API em `INFOSTORAGE_API_URL` (padrão `http://127.0.0.1:8000`). O cookie contém apenas um identificador de sessão assinado; o token Bearer da API fica em memória no processo Flask. Defina `INFOSTORAGE_FLASK_SECRET` para uma chave estável e aleatória; `INFOSTORAGE_COOKIE_SECURE=1` habilita cookies `Secure` quando servido por HTTPS.

## Android

Na tela inicial do app é possível escolher **Somente local** ou **Sincronizar API**. O modo local mantém o armazenamento no dispositivo e não faz chamadas HTTP. No modo sincronizado, informe a URL, usuário e senha da conta da API; o token de sessão fica apenas em memória no app. Os dois modos são cofres separados: escolher sincronização não envia automaticamente um cofre local existente.

Para o emulador Android padrão, use `http://10.0.2.2:8000` e inicie a API acessível ao emulador, por exemplo `py -m uvicorn --app-dir python info_storage.web.main:app --host 0.0.0.0 --port 8000`. O Android só permite HTTP nesse endereço de desenvolvimento; em dispositivos físicos ou servidores remotos, configure HTTPS e use a URL `https://`.

Por padrão, os dados ficam em `web/data/`. Defina `INFOSTORAGE_WEB_DATA` para usar outro diretório e `INFOSTORAGE_SESSION_TTL` para ajustar a duração da sessão em segundos (mínimo de 60; padrão 900).

## Sessão e autenticação

`POST /api/v1/auth/register` e `POST /api/v1/auth/login` recebem:

```json
{"username": "ana", "password": "uma senha forte"}
```

As respostas contêm um token Bearer aleatório. Envie-o em `Authorization: Bearer <token>`. As sessões expiram por inatividade, são mantidas apenas em memória e são revogadas no logout ou ao iniciar uma nova sessão para a mesma conta. Reiniciar o servidor invalida todas as sessões. O nome de usuário é normalizado sem diferenciar maiúsculas de minúsculas; a senha é usada pelo sistema Argon2id e para desbloquear o cofre.

## Rotas

Todas as rotas abaixo, exceto saúde e autenticação, exigem sessão válida:

| Método | Caminho | Ação |
| --- | --- | --- |
| GET | `/health` | Verifica disponibilidade |
| POST | `/api/v1/auth/register` | Cria usuário e cofre |
| POST | `/api/v1/auth/login` | Inicia sessão |
| GET | `/api/v1/auth/me` | Retorna o usuário da sessão |
| POST | `/api/v1/auth/logout` | Revoga sessão e bloqueia cofre |
| GET/POST | `/api/v1/credentials` | Lista ou cria credenciais |
| GET/PUT/DELETE | `/api/v1/credentials/{id}` | Consulta, atualiza ou remove credencial |
| GET/POST | `/api/v1/notes` | Lista ou cria notas |
| GET/PUT/DELETE | `/api/v1/notes/{id}` | Consulta, atualiza ou remove nota |
| GET | `/api/v1/vault/summary` | Resume quantidades do cofre da sessão |
| GET | `/api/v1/search?q=termo` | Busca autenticada sem retornar senhas |

Credenciais usam `title`, `username`, `password` e `notes`. Notas usam `title` e `content`. Segredos só são retornados em rotas autenticadas; as respostas recebem `Cache-Control: no-store`.

## Segurança de rede

O servidor deve permanecer em `127.0.0.1` para desenvolvimento local. Não exponha a API à rede pública sem TLS, limitação de tentativas, gestão persistente de sessões e uma revisão de segurança. As sessões em memória não são compartilhadas entre processos, portanto execute uma única instância do Uvicorn.

O aplicativo Tkinter pode ser iniciado com `py -m info_storage.desktop`. Ele oferece armazenamento local cifrado e sincronização opcional com a API; no modo local, não envia dados pela rede. Para sincronizar pelo emulador Android, use `http://10.0.2.2:8000`; no desktop local, use `http://127.0.0.1:8000`. Para hosts remotos, configure HTTPS.

## Testes

```powershell
$env:PYTHONPATH = "python"
py -m pytest python/tests/unit/test_web_api.py
```