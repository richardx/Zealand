import json
import os

DB_FILE = "flat_file_db.json"


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
    """Opretter en ny bruger i JSON-filen."""
    users = _load_db()
    user = {
        "person_id": _next_id(users),
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "street_number": street_number,
        "password": password,
        "enabled": enabled
    }
    users.append(user)
    _save_db(users)
    return user


def get_user(person_id):
    """Henter en bruger fra JSON-filen ud fra person_id."""
    for user in _load_db():
        if user["person_id"] == person_id:
            return user
    return None


def get_all_users():
    """Henter alle brugere fra JSON-filen."""
    return _load_db()


def update_user(person_id, updates):
    """Opdaterer en bruger i JSON-filen."""
    updates.pop("person_id", None)
    users = _load_db()
    for user in users:
        if user["person_id"] == person_id:
            for key, value in updates.items():
                if key in user:
                    user[key] = value
            _save_db(users)
            return user
    return None


def delete_user(person_id):
    """Sletter en bruger fra JSON-filen."""
    users = _load_db()
    new_users = [u for u in users if u["person_id"] != person_id]
    if len(new_users) < len(users):
        _save_db(new_users)
        return True
    return False