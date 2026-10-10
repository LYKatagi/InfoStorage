from pathlib import Path

from info_storage.auth.authenticator import Authenticator
from info_storage.auth.exceptions import (
    AlreadyAuthenticatedError,
    InvalidCredentialsError,
    UserNotAuthenticatedError,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CREDENTIALS_FILE = DATA_DIR / "credentials.json"


def create_directories() -> None:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def register_user(
    authenticator: Authenticator,
) -> None:
    print("\n=== Criar conta ===")

    password = input("Digite uma senha: ")
    confirmation = input("Confirme a senha: ")

    if password != confirmation:
        print("As senhas não são iguais.")
        return

    try:
        authenticator.register(password)
    except FileExistsError:
        print("As credenciais já estão cadastradas.")
    except ValueError as error:
        print(f"Senha inválida: {error}")
    except TypeError as error:
        print(f"Entrada inválida: {error}")
    else:
        print("Conta criada com sucesso.")


def login(
    authenticator: Authenticator,
) -> None:
    print("\n=== Login ===")

    password = input("Digite sua senha: ")

    try:
        authenticator.authenticate(password)
    except InvalidCredentialsError as error:
        print(error)
    except AlreadyAuthenticatedError as error:
        print(error)
    else:
        print("Login realizado com sucesso.")


def logout(
    authenticator: Authenticator,
) -> None:
    try:
        authenticator.logout()
    except UserNotAuthenticatedError as error:
        print(error)
    else:
        print("Logout realizado com sucesso.")


def show_status(
    authenticator: Authenticator,
) -> None:
    if authenticator.authenticated:
        print("Status: autenticado")
    else:
        print("Status: não autenticado")

    if authenticator.security.unlocked:
        print("Criptografia: desbloqueada")
    else:
        print("Criptografia: bloqueada")


def main() -> None:
    create_directories()

    authenticator = Authenticator(
        credentials_path=CREDENTIALS_FILE,
    )

    while True:
        auth_action = "Login" if authenticator.credentials.exists() else "Criar conta"
        print(
            f"""
==============================
        INFOSTORAGE
==============================

1. {auth_action}
2. Logout
3. Ver status
0. Sair
"""
        )

        option = input("Escolha uma opção: ").strip()

        if option == "1":
            if authenticator.credentials.exists():
                login(authenticator)
            else:
                register_user(authenticator)

        elif option == "2":
            logout(authenticator)

        elif option == "3":
            show_status(authenticator)

        elif option == "0":
            if authenticator.authenticated:
                authenticator.logout()

            print("Encerrando InfoStorage...")
            break

        else:
            print("Opção inválida.")
