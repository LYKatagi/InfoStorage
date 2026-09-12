# Vault

Este documento descreve o sistema de cofre do InfoStorage.

## Objetivo

O `Vault` é responsável por controlar o ciclo de vida de um cofre protegido.

Ele coordena:

* Segurança.
* Armazenamento.
* Desbloqueio.
* Bloqueio.
* Expiração por inatividade.
* Leitura e escrita dos dados.
* Validação básica do formato do cofre.

O `Vault` funciona como a camada principal entre a aplicação e os componentes de segurança e armazenamento.

## Estrutura

```text
python/info_storage/vault/
├── __init__.py
├── exceptions.py
├── format.py
├── integrity.py
├── timer.py
└── vault.py
```

## Arquitetura

O `Vault` integra os principais componentes do InfoStorage:

```text
                    ┌──────────────┐
                    │     Vault    │
                    └──────┬───────┘
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
      SecurityManager   Storage      VaultTimer
             │             │             │
             ↓             ↓             ↓
          Argon2id      DAT/JSON     Timeout
             │
             ↓
           Fernet
```

## Criação

Um cofre é criado utilizando uma senha e os dados iniciais.

Fluxo:

```text
Senha + Dados
     ↓
SecurityManager.setup()
     ↓
Salt aleatório
     ↓
Derivação da chave
     ↓
Criptografia dos dados
     ↓
Construção do arquivo
     ↓
Storage
     ↓
vault.dat
```

O arquivo do cofre contém:

```text
MAGIC
VERSION
SALT
ENCRYPTED_DATA
```

## Estado do Vault

O `Vault` mantém o estado de desbloqueio através de:

```python
self.unlocked
```

Quando:

```python
self.unlocked = True
```

o cofre pode ser utilizado, desde que o temporizador ainda não tenha expirado.

Quando:

```python
self.unlocked = False
```

operações protegidas são recusadas.

## Desbloqueio

Para desbloquear um cofre, o sistema:

1. Carrega o arquivo.
2. Divide o conteúdo do formato.
3. Verifica o `MAGIC`.
4. Verifica a versão.
5. Obtém o salt.
6. Deriva a chave usando a senha.
7. Tenta descriptografar os dados.
8. Marca o cofre como desbloqueado.
9. Inicia o temporizador.

Fluxo:

```text
Arquivo
  ↓
Validação
  ↓
Salt
  ↓
Senha
  ↓
Argon2id
  ↓
Chave
  ↓
Fernet
  ↓
Dados originais
```

## Senha incorreta

Uma senha incorreta não deve permitir o acesso aos dados.

Quando a descriptografia falha, o `Vault` gera um erro apropriado.

A aplicação não deve receber a chave interna nem dados parcialmente descriptografados.

## Leitura

O método `load()` verifica primeiro se o cofre ainda está acessível.

Fluxo:

```text
load()
  ↓
_check_access()
  ↓
Verificar timeout
  ↓
Descriptografar
  ↓
Retornar dados
```

A atividade também reinicia o temporizador.

## Salvamento

O método `save()` funciona de maneira semelhante.

Fluxo:

```text
Dados
  ↓
_check_access()
  ↓
Criptografia
  ↓
Construção do formato
  ↓
Storage
  ↓
Arquivo atualizado
```

O arquivo continua utilizando o mesmo salt associado ao cofre.

## Bloqueio

O método `lock()` bloqueia o cofre.

Durante o bloqueio:

```text
unlocked = False
```

O objeto de segurança também é reinicializado para remover a chave ativa da estrutura principal do `Vault`.

O temporizador é interrompido.

## Timeout

O cofre possui proteção contra permanência indefinida em estado desbloqueado.

O `VaultTimer` registra a última atividade.

Exemplo:

```text
Timeout = 300 segundos

Desbloqueio
    ↓
atividade
    ↓
atividade
    ↓
300 segundos sem atividade
    ↓
lock()
```

Quando o tempo limite expira, o cofre é bloqueado automaticamente.

## Controle de acesso

Antes de operações protegidas, o `Vault` utiliza:

```python
_check_access()
```

Esse método:

1. Verifica o timeout.
2. Bloqueia o cofre caso o tempo tenha expirado.
3. Verifica se ele continua desbloqueado.
4. Gera `VaultLockedError` quando necessário.

Isso impede que `save()` e `load()` sejam utilizados enquanto o cofre está bloqueado.

## Formato

O formato atual é definido em:

```text
vault/format.py
```

Atualmente:

```python
FORMAT_VERSION = 1
VAULT_MAGIC = b"INFOSTORAGE"
```

O `MAGIC` identifica arquivos pertencentes ao InfoStorage.

A versão permite que formatos futuros sejam diferenciados.

Exemplo:

```text
INFOSTORAGE
1
...
```

## Validação

Durante o desbloqueio, o `Vault` verifica:

### Estrutura

O arquivo precisa possuir as partes esperadas.

### MAGIC

O identificador precisa ser:

```text
INFOSTORAGE
```

### Versão

A versão armazenada precisa ser compatível com a versão suportada pelo programa.

### Dados criptografados

Os dados precisam conseguir ser descriptografados com a chave derivada da senha fornecida.

Quando uma dessas verificações falha, o sistema pode gerar:

```text
InvalidVaultError
```

## Exceções

As exceções específicas do sistema estão em:

```text
vault/exceptions.py
```

Principais exceções:

```text
VaultError
├── VaultLockedError
├── VaultAlreadyExistsError
├── InvalidVaultError
├── InvalidPasswordError
└── IntegrityError
```

Isso permite que a aplicação trate os erros de forma específica.

## Dependências

O `Vault` depende diretamente de:

```text
SecurityManager
Storage
VaultTimer
format
exceptions
```

Ele não implementa diretamente Argon2id ou Fernet.

Essa separação mantém cada componente responsável por uma única função.

## Responsabilidades

O `Vault` é responsável por:

* Criar cofres.
* Abrir cofres.
* Bloquear cofres.
* Verificar acesso.
* Controlar o timeout.
* Ler dados.
* Salvar dados.
* Validar a estrutura básica do arquivo.

O `Vault` não é responsável diretamente por:

* Implementar Argon2id.
* Implementar Fernet.
* Manipular diretamente arquivos do sistema.
* Implementar a interface gráfica.
* Gerenciar contas do Android.

## Exemplo de uso

```python
from info_storage.vault import Vault


vault = Vault("vault.dat")

vault.create(
    "minha-senha",
    "dados secretos"
)

data = vault.load()

vault.save(
    "novos dados secretos"
)

vault.lock()
```

Para abrir um cofre existente:

```python
from info_storage.vault import Vault


vault = Vault("vault.dat")

data = vault.unlock(
    "minha-senha"
)
```

## Ciclo de vida

O ciclo básico do cofre é:

```text
        ┌─────────┐
        │  Criado │
        └────┬────┘
             ↓
       ┌───────────┐
       │Desbloqueado│
       └─────┬─────┘
             │
       ┌─────┴─────┐
       ↓           ↓
    Atividade   Timeout
       │           │
       └─────┐     ↓
             │   Bloqueado
             ↓
       Desbloqueado
             │
             ↓
          lock()
             │
             ↓
        Bloqueado
```

## Segurança

O `Vault` atua como uma barreira de controle entre os dados e a aplicação.

Nenhuma operação de leitura ou escrita deve ocorrer sem passar pelo controle de acesso.

O fluxo esperado é:

```text
Aplicação
    ↓
Vault
    ↓
SecurityManager
    ↓
Storage
```

Isso reduz a possibilidade de a aplicação acessar diretamente dados protegidos.

## Testes

O sistema deve testar pelo menos:

* Criação do cofre.
* Desbloqueio correto.
* Senha incorreta.
* Tentativa de criar cofre existente.
* Leitura com cofre bloqueado.
* Escrita com cofre bloqueado.
* Bloqueio manual.
* Expiração automática.
* Salvamento.
* Carregamento.
* Formato inválido.
* `MAGIC` inválido.
* Versão inválida.
* Arquivo corrompido.

## Estado atual

O `Vault` atualmente possui:

```text
✅ Criação
✅ Desbloqueio
✅ Bloqueio manual
✅ Bloqueio automático
✅ Timeout
✅ Criptografia
✅ Leitura
✅ Escrita
✅ Validação básica do formato
✅ Tratamento de exceções
```

Funcionalidades planejadas:

```text
⬜ Integridade completa do envelope
⬜ Migração entre versões
⬜ Troca de senha
⬜ Recuperação/backup
⬜ Formato definitivo
⬜ Melhor proteção de dados sensíveis em memória
```

## Princípio de projeto

O `Vault` deve ser o controlador do cofre, não o implementador de todas as funcionalidades.

Cada responsabilidade deve permanecer em seu próprio módulo.

> O Vault controla. A segurança protege. O Storage persiste.
