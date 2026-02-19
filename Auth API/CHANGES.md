# Auth API — Ændringslog

Dette dokument forklarer hvad der er bygget, hvorfor det er bygget sådan,
og hvordan man bruger systemet.

---

## Trin 1 — Grundstruktur

### Filer oprettet

| Fil | Formål |
|-----|--------|
| `models.py` | Definerer `User`-modellen og `Role`-enum som bruges i hele systemet |
| `environment_loader.py` | Indlæser secrets sikkert fra `.env` (test) eller OS-miljøvariabler (prod) |
| `.env` | Test-secrets — må gerne ligge i git da det kun er til udvikling |
| `requirements.txt` | Alle Python-pakker systemet afhænger af |

---

### models.py

Definerer de to centrale datatyper:

**`Role` (enum)**
```
user  → almindelig bruger
admin → administrator med udvidede rettigheder
```

**`User` (Pydantic BaseModel)**

| Felt | Type | Beskrivelse |
|------|------|-------------|
| `username` | str | Bruges som unik nøgle (skal være email-format) |
| `password` | str | Gemmes altid som hash — aldrig i klartekst |
| `first_name` | str | Gemmes altid krypteret |
| `last_name` | str | Gemmes altid krypteret |
| `active` | bool | Om kontoen er aktiv (default: True) |
| `roles` | List[Role] | En bruger kan have flere roller |

`toDict()` bruges til at serialisere brugeren til JSON når den gemmes i databasen.

---

### environment_loader.py

Håndterer to miljøer:

**Testmiljø (lokalt):**
- `APP_ENV` er IKKE sat
- Indlæser automatisk fra `Auth API/.env`
- Printer en advarsel så man ved man kører med test-secrets

**Produktionsmiljø:**
- `APP_ENV` er sat (f.eks. `APP_ENV=production`)
- Indlæser HASH_KEY og ENCRYPTION_KEY direkte fra OS-miljøvariablerne
- `.env`-filen bruges IKKE

Returnerer: `(secret: bytes, fernet: Fernet)` som bruges i `auth_service.py`.

**Hvorfor denne opdeling?**
- Test-secrets kan ligge i git så hele teamet kan køre tests uden ekstra setup
- Prod-secrets sættes på serveren via miljøvariabler og er aldrig i kildekoden

---

### .env (test-secrets)

```
ENVIRONMENT_NAME=test
HASH_KEY=test_hemmeligt_hmac_noegle_til_udvikling_ikke_til_produktion
ENCRYPTION_KEY=qI_o7EhqL5ahYERyp3aMRmwwsj0Tq9Qk8iZHyWDx0Vk=
```

- `HASH_KEY` → bruges som nøgle i HMAC-hashing af passwords
- `ENCRYPTION_KEY` → en gyldig Fernet-nøgle til AES-kryptering af persondata

Denne fil MÅ ligge i git — den indeholder kun test-data.
En eventuel `.env.prod` MÅ ALDRIG ligge i git (ignoreres af rod-.gitignore).

---

### requirements.txt

| Pakke | Bruges til |
|-------|-----------|
| `fastapi` | REST API framework |
| `uvicorn[standard]` | ASGI-server til at køre FastAPI |
| `cryptography` | Fernet AES-kryptering |
| `python-dotenv` | Indlæsning af `.env`-filer |
| `PyJWT` | Generering og validering af JWT-tokens |
| `pytest` | Unit-tests |
| `httpx` | HTTP-klient til at teste FastAPI endpoints i tests |

**Installation:**
```bash
cd "Auth API"
pip install -r requirements.txt
```
