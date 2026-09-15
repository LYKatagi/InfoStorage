# INFOSTORAGE - PYTHON

Este diretório contém a implementação principal do InfoStorage em Python.

O Python funciona como o núcleo do projeto, contendo os componentes de segurança, armazenamento e gerenciamento do Vault.

# ESTRUTURA

python/
├── README.txt
├── info_storage/
│   ├── **init**.py
│   │
│   ├── security/
│   │   ├── **init**.py
│   │   ├── argon2.py
│   │   ├── fernet.py
│   │   └── keys.py
│   │
│   ├── storage/
│   │   ├── **init**.py
│   │   ├── dat.py
│   │   ├── json.py
│   │   └── storage.py
│   │
│   └── vault/
│       ├── **init**.py
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

# SEGURANÇA

A camada de segurança está localizada em:

info_storage/security/

Os principais componentes são:

argon2.py
Responsável pelo uso do Argon2id.

fernet.py
Responsável pela criptografia e descriptografia usando Fernet.

keys.py
Responsável pelo gerenciamento da chave derivada e da criptografia ativa.

# STORAGE

A camada de armazenamento está localizada em:

info_storage/storage/

Backends disponíveis:

JSON
Usado para dados estruturados em formato JSON.

DAT
Usado para dados binários.

O Vault atualmente utiliza o backend DAT.

# VAULT

A implementação do cofre está localizada em:

info_storage/vault/

O Vault é responsável por:

* Criar cofres.
* Desbloquear cofres.
* Bloquear cofres.
* Salvar dados.
* Carregar dados.
* Controlar timeout.
* Validar o formato do arquivo.

Arquivos principais:

vault.py
Implementação principal.

format.py
Constantes do formato.

timer.py
Temporizador de atividade.

integrity.py
Verificação de integridade.

exceptions.py
Exceções específicas.

# FLUXO

O funcionamento principal segue:

Senha
|
v
Argon2id
|
v
Chave derivada
|
v
Fernet
|
v
Dados criptografados
|
v
Storage
|
v
Arquivo do Vault

# TESTES

Os testes estão localizados em:

tests/

Para executar:

pytest

Ou:

pytest -q

Os testes verificam componentes individuais e o comportamento do Vault.

# EXECUÇÃO

A partir da raiz do projeto, o ambiente Python deve estar configurado de acordo com o pyproject.toml.

Exemplo:

python -m pytest

# DEPENDÊNCIAS

As principais dependências do núcleo Python são:

* argon2-cffi
* cryptography
* pytest

As dependências do projeto estão definidas em:

../requirements.txt

e:

../pyproject.toml

# DESENVOLVIMENTO

O diretório Python deve conter somente a implementação relacionada ao núcleo Python do InfoStorage.

A parte Android fica separada em:

../android/

# PRINCÍPIOS

O código deve seguir os seguintes princípios:

1. Separação de responsabilidades.
2. Segurança por design.
3. Código testável.
4. Componentes independentes.
5. Interfaces simples.
6. Evitar duplicação de lógica.
7. Não armazenar senhas em texto puro.

# ESTADO

O núcleo Python está em desenvolvimento.

A implementação atual já possui:

* Sistema de segurança.
* Argon2id.
* Fernet.
* Derivação de chaves.
* Storage JSON.
* Storage DAT.
* Vault.
* Timeout.
* Exceções específicas.
* Testes automatizados.

Funcionalidades futuras poderão adicionar:

* Migração de formatos.
* Troca de senha.
* Backup.
* Melhor gerenciamento de memória.
* Mais testes de segurança.
* Integração com Android.

