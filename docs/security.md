# Segurança

Este documento descreve os componentes de segurança do InfoStorage.

## Objetivo

O objetivo do sistema de segurança é proteger informações confidenciais contra:

* Acesso sem autorização.
* Senhas incorretas.
* Leitura direta dos arquivos.
* Alterações acidentais.
* Corrupção dos dados.
* Permanência excessiva do cofre desbloqueado.

## Componentes

A segurança está localizada em:

```text
python/info_storage/security/
├── argon2.py
├── fernet.py
├── keys.py
└── __init__.py
```

## Argon2id

O InfoStorage utiliza Argon2id para derivar uma chave a partir da senha do usuário.

Parâmetros atuais:

| Parâmetro   |     Valor |
| ----------- | --------: |
| Tipo        |  Argon2id |
| Time cost   |         3 |
| Memory cost | 66576 KiB |
| Parallelism |         4 |
| Hash length |  32 bytes |
| Salt length |  16 bytes |

### Por que usar Argon2id?

Argon2id foi projetado para dificultar ataques de tentativa de senha.

Ele utiliza:

* Tempo de processamento.
* Uso de memória.
* Paralelismo.
* Salt aleatório.

O salt impede que a mesma senha gere sempre exatamente o mesmo resultado em cofres diferentes.

## Fernet

O Fernet é usado para criptografar os dados do cofre.

Ele fornece:

* Confidencialidade.
* Autenticação.
* Detecção de alterações.
* Proteção contra descriptografia com chave incorreta.

O fluxo básico é:

```text
Senha
  ↓
Argon2id
  ↓
Chave derivada
  ↓
Fernet
  ↓
Dados criptografados
```

## Chave derivada

A chave derivada pelo Argon2id é convertida para o formato aceito pelo Fernet usando Base64 URL-safe.

A chave não deve ser armazenada diretamente no arquivo do cofre.

## Salt

Cada cofre deve possuir um salt aleatório.

O salt não precisa ser secreto, mas precisa ser armazenado para que a chave possa ser derivada novamente.

O salt é utilizado assim:

```text
Senha + Salt
    ↓
Argon2id
    ↓
Mesma chave derivada
```

## Bloqueio automático

O cofre possui um temporizador de inatividade.

Quando o tempo limite é atingido:

1. O cofre é bloqueado.
2. A chave ativa é removida do objeto de segurança.
3. Operações de leitura e escrita são recusadas.

## Integridade

A integridade será responsável por detectar alterações no conteúdo do arquivo.

O projeto possui um componente baseado em HMAC:

```text
Dados + chave secreta
        ↓
       HMAC
        ↓
Assinatura de integridade
```

Um hash comum não é suficiente para autenticar dados, pois qualquer pessoa que altere o arquivo também poderia recalcular o hash.

## Ameaças consideradas

* Senha incorreta.
* Arquivo corrompido.
* Arquivo modificado manualmente.
* Cofre inexistente.
* Cofre bloqueado.
* Alteração do formato.
* Tentativas repetidas de desbloqueio.
* Vazamento de dados em mensagens de erro.

## Princípios de segurança

### Separação de responsabilidades

Cada módulo possui uma função específica:

```text
Argon2id
    ↓
Derivação da chave

Fernet
    ↓
Criptografia dos dados

IntegrityChecker
    ↓
Verificação de alterações

Vault
    ↓
Orquestração do cofre

Storage
    ↓
Leitura e escrita dos arquivos
```

### Nenhuma senha deve ser armazenada

O InfoStorage não deve salvar a senha original do usuário.

A senha deve ser usada apenas para derivar a chave necessária.

### O salt não é uma senha

O salt pode ser armazenado junto do arquivo do cofre.

Ele não precisa ser secreto, mas deve ser diferente para cada cofre.

### Erros não devem revelar segredos

Mensagens de erro não devem mostrar:

* Senhas.
* Chaves.
* Dados descriptografados.
* Conteúdo privado.
* Informações sensíveis do arquivo.

## Limitações atuais

O sistema ainda precisa evoluir para oferecer:

* Formato binário definitivo.
* Autenticação de todos os campos.
* Proteção contra replay.
* Troca segura de senha.
* Backup seguro.
* Limpeza de dados sensíveis da memória.
* Auditoria externa.
* Proteção específica para Android.
* Limitação de tentativas de desbloqueio.

## Auditoria de segurança

Depois que o sistema estiver estável, serão realizados testes para tentar encontrar falhas.

Exemplos:

* Alterar bytes do arquivo `.dat`.
* Utilizar senhas incorretas.
* Cortar arquivos pela metade.
* Remover partes do cabeçalho.
* Alterar a versão do formato.
* Reutilizar arquivos antigos.
* Tentar carregar arquivos inválidos.
* Interromper uma gravação.
* Verificar se informações secretas aparecem em logs.

Esses testes devem ser realizados apenas nos próprios arquivos e ambientes de teste do projeto.

## Regra de desenvolvimento

Toda nova camada de segurança deve resolver uma ameaça real e possuir testes.

> Segurança não é adicionar complexidade sem motivo. Segurança é reduzir riscos de forma verificável.

## Status

A segurança do InfoStorage ainda está em desenvolvimento.

O projeto não deve ser considerado uma solução de segurança profissional ou definitiva até que seus componentes tenham sido completamente testados e auditados.
