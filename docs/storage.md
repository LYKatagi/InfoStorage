# Storage

Este documento descreve o sistema de armazenamento do InfoStorage.

## Objetivo

O sistema de armazenamento é responsável por fornecer uma interface única para salvar e carregar dados, independentemente do formato utilizado.

Atualmente, o InfoStorage possui suporte para:

* JSON.
* DAT.

A camada de armazenamento não é responsável pela criptografia. A criptografia é realizada pela camada de segurança antes que os dados sejam enviados ao storage.

## Estrutura

```text
python/info_storage/storage/
├── __init__.py
├── dat.py
├── json.py
└── storage.py
```

## Arquitetura

O sistema utiliza uma camada de abstração para selecionar o backend adequado.

```text
Aplicação
    ↓
Storage
    ↓
┌───────────────┐
│               │
JSONStorage  DatStorage
│               │
JSON            DAT
```

## Storage

O `Storage` funciona como ponto de entrada para operações de leitura e escrita.

Ele mantém os backends disponíveis:

```python
self.backends = {"json": JSONStorage(), "dat": DatStorage()}
```

Isso permite selecionar o backend manualmente ou detectar o formato através da extensão do arquivo.

## Detecção automática

Quando o tipo de armazenamento não é informado, o `Storage` utiliza a extensão do arquivo.

Exemplo:

```text
database.json
    ↓
json

vault.dat
    ↓
dat
```

Caso o arquivo não possua extensão, um erro é gerado.

## JSONStorage

O `JSONStorage` é utilizado para dados estruturados que precisam permanecer legíveis.

Exemplo:

```json
{
    "name": "Example",
    "value": "Data"
}
```

### Salvamento

O método `save()`:

1. Converte o caminho para `Path`.
2. Cria o diretório pai quando necessário.
3. Abre o arquivo em modo de escrita.
4. Serializa os dados usando JSON.

O JSON utiliza:

```python
indent = 4
ensure_ascii = False
```

Isso mantém o arquivo organizado e permite caracteres Unicode.

### Carregamento

O método `load()` abre o arquivo usando UTF-8 e converte o conteúdo de JSON para objetos Python.

## DatStorage

O `DatStorage` trabalha com dados binários.

Ele é o backend utilizado pelo cofre.

Exemplo:

```text
vault.dat
```

### Salvamento

O método `save()`:

1. Converte o caminho para `Path`.
2. Cria o diretório pai quando necessário.
3. Converte `str` para UTF-8 quando necessário.
4. Abre o arquivo em modo binário.
5. Grava os bytes diretamente.

### Carregamento

O método `load()` abre o arquivo em modo binário e retorna os bytes originais.

Exemplo:

```text
Arquivo
   ↓
bytes
   ↓
Vault
```

## Relação com a segurança

O Storage não deve receber a responsabilidade de proteger informações secretas.

O fluxo esperado é:

```text
Dados originais
      ↓
SecurityManager
      ↓
Criptografia
      ↓
Dados criptografados
      ↓
Storage
      ↓
Arquivo
```

Durante a leitura:

```text
Arquivo
   ↓
Storage
   ↓
Dados criptografados
   ↓
SecurityManager
   ↓
Descriptografia
   ↓
Dados o
```
