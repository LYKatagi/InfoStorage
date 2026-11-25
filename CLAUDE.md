# Regras do Projeto (InfoStorage)

## Stack e Arquitetura
- **Linguagem:** Python 3.14/3.15 + Kotlin (Jetpack Compose)
- **Core & APIs (`python/info_storage/`):**
  - `auth/`, `security/`, `storage/`, `vault/`: núcleo de criptografia (Argon2/Fernet) e cofre
  - `web/`: API backend (FastAPI) — entrypoint em `python/info_storage/web/main.py`
  - `desktop/`: cliente desktop
  - `mobile_api.py`: ponte Python para o app Android
- **Web Frontend (`web_frontend/`):** interface web (Flask/Jinja2) — entrypoint em `web_frontend/app.py`
- **Android (`android/`):** UI em Kotlin (`app/src/main/java/com/luiz/infostorage/`). **Atenção:** `android/app/src/main/python/` é uma cópia embarcada do pacote `python/info_storage/` (não edite lá a menos que solicitado).
- **Testes:** `python/tests/unit/` e `web_frontend/tests/`

## Comandos Úteis
- Rodar testes unitários: `pytest python/tests`
- Rodar testes frontend: `pytest web_frontend/tests`
- Rodar API Backend: `python -m info_storage.web`
- Rodar Frontend Web: `python -m web_frontend`

## Diretrizes de Economia e Código
- Responda em português de forma direta e curta, sem explicações longas.
- Leia apenas os arquivos estritamente necessários para a tarefa.
- Consulte `docs/` (`security.md`, `storage.md`, `vault.md`, `web-api.md`) apenas se precisar entender regras de negócio.
- Não refatore código não solicitado e não adicione comentários óbvios.
