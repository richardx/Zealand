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

---

## Trin 2 — auth_service.py

### Filer oprettet

| Fil | Formål |
|-----|--------|
| `auth_service.py` | Al sikkerhedslogik: hashing, kryptering og JWT-tokens |

---

### auth_service.py

En klasse med udelukkende statiske metoder. Secrets hentes automatisk fra
`environment_loader.py` ved opstart — de er aldrig skrevet direkte i koden.

#### Metoder

| Metode | Beskrivelse |
|--------|-------------|
| `hash_password(password)` | HMAC-SHA256 med tilfældigt salt → base64-string |
| `verify_password(password, stored_hash)` | Verificerer password mod gemt hash |
| `encrypt_data(plaintext)` | Krypterer tekst med Fernet (AES) |
| `decrypt_data(token)` | Dekrypterer Fernet-krypteret tekst |
| `get_bearer_token(user)` | Genererer JWT Bearer token (1 times levetid) |
| `verify_token(token)` | Validerer JWT, kaster HTTPException ved fejl |

---

### Sikkerhedsprincipper

#### HMAC-SHA256 vs. ren SHA-256

Den tidligere `flat_file_db.py` brugte ren SHA-256 uden salt og uden nøgle:
```python
hashlib.sha256(password.encode()).hexdigest()  # Usikkert
```

`auth_service.py` bruger HMAC-SHA256 med salt:
```python
hmac.new(secret_key, salt + password, hashlib.sha256).digest()  # Sikkert
```

**Forskellen:**

| | SHA-256 (ingen nøgle) | HMAC-SHA256 (med nøgle) |
|--|----------------------|------------------------|
| Nøgle | Ingen | Ja — `HASH_KEY` fra miljøvariabel |
| Angreb | Sårbar over for rainbow tables | Kræver kendskab til nøglen |
| Samme password → samme hash | Ja (problem) | Nej — salt sikrer unikhed |

---

#### Hvorfor salt?

Salt er 16 tilfældige bytes der genereres ved hvert kald til `hash_password`.
De gemmes sammen med hashet (foran) og bruges igen ved `verify_password`.

**Uden salt:** To brugere med password "abc123" får identiske hashes i databasen.
En angriber der ser databasen kan øjeblikkeligt se at de har samme password.

**Med salt:** Hvert hash er unikt, selv for identiske passwords:
```
password: "abc123"  →  hash 1: Ncqh88Zb9poV...
password: "abc123"  →  hash 2: 87eAAJ2iNtV1...
```

---

#### Timing-sikker sammenligning

`verify_password` bruger `hmac.compare_digest()` i stedet for `==`:

```python
# Usikkert — stopper ved første forskel (timing-angreb muligt):
return stored_digest == new_digest

# Sikkert — bruger altid samme tid uanset resultat:
return hmac.compare_digest(stored_digest, new_digest)
```

Et timing-angreb måler præcist hvor lang tid et afslag tager. Ved `==` stopper
sammenligningen ved første forskel, hvilket afslører hvor mange bytes der matcher.
`compare_digest` er designet til altid at tage samme tid.

---

#### JWT — hvad indeholder tokenet?

JWT (JSON Web Token) er en signeret streng i tre dele adskilt af punktummer:
`header.payload.signature`

Payload der genereres i `get_bearer_token`:

| Felt | Indhold | Formål |
|------|---------|--------|
| `sub` | brugernavn | Identificerer hvem tokenet tilhører |
| `roles` | `["admin"]` / `["user"]` | Bruges til adgangskontrol i endpoints |
| `exp` | tidspunkt + 1 time | Tokenet bliver ugyldigt efter 1 time |
| `iat` | nuværende tidspunkt | Hvornår tokenet blev udstedt |

Tokenet signeres med `HASH_KEY` via algoritmen `HS256`. Det betyder at
serveren kan verificere at tokenet ikke er blevet ændret, uden at gemme
det i en database.

---

## Trin 3 — flat_file_loader.py, user_service.py og tests

### Filer oprettet

| Fil | Formål |
|-----|--------|
| `Auth API/flat_file_loader.py` | Gemmer og indlæser bruger-databasen som JSON |
| `Auth API/user_service.py` | Al forretningslogik: opret, login, aktiver, skift password |
| `Test/test_auth.py` | 21 unit-tests der dækker alle metoder |

---

### flat_file_loader.py

Simpel klasse med to metoder:
- `load()` → indlæser JSON-filen, returnerer tom dict hvis filen ikke findes
- `save(data)` → skriver dict til JSON-filen

Returnerer altid en dict, aldrig `None` — det gør `user_service.py` mere robust.

---

### user_service.py

Holder databasen i hukommelsen (`_user_db`) og synkroniserer til fil ved hver ændring.

#### Metoder og adgangsregler

