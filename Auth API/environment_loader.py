import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv


class Environment_loader:

    @staticmethod
    def load_environment_data():
        if os.getenv("APP_ENV") is None:
            # APP_ENV ikke sat → vi er i testmiljø, indlæs fra .env-filen
            env_path = os.path.join(os.path.dirname(__file__), ".env")
            load_dotenv(env_path)

        environment_name = os.getenv("ENVIRONMENT_NAME")
        if environment_name == "test":
            print("ADVARSEL: Indlæser test-secrets fra .env fil — brug ikke i produktion!")

        secret = os.getenv("HASH_KEY")
        if secret is not None:
            secret = secret.encode()
        else:
            raise ValueError("HASH_KEY ikke fundet i miljøvariabler eller .env fil")

        fernet_key = os.getenv("ENCRYPTION_KEY")
        if fernet_key is not None:
            fernet = Fernet(fernet_key)
        else:
            raise ValueError("ENCRYPTION_KEY ikke fundet i miljøvariabler eller .env fil")

        return secret, fernet
