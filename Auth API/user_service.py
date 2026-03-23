from fastapi import HTTPException

from auth_service import Auth_service
from flat_file_loader import Flat_file_loader
from models import User, Role


class User_service:

    def __init__(self, database_file: str = "db_user_flat_file.json"):
        self._file_loader = Flat_file_loader(database_file)
        self._user_db: dict = {}
        self._load_database()

    # --- Private hjælpemetoder ---

    def _load_database(self):
        raw_data = self._file_loader.load()
        if not raw_data:
            print("Ingen database fundet — opretter standard admin-bruger.")
            self._create_default_admin()
        else:
            for username, data in raw_data.items():
                try:
                    self._user_db[username] = User(**data)
                except Exception as e:
                    print(f"ADVARSEL: Springer ugyldig bruger '{username}' over: {e}")

    def _create_default_admin(self):
        admin = User(
            username="admin",
            password=Auth_service.hash_password("admin"),
            first_name=Auth_service.encrypt_data("admin_first_name"),
            last_name=Auth_service.encrypt_data("admin_last_name"),
            active=True,
            roles=[Role.admin],
        )
        self._user_db = {admin.username: admin}
        self._save_database()

    def _save_database(self):
        self._file_loader.save({k: v.toDict() for k, v in self._user_db.items()})

    def _get_user(self, username: str) -> User:
        user = self._user_db.get(username)
        if user is None:
            raise HTTPException(status_code=404, detail=f"Bruger '{username}' ikke fundet")
        return user

    def _check_email(self, username: str):
        parts = username.split("@")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise HTTPException(status_code=400, detail="Ugyldigt email-format")

    def _has_role(self, username: str, role: Role) -> bool:
        user = self._user_db.get(username)
        if user is None:
            return False
        return role in user.roles

    # --- Offentlige metoder ---

    def register_user(self, username: str, password: str, first_name: str, last_name: str, roles: list):
        """Opretter en ny bruger. Username skal være email-format."""
        self._check_email(username)
        if username in self._user_db:
            raise HTTPException(status_code=400, detail="Brugernavn er allerede taget")
        user = User(
            username=username,
            password=Auth_service.hash_password(password),
            first_name=Auth_service.encrypt_data(first_name),
            last_name=Auth_service.encrypt_data(last_name),
            active=True,
            roles=roles,
        )
        self._user_db[username] = user
        self._save_database()
        return user

    def get_bearer_token(self, username: str, password: str) -> str:
        """Returnerer et JWT Bearer token hvis credentials er korrekte."""
        user = self._user_db.get(username)
        if not user or not Auth_service.verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Ugyldigt brugernavn eller password")
        return Auth_service.get_bearer_token(user)

    def deactivate_user(self, token: str, username_to_deactivate: str):
        """Deaktiverer en bruger.

        Regler:
        - Admin kan deaktivere alle brugere
        - En bruger kan kun deaktivere sig selv
        - En deaktiveret bruger kan ikke deaktivere andre
        """
        payload = Auth_service.verify_token(token)
        requester_username = payload["sub"]
        requester = self._get_user(requester_username)

        if not requester.active:
            raise HTTPException(status_code=403, detail="Ingen rettigheder")

        if Role.admin in requester.roles:
            pass  # Admin må deaktivere alle
        elif requester_username == username_to_deactivate:
            pass  # Bruger må deaktivere sig selv
        else:
            raise HTTPException(status_code=403, detail="Ingen rettigheder")

        user = self._get_user(username_to_deactivate)
        user.active = False
        self._save_database()

    def activate_user(self, token: str, username_to_activate: str):
        """Reaktiverer en bruger. Kun admin har rettighed."""
        payload = Auth_service.verify_token(token)
        requester_username = payload["sub"]
        requester = self._get_user(requester_username)

        if Role.admin not in requester.roles:
            raise HTTPException(status_code=403, detail="Kun admin kan aktivere brugere")

        user = self._get_user(username_to_activate)
        user.active = True
        self._save_database()

    def change_password(self, token: str, old_password: str, new_password: str):
        """Skifter password for den bruger der ejer tokenet.

        Verificerer at det gamle password er korrekt inden skift.
        """
        payload = Auth_service.verify_token(token)
        username = payload["sub"]
        user = self._get_user(username)

        if not Auth_service.verify_password(old_password, user.password):
            raise HTTPException(status_code=401, detail="Forkert nuværende password")

        user.password = Auth_service.hash_password(new_password)
        self._save_database()