| Metode | Hvem har adgang | Beskrivelse |
|--------|----------------|-------------|
| `register_user(...)` | Alle | Username skal være email-format (noget@noget) |
| `get_bearer_token(...)` | Alle | Returnerer JWT-token hvis credentials er korrekte |
| `deactivate_user(token, username)` | Admin (alle) / User (kun sig selv) | Deaktiverede brugere kan ikke deaktivere andre |
| `activate_user(token, username)` | Kun admin | Reaktiverer en deaktiveret konto |
| `change_password(token, gammelt, nyt)` | Den bruger der ejer tokenet | Verificerer gammelt password inden skift |

#### Email-validering

Valideringen tjekker at:
1. Der er præcis ét `@`-tegn
2. Der er noget *før* `@` (lokal del)
3. Der er noget *efter* `@` (domæne del)

Dette er en bevidst enkel validering — den accepterer `a@b` som gyldig.

#### Standard admin-bruger

Hvis databasefilen ikke eksisterer oprettes automatisk:
```
username:    admin
password:    admin  (gemt som HMAC-hash)
first_name:  admin_first_name  (gemt krypteret)
last_name:   admin_last_name   (gemt krypteret)
active:      True
roles:       [admin]
```

---

### Test-strategi (Test/test_auth.py)

**21 tests fordelt på 6 kategorier:**

| Kategori | Antal tests | Hvad testes |
|----------|-------------|-------------|
| Database-opstart | 2 | Standard admin oprettes / eksisterende DB indlæses |
| `register_user` | 3 | Oprettelse, email-validering (5 cases), duplikat |
| `get_bearer_token` | 3 | Korrekte credentials, forkert password, ukendt bruger |
| `deactivate_user` | 4 | Admin, sig selv, anden bruger, deaktiveret admin |
| `activate_user` | 2 | Admin kan, ikke-admin kan ikke |
| `change_password` | 3 | Korrekt, forkert gammelt password, udløbet token |

**Testopbygning:**
- Hvert test følger **Given-When-Then**-mønsteret
- Hvert test har en **Risiko**-kommentar der beskriver hvad der går galt hvis testen fejler
- En `autouse`-fixture sletter testdatabasen før og efter **hvert enkelt test**
- Testdatabasen hedder `db_test_user_flat_file.json` og ignoreres af `.gitignore`

**Kørsel:**
```bash
# Fra Zealand/-roden:
python -m pytest Test/test_auth.py -v
```

---

## Trin 4 — auth_rest_api_models.py, auth_rest_api.py og main.py

### Filer oprettet

| Fil | Formål |
|-----|--------|
| `auth_rest_api_models.py` | Pydantic-modeller til request bodies |
| `auth_rest_api.py` | FastAPI-klasse med alle endpoints |
| `main.py` | Entry point — starter serveren |

---

### Start serveren

```bash
cd "Auth API"
uvicorn main:app --reload
```

Åbn derefter **http://127.0.0.1:8000/docs** i din browser.

> **Bemærk:** `main.py` sætter automatisk arbejdsmappen til `Auth API/`
> så databasefilen `db_user_flat_file.json` oprettes der.

---

### Endpoints — oversigt

| Metode | URL | Token krævet | Beskrivelse |
|--------|-----|:------------:|-------------|
| POST | `/get_bearer_token` | Nej | Log ind og få JWT token |
| POST | `/register_user` | Nej | Opret ny bruger |
| POST | `/deactivate_user` | Ja | Deaktiver bruger |
| POST | `/activate_user` | Ja (admin) | Reaktiver bruger |
| POST | `/change_password` | Ja | Skift eget password |

Token sendes som HTTP-header: `token: Bearer eyJ...`

---

### Sådan tester du hvert endpoint i Swagger UI

Åbn **http://127.0.0.1:8000/docs** efter serveren er startet.

---

#### 1. Få et token — `POST /get_bearer_token`

Klik **Try it out** og send:
```json
{
  "username": "admin",
  "password": "admin"
}
```
Kopiér værdien af `token` fra svaret — du skal bruge den til de næste endpoints.
Token ser sådan ud: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

---

#### 2. Registrer ny bruger — `POST /register_user`

```json
{
  "username": "ny@test.dk",
  "password": "hemmelig123",
  "first_name": "Ny",
  "last_name": "Bruger",
  "roles": ["user"]
}
```

---

#### 3. Deaktiver bruger — `POST /deactivate_user`

1. Klik **Try it out**
2. I feltet **token** (under Parameters) indsæt dit Bearer token: `Bearer eyJ...`
3. Send body:
```json
{
  "username": "ny@test.dk"
}
```

---

#### 4. Reaktiver bruger — `POST /activate_user`

Samme fremgangsmåde som deaktivering — kræver admin-token.

```json
{
  "username": "ny@test.dk"
}
```

---

#### 5. Skift password — `POST /change_password`

1. Indsæt dit Bearer token i **token**-feltet
2. Send body:
```json
{
  "old_password": "admin",
  "new_password": "nyt_password123"
}
```

Efter dette skal du hente et nyt token med det nye password.

---

### Anbefalet testrækkefølge

```
1. POST /get_bearer_token      → log ind som admin, kopiér token
2. POST /register_user         → opret en testbruger
3. POST /get_bearer_token      → log ind som testbruger, kopiér token
4. POST /deactivate_user       → deaktiver testbruger (med admin-token)
5. POST /activate_user         → reaktiver testbruger (med admin-token)
6. POST /change_password       → skift password på testbruger (med testbruger-token)
7. POST /get_bearer_token      → verificér nyt password virker
```

---

## Trin 5 — Kravgennemgang og komplet systemoversigt

### Kravopfyldelse

| # | Krav | Status | Test |
|---|------|:------:|------|
| 1 | Standard admin oprettes hvis ingen DB | ✅ | `test_ingen_database_opretter_standard_admin` |
| 2 | Security token via admin-bruger | ✅ | `test_krav2_token_via_standard_admin` |
| 3 | Skift password på admin | ✅ | `test_krav3_change_password_admin` |
| 4 | Registrer nye accounts | ✅ | `test_register_user` |
| 5 | Deaktiver account med sig selv | ✅ | `test_deactivate_user_som_sig_selv` |
| 6 | Reaktiver account kun med admin | ✅ | `test_activate_user_som_admin` + `test_activate_user_som_ikke_admin` |
| 7 | Test-secrets i git, prod-secrets i env vars | ✅ | `test_krav7_secrets_indlæses_fra_env_fil` |
| 8 | Alle endpoints testbare via /docs | ✅ | `test_krav8_alle_endpoints_via_rest_api` |

**Samlet: 25 auth-tests, alle består.**

---

### Komplet mappestruktur

```
Zealand/
├── .gitignore                        ← ignorerer __pycache__, secret.key, db-filer, .env.prod
├── README.md
│
├── Auth API/                         ← Authorization REST API (dette system)
│   ├── .env                          ← test-secrets (må ligge i git)
│   ├── models.py                     ← User-model og Role-enum
│   ├── environment_loader.py         ← indlæser secrets fra .env eller OS env vars
│   ├── auth_service.py               ← hashing, kryptering, JWT-tokens
│   ├── flat_file_loader.py           ← læs/skriv JSON-database
│   ├── user_service.py               ← forretningslogik og adgangskontrol
│   ├── auth_rest_api_models.py       ← Pydantic request-modeller
│   ├── auth_rest_api.py              ← FastAPI endpoints
│   ├── main.py                       ← entry point
│   ├── requirements.txt              ← pakkeafhængigheder
│   └── CHANGES.md                    ← denne fil
│
├── Bruger API/                       ← Bruger CRUD API (tidligere system)
│   ├── main.py
│   ├── requirements.txt
│   └── SETUP.md
│
├── Kryptering/
│   └── flat_file_db.py               ← kryptering og database til Bruger API
│
└── Test/                             ← alle tests samlet
    ├── test_auth.py                  ← 25 tests for Auth API
    ├── test_crud.py                  ← 17 tests for Bruger API / kryptering
    └── test_login.py                 ← 8 tests for login-validering
```

---

### Start Auth API-serveren

```bash
cd "Auth API"
pip install -r requirements.txt   # første gang
uvicorn main:app --reload
```

Åbn **http://127.0.0.1:8000/docs** i din browser.

---

### Kør alle tests

```bash
# Fra Zealand/-roden — kører ALLE 50 tests på én gang:
python -m pytest Test/ -v

# Kun auth-tests:
python -m pytest Test/test_auth.py -v
```

---

### Prod-secrets — sådan sætter du dem op

I testmiljø bruges `.env`-filen automatisk. I produktion skal du sætte
disse to miljøvariabler på serveren **inden** du starter serveren:

```bash
export APP_ENV=production
export HASH_KEY=din_hemmelige_hmac_nøgle_her
export ENCRYPTION_KEY=din_gyldige_fernet_nøgle_her
```

Generer en ny Fernet-nøgle med:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

| Miljøvariabel | Beskrivelse |
|---------------|-------------|
| `APP_ENV` | Sæt til hvad som helst (f.eks. `production`) for at deaktivere .env-indlæsning |
| `HASH_KEY` | Hemmelig nøgle til HMAC-SHA256 password-hashing |
| `ENCRYPTION_KEY` | Fernet-nøgle (base64, 32 bytes) til AES-kryptering af persondata |

> **Vigtigt:** Brug ALDRIG test-secrets fra `.env` i produktion.
> Generer nye nøgler og sæt dem som OS-miljøvariabler.
