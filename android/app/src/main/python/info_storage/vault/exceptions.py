class VaultError(Exception):
    """Erro base do sistema de cofre."""


class VaultLockedError(VaultError):
    """Tentativa de usar um cofre bloqueado."""


class VaultAlreadyExistsError(VaultError):
    """Tentativa de criar um cofre existente."""


class InvalidVaultError(VaultError):
    """Arquivo de cofre inválido ou corrompido."""


class InvalidPasswordError(VaultError):
    """Senha incorreta."""


class IntegrityError(VaultError):
    """Falha na verificação de integridade."""
