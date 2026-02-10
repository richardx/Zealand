import json
import os
import hashlib
import base64
from cryptography.fernet import Fernet

DB_FILE = "flat_file_db.json"
KEY_FILE = "secret.key"


# --- Kryptering (Fernet/AES) ---

def _load_key():
    """Indlæser krypteringsnøglen. Opretter en ny hvis den ikke findes."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    with open(KEY_FILE, "rb") as f:
        return f.read()


def encrypt(text):
    """Krypterer en tekst med Fernet (AES)."""
    f = Fernet(_load_key())
    return f.encrypt(text.encode()).decode()


def decrypt(token):
    """Dekrypterer en tekst med Fernet (AES)."""
    f = Fernet(_load_key())
    return f.decrypt(token.encode()).decode()


# --- Hashing (SHA-256) ---

def hash_password(password):
    """Hasher et password med SHA-256. Kan ikke dekrypteres."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    """Verificerer et password mod et hash."""
    return hashlib.sha256(password.encode()).hexdigest() == hashed


# --- Database funktioner ---

def _load_db():
    """Indlæser databasen fra JSON-filen."""
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_db(data):
    """Gemmer data til JSON-filen."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _next_id(users):
    """Finder næste ledige person_id."""
    if not users:
        return 1
    return max(u["person_id"] for u in users) + 1


def create_user(first_name, last_name, address, street_number, password, enabled=True):
    """Opretter en ny bruger. Persondata krypteres, password hashes."""
    users = _load_db()
    user = {
        "person_id": _next_id(users),
        "first_name": encrypt(first_name),
        "last_name": encrypt(last_name),
        "address": encrypt(address),
        "street_number": encrypt(street_number),
        "password": hash_password(password),
        "enabled": enabled
    }
    users.append(user)
    _save_db(users)
    return user


def get_user(person_id):
    """Henter en bruger og dekrypterer persondata."""
    for user in _load_db():
        if user["person_id"] == person_id:
            decrypted = {
                "person_id": user["person_id"],
                "first_name": decrypt(user["first_name"]),
                "last_name": decrypt(user["last_name"]),
                "address": decrypt(user["address"]),
                "street_number": decrypt(user["street_number"]),
                "password": user["password"],
                "enabled": user["enabled"]
            }
            return decrypted
    return None


def get_all_users():
    """Henter alle brugere og dekrypterer persondata."""
    users = _load_db()
    decrypted_users = []
    for user in users:
        decrypted_users.append({
            "person_id": user["person_id"],
            "first_name": decrypt(user["first_name"]),
            "last_name": decrypt(user["last_name"]),
            "address": decrypt(user["address"]),
            "street_number": decrypt(user["street_number"]),
            "password": user["password"],
            "enabled": user["enabled"]
        })
    return decrypted_users


def update_user(person_id, updates):
    """Opdaterer en bruger. Nye værdier krypteres/hashes før de gemmes."""
    updates.pop("person_id", None)
    users = _load_db()
    # Felter der skal krypteres
    encrypt_fields = ["first_name", "last_name", "address", "street_number"]
    for user in users:
        if user["person_id"] == person_id:
            for key, value in updates.items():
                if key in user:
                    if key == "password":
                        user[key] = hash_password(value)
                    elif key in encrypt_fields:
                        user[key] = encrypt(value)
                    else:
                        user[key] = value
            _save_db(users)
            return get_user(person_id)
    return None


def delete_user(person_id):
    """Sletter en bruger fra JSON-filen."""
    users = _load_db()
    new_users = [u for u in users if u["person_id"] != person_id]
    if len(new_users) < len(users):
        _save_db(new_users)
        return True
    return False