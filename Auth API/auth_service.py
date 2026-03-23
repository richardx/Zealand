import hashlib
import hmac
import os
import base64
import datetime

import jwt
from fastapi import HTTPException

from environment_loader import Environment_loader
from models import User


class Auth_service:
    _algorithm = "HS256"

    # Secrets indlæses én gang ved opstart — aldrig hardcoded
    _secret, _fernet = Environment_loader.load_environment_data()

    # --- Password hashing ---

    @staticmethod
    def hash_password(password: str) -> str:
        """Hasher et password med HMAC-SHA256 og et tilfældigt salt.

        Format der gemmes: base64(salt + hmac_digest)
        Salt er 16 tilfældige bytes, ny for hvert kald.
        """
        salt = os.urandom(16)
        digest = hmac.new(
            Auth_service._secret,
            salt + password.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(salt + digest).decode()

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verificerer et password mod et gemt hash.

        Bruger hmac.compare_digest for at undgå timing-angreb.
        """
        data = base64.b64decode(stored_hash.encode())
        salt = data[:16]
        stored_digest = data[16:]
        new_digest = hmac.new(
            Auth_service._secret,
            salt + password.encode(),
            hashlib.sha256
        ).digest()
        return hmac.compare_digest(stored_digest, new_digest)

    # --- Kryptering ---

    @staticmethod
    def encrypt_data(plaintext: str) -> str:
        """Krypterer en tekst med Fernet (AES-128-CBC + HMAC-SHA256)."""
        return Auth_service._fernet.encrypt(plaintext.encode()).decode()

    @staticmethod
    def decrypt_data(token: str) -> str:
        """Dekrypterer en Fernet-krypteret tekst."""
        return Auth_service._fernet.decrypt(token.encode()).decode()

    # --- JWT tokens ---

    @staticmethod
    def get_bearer_token(user: User) -> str:
        """Genererer et JWT Bearer token for en bruger.

        Payload indeholder:
        - sub: brugernavn (subject)
        - roles: liste af brugerens roller
        - exp: udløbstidspunkt (1 time fra nu)
        - iat: udstedelsestidspunkt
        """
        payload = {
            "sub": user.username,
            "roles": list(user.roles),
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1),
            "iat": datetime.datetime.now(datetime.UTC),
        }
        token = jwt.encode(payload, Auth_service._secret, algorithm=Auth_service._algorithm)
        return f"Bearer {token}"

    @staticmethod
    def verify_token(token: str) -> dict:
        """Validerer et JWT Bearer token og returnerer payload.

        Kaster HTTPException 401 hvis token er udløbet eller ugyldigt.
        """
        token_data = token.split()[1]
        try:
            payload = jwt.decode(
                token_data,
                Auth_service._secret,
                algorithms=[Auth_service._algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token udløbet")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Ugyldigt token")
