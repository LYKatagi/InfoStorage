from cryptography.fernet import Fernet, InvalidToken


class Crypto(Fernet):
    def __init__(self, key=None):
        if key is None:
            key = Fernet.generate_key()

        self.key = key

        super().__init__(self.key)

    def encrypt_data(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")

        return self.encrypt(data)

    def decrypt_data(self, data):
        try:
            original_data = self.decrypt(data)
            return original_data.decode("utf-8")
        except InvalidToken:
            raise ValueError("Chave incorreta ou dados inválidos.")