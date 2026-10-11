# InfoStorage

InfoStorage é um sistema de armazenamento seguro desenvolvido em Python, projetado para proteger informações confidenciais através de um sistema de cofre criptografado.

O projeto utiliza **Argon2id** para derivação de chaves e **Fernet** para criptografia dos dados.

## Objetivo

O objetivo do InfoStorage é fornecer uma base segura e modular para armazenar informações privadas em um cofre protegido por senha.

O projeto foi desenvolvido com foco em:

* Segurança.
* Modularidade.
* Testabilidade.
* Separação de responsabilidades.
* Facilidade de expansão.
* Futuro suporte para Android.

## Estrutura

```text
InfoStorage/
├── .gitattributes
├── .gitignore
├── LICENSE
├── pyproject.toml
├── requirements.txt
│
├── android/
│
└── python/
    ├── README.txt
    │
    ├── info_storage/
    │   ├── __init__.py
    │   │
    │   ├── security/
    │   │   ├── __init__.py
    │   │   ├── argon2.py
    │   │   ├── fernet.py
    │   │   └── keys.py
    │   │
    │   ├── storage/
    │   │   ├── __init__.py
    │   │   ├── dat.py
    │   │   ├── json.py
    │   │   └── storage.py
    │   │
    │   └── vault/
    │       ├── __init__.py
    │       ├── exceptions.py
    │       ├── format.py
    │       ├── integrity.py
    │       ├── timer.py
    │       └── vault.py
    │
    └── tests/
        ├── integration/
        └── unit/
            ├── test_keys.py
            ├── test_storage.py
            └── test_vault.py
```

## Arquitetura

O InfoStorage utiliza uma arquitetura modular.

```text
                    InfoStorage
                         │
                         ↓
                       Vault
                         │
              ┌──────────┼──────────┐
              ↓          ↓          ↓
        Security      Storage    Timer
              │          │
        ┌─────┴─────┐    ├── JSON
        ↓           ↓    └── DAT
     Argon2id     Fernet
```

Cada camada possui uma responsabilidade específica.

### Security

Responsável pela proteção criptográfica.

Principais componentes:

* Argon2id.
* Fernet.
* Derivação de chaves.
* Salt.
* Gerenciamento da chave ativa.

### Storage

Responsável pela persistência dos dados.

Backends atuais:

* JSON.
* DAT.

### Vault

Responsável pelo controle do cofre.

Funções principais:

* Criar.
* Desbloquear.
* Bloquear.
* Salvar.
* Carregar.
* Controlar timeout.
* Validar o formato.

### Timer

Controla o tempo de atividade do cofre e permite bloqueio automático após um período de inatividade.

## Fluxo de segurança

A senha do usuário não é utilizada diretamente como chave Fernet.

O processo é:

```text
Senha
  ↓
Salt
  ↓
Argon2id
  ↓
Chave derivada
  ↓
Fernet
  ↓
Dados criptografados
```

Durante o desbloqueio, o processo é revertido logicamente:

```text
Arquivo
  ↓
Salt
  ↓
Senha fornecida
  ↓
Argon2id
  ↓
Chave derivada
  ↓
Fernet
  ↓
Dados
```

## Formato do Vault

O formato atual do arquivo utiliza uma estrutura simples:

```text
MAGIC
VERSION
SALT
ENCRYPTED_DATA
```

Atualmente:

```text
MAGIC   = INFOSTORAGE
VERSION = 1
```

O arquivo utiliza o backend DAT.

## Criptografia

O projeto utiliza:

### Argon2id

Argon2id é utilizado para transformar a senha em uma chave criptográfica através de um processo resistente a ataques de tentativa de senha.

Parâmetros atuais:

```text
Time cost:   3
Memory cost: 66576 KiB
Parallelism: 4
Hash length: 32 bytes
Salt length: 16 bytes
```

### Fernet

Fernet é utilizado para proteger os dados.

Ele fornece criptografia autenticada, permitindo detectar tokens inválidos ou alterados.

## Integridade

O projeto também possui um componente `IntegrityChecker` baseado em HMAC-SHA256.

Sua finalidade é permitir verificações adicionais de integridade.

```text
Dados + Chave
      ↓
    HMAC
      ↓
Assinatura
```

## Bloqueio automático

O cofre possui um temporizador de inatividade.

Quando o limite é alcançado:

```text
Cofre desbloqueado
       ↓
Sem atividade
       ↓
Timeout
       ↓
Cofre bloqueado
```

## Testes

Os testes estão localizados em:

```text
python/tests/
```

Para executar os testes:

```bash
pytest
```

Ou:

```bash
pytest -q
```

Os testes cobrem principalmente:

* Segurança.
* Armazenamento.
* Criação de cofres.
* Desbloqueio.
* Bloqueio.
* Timeout.
* Leitura.
* Escrita.
* Validação do formato.
* Tratamento de erros.

## Desenvolvimento

O projeto é desenvolvido em Python.

As dependências principais incluem:

* `argon2-cffi`
* `cryptography`
* `pytest`

A configuração do projeto está em:

```text
pyproject.toml
```

As dependências também podem ser instaladas através de:

```bash
pip install -r requirements.txt
```

### Compilação

O `Makefile` compila os módulos Python do core/desktop e gera o APK Android. Ele não executa nem inclui a API FastAPI ou o frontend Flask.

```bash
make help
make
```

No Windows, use `mingw32-make`. Para o alvo Android, configure `JAVA_HOME` para o JDK 25 do Android Studio e tenha `uv` instalado, usado pelo Chaquopy para selecionar Python 3.13.

Alvos individuais: `make compile-python` e `make android`.

## Princípios

O projeto segue alguns princípios básicos:

### Separação de responsabilidades

Cada módulo deve possuir uma função clara.

### Segurança por design

A segurança deve ser considerada desde a arquitetura, e não adicionada apenas posteriormente.

### Testabilidade

Componentes importantes devem possuir testes automatizados.

### Modularidade

Novos backends e funcionalidades devem poder ser adicionados sem reescrever o sistema inteiro.

## Futuro

Funcionalidades planejadas incluem:

```text
⬜ Formato definitivo do Vault
⬜ Integridade completa do envelope
⬜ Migração de versões
⬜ Troca de senha
⬜ Sistema de backup
⬜ Melhor gerenciamento de dados sensíveis em memória
⬜ Interface Android
⬜ Testes de segurança mais avançados
```

## Estado atual

O InfoStorage está em desenvolvimento.

A versão atual deve ser considerada uma versão experimental e não uma solução de segurança profissional ou auditada.

## Licença

Este projeto é distribuído sob os termos definidos no arquivo:

```text
LICENSE
```
