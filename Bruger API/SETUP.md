# Bruger API — Bruger REST API

Et simpelt REST API bygget med FastAPI og en krypteret flat-file database.

## Krav

- Python 3.10+
- Pip

## Installation

```bash
cd "Bruger API"
pip install -r requirements.txt
```

## Start serveren

```bash
uvicorn main:app --reload
```

Åbn derefter **http://127.0.0.1:8000/docs** i din browser for at teste API'et via Swagger UI.

## Endpoints

| Metode | URL | Beskrivelse |
|--------|-----|-------------|
| `POST` | `/users` | Opret bruger |
| `GET` | `/users` | List alle brugere |
| `GET` | `/users/{person_id}` | Hent én bruger |
| `PUT` | `/users/{person_id}` | Opdater bruger |
| `DELETE` | `/users/{person_id}` | Slet bruger |

## Bemærk

- Persondata (navn, adresse) krypteres automatisk med AES (Fernet) før det gemmes
- Passwords hashes med SHA-256 og kan ikke læses tilbage
- Data gemmes i `flat_file_db.json` og krypteringsnøglen i `secret.key` — disse filer oprettes automatisk første gang serveren startes
