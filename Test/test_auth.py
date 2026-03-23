import pytest
import os
import sys
import json
import datetime
import jwt
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Peg Python mod Auth API-mappen så imports virker
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Auth API"))

from models import User, Role
from auth_service import Auth_service
from user_service import User_service
from auth_rest_api import Auth_rest_api
from environment_loader import Environment_loader

# Separat testdatabase — oprettes og slettes af fixture
TEST_DB = "db_test_user_flat_file.json"


# --- Hjælpefunktion til at oprette testdata ---

def opret_test_database(filename: str):
    """Opretter en testdatabase med kendte brugere."""
    data = {
        "admin_test": User(
            username="admin_test",
            password=Auth_service.hash_password("admin_password"),
            first_name=Auth_service.encrypt_data("Admin"),
            last_name=Auth_service.encrypt_data("Testersen"),
            active=True,
            roles=[Role.admin],
        ).toDict(),
        "bruger@test.dk": User(
            username="bruger@test.dk",
            password=Auth_service.hash_password("bruger_password"),
            first_name=Auth_service.encrypt_data("Bruger"),
            last_name=Auth_service.encrypt_data("Testersen"),
            active=True,
            roles=[Role.user],
        ).toDict(),
        "inaktiv@test.dk": User(
            username="inaktiv@test.dk",
            password=Auth_service.hash_password("inaktiv_password"),
            first_name=Auth_service.encrypt_data("Inaktiv"),
            last_name=Auth_service.encrypt_data("Testersen"),
            active=False,
            roles=[Role.user],
        ).toDict(),
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# --- Fixture: ryd op før og efter hver test ---

@pytest.fixture(autouse=True)
def cleanup():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


# ================================================================
# TESTS: Database-opstart
# ================================================================

# Risiko: Systemet kræver manuel oprettelse af admin — blokkerer første brug.
def test_ingen_database_opretter_standard_admin():
    # Given: Ingen databasefil findes
    # When: User_service startes
    service = User_service(TEST_DB)

    # Then: Én admin-bruger er oprettet med username "admin"
    assert len(service._user_db) == 1
    bruger = service._user_db["admin"]
    assert bruger.username == "admin"
    assert Auth_service.verify_password("admin", bruger.password)
    assert Auth_service.decrypt_data(bruger.first_name) == "admin_first_name"
    assert Auth_service.decrypt_data(bruger.last_name) == "admin_last_name"
    assert bruger.active is True
    assert Role.admin in bruger.roles


# Risiko: Eksisterende brugere overskrives ved genstart.
def test_eksisterende_database_indlæses_korrekt():
    # Given: En database med kendte brugere
    opret_test_database(TEST_DB)

    # When: User_service startes
    service = User_service(TEST_DB)

    # Then: Alle brugere er indlæst korrekt
    assert len(service._user_db) == 3
    admin = service._user_db["admin_test"]
    assert admin.username == "admin_test"
    assert Auth_service.verify_password("admin_password", admin.password)
    assert Auth_service.decrypt_data(admin.first_name) == "Admin"


# ================================================================
# TESTS: register_user
# ================================================================

# Risiko: Nye brugere kan ikke oprettes i systemet.
def test_register_user():
    # Given: En eksisterende database
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    # When: En ny bruger registreres
    service.register_user("ny@test.dk", "password123", "Ny", "Bruger", [Role.user])

    # Then: Brugeren er i databasen med krypteret data og hashet password
    bruger = service._user_db["ny@test.dk"]
    assert bruger.username == "ny@test.dk"
    assert Auth_service.verify_password("password123", bruger.password)
    assert Auth_service.decrypt_data(bruger.first_name) == "Ny"
    assert Auth_service.decrypt_data(bruger.last_name) == "Bruger"
    assert bruger.active is True
    assert Role.user in bruger.roles


# Risiko: Ugyldige email-formater accepteres som brugernavn.
@pytest.mark.parametrize("email,fejl_forventet", [
    ("a@b", False),
    ("test@test.dk", False),
    ("ingen_snabel_a", True),
    ("@mangler_lokal", True),
    ("ab", True),
])
def test_register_user_email_validering(email, fejl_forventet):
    # Given: En eksisterende database
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    # When: Register forsøges med forskellig email-format
    fejl = None
    try:
        service.register_user(email, "pw", "Fornavn", "Efternavn", [Role.user])
    except HTTPException as e:
        fejl = e

    # Then: Fejl opstår kun for ugyldige formater
    if fejl_forventet:
        assert fejl is not None
        assert fejl.status_code == 400
        assert fejl.detail == "Ugyldigt email-format"
    else:
        assert fejl is None


# Risiko: To brugere kan registreres med samme brugernavn.
def test_register_user_brugernavn_taget():
    # Given: En database med en eksisterende bruger
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    # When: Der registreres med et allerede brugt brugernavn
    fejl = None
    try:
        service.register_user("bruger@test.dk", "nyt_password", "Ny", "Bruger", [Role.user])
    except HTTPException as e:
        fejl = e

    # Then: 400-fejl med klar besked
    assert fejl is not None
    assert fejl.status_code == 400
    assert fejl.detail == "Brugernavn er allerede taget"


# ================================================================
# TESTS: get_bearer_token
# ================================================================

# Risiko: Brugere kan ikke logge ind og hente tokens.
def test_get_bearer_token():
    # Given: En database med en admin-bruger
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    # When: Token hentes med korrekte credentials
    token = service.get_bearer_token("admin_test", "admin_password")
    payload = Auth_service.verify_token(token)

    # Then: Token er gyldigt og indeholder korrekt data
    assert payload["sub"] == "admin_test"
    assert "admin" in payload["roles"]
    assert payload["exp"] is not None
    assert payload["iat"] is not None


# Risiko: Forkerte passwords accepteres.
def test_get_bearer_token_forkert_password():
    # Given: En eksisterende bruger
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    # When: Token forsøges hentet med forkert password
    fejl = None
    try:
        service.get_bearer_token("bruger@test.dk", "FORKERT")
    except HTTPException as e:
        fejl = e

    # Then: 401-fejl returneres
    assert fejl is not None
    assert fejl.status_code == 401


# Risiko: Ikke-eksisterende brugere kan få tokens.
def test_get_bearer_token_bruger_ikke_fundet():
    # Given: En database uden den søgte bruger
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    # When: Token forsøges hentet for ikke-eksisterende bruger
    fejl = None
    try:
        service.get_bearer_token("findes_ikke@test.dk", "password")
    except HTTPException as e:
        fejl = e

    # Then: 401-fejl — vi afslører ikke om brugeren eksisterer
    assert fejl is not None
    assert fejl.status_code == 401


# ================================================================
# TESTS: deactivate_user
# ================================================================

# Risiko: Admin kan ikke deaktivere andre brugere.
def test_deactivate_user_som_admin():
    # Given: En aktiv bruger og en admin
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)
    assert service._user_db["bruger@test.dk"].active is True

    # When: Admin deaktiverer brugeren
    token = service.get_bearer_token("admin_test", "admin_password")
    service.deactivate_user(token, "bruger@test.dk")

    # Then: Brugeren er deaktiveret
    assert service._user_db["bruger@test.dk"].active is False


# Risiko: En bruger kan ikke deaktivere sig selv.
def test_deactivate_user_som_sig_selv():
    # Given: En aktiv bruger
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)
    assert service._user_db["bruger@test.dk"].active is True

    # When: Brugeren deaktiverer sin egen konto
    token = service.get_bearer_token("bruger@test.dk", "bruger_password")
    service.deactivate_user(token, "bruger@test.dk")

    # Then: Kontoen er deaktiveret
    assert service._user_db["bruger@test.dk"].active is False


# Risiko: En bruger kan deaktivere andre brugeres konti.
def test_deactivate_user_som_anden_bruger():
    # Given: To aktive brugere uden admin-rettigheder
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)
    service.register_user("anden@test.dk", "password", "Anden", "Bruger", [Role.user])

    # When: En bruger forsøger at deaktivere en anden bruger
    token = service.get_bearer_token("bruger@test.dk", "bruger_password")
    fejl = None
    try:
        service.deactivate_user(token, "anden@test.dk")
    except HTTPException as e:
        fejl = e

    # Then: 403-fejl og den anden bruger er stadig aktiv
    assert fejl is not None
    assert fejl.status_code == 403
    assert service._user_db["anden@test.dk"].active is True


# Risiko: En deaktiveret admin kan stadig deaktivere brugere.
def test_deaktiveret_admin_kan_ikke_deaktivere():
    # Given: Admin deaktiverer sin egen konto
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)
    token = service.get_bearer_token("admin_test", "admin_password")
    service.deactivate_user(token, "admin_test")
    assert service._user_db["admin_test"].active is False

    # When: Den deaktiverede admin forsøger at deaktivere en anden bruger
    fejl = None
    try:
        service.deactivate_user(token, "bruger@test.dk")
    except HTTPException as e:
        fejl = e

    # Then: 403-fejl — deaktiverede brugere har ingen rettigheder
    assert fejl is not None
    assert fejl.status_code == 403
    assert service._user_db["bruger@test.dk"].active is True


# ================================================================
# TESTS: activate_user
# ================================================================

# Risiko: Admin kan ikke reaktivere deaktiverede brugere.
def test_activate_user_som_admin():
    # Given: En inaktiv bruger
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)
    assert service._user_db["inaktiv@test.dk"].active is False

    # When: Admin reaktiverer brugeren
    token = service.get_bearer_token("admin_test", "admin_password")
    service.activate_user(token, "inaktiv@test.dk")

    # Then: Brugeren er aktiv igen
    assert service._user_db["inaktiv@test.dk"].active is True


# Risiko: Almindelige brugere kan reaktivere konti.
def test_activate_user_som_ikke_admin():
    # Given: En inaktiv bruger og en aktiv ikke-admin
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    # When: En ikke-admin forsøger at reaktivere en konto
    token = service.get_bearer_token("bruger@test.dk", "bruger_password")
    fejl = None
    try:
        service.activate_user(token, "inaktiv@test.dk")
    except HTTPException as e:
        fejl = e

    # Then: 403-fejl og kontoen er stadig inaktiv
    assert fejl is not None
    assert fejl.status_code == 403
    assert service._user_db["inaktiv@test.dk"].active is False


# ================================================================
# TESTS: change_password
# ================================================================

# Risiko: Brugere kan ikke skifte password.
def test_change_password():
    # Given: En bruger med kendt password
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    # When: Brugeren skifter password
    token = service.get_bearer_token("bruger@test.dk", "bruger_password")
    service.change_password(token, "bruger_password", "nyt_password123")

    # Then: Det nye password virker, det gamle gør ikke
    assert Auth_service.verify_password("nyt_password123", service._user_db["bruger@test.dk"].password)
    assert not Auth_service.verify_password("bruger_password", service._user_db["bruger@test.dk"].password)


# Risiko: Password kan skiftes uden at kende det nuværende.
def test_change_password_forkert_gammelt_password():
    # Given: En bruger med kendt password
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    # When: Passwordskift forsøges med forkert gammelt password
    token = service.get_bearer_token("bruger@test.dk", "bruger_password")
    fejl = None
    try:
        service.change_password(token, "FORKERT_PASSWORD", "nyt_password123")
    except HTTPException as e:
        fejl = e

    # Then: 401-fejl og password er uændret
    assert fejl is not None
    assert fejl.status_code == 401
    assert Auth_service.verify_password("bruger_password", service._user_db["bruger@test.dk"].password)


# Risiko: Et udløbet token accepteres ved passwordskift.
def test_change_password_udløbet_token():
    # Given: Et token der allerede er udløbet
    opret_test_database(TEST_DB)
    service = User_service(TEST_DB)

    payload = {
        "sub": "bruger@test.dk",
        "roles": ["user"],
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=0),
        "iat": datetime.datetime.now(datetime.UTC),
    }
    udløbet_token = f"Bearer {jwt.encode(payload, Auth_service._secret, algorithm=Auth_service._algorithm)}"

    # When: Passwordskift forsøges med udløbet token
    fejl = None
    try:
        service.change_password(udløbet_token, "bruger_password", "nyt")
    except HTTPException as e:
        fejl = e

    # Then: 401-fejl pga. udløbet token
    assert fejl is not None
    assert fejl.status_code == 401
    assert fejl.detail == "Token udløbet"


# ================================================================
# TESTS: Direkte kravdækning (krav 2, 3, 7, 8)
# ================================================================

# Krav 2: Man kan få en security_token via den auto-oprettede admin-bruger.
def test_krav2_token_via_standard_admin():
    # Given: Ingen database → standard admin oprettes automatisk
    service = User_service(TEST_DB)
    assert service._user_db["admin"].username == "admin"

    # When: Token hentes med default-credentials (admin / admin)
    token = service.get_bearer_token("admin", "admin")
    payload = Auth_service.verify_token(token)

    # Then: Gyldigt token med admin-rolle
    assert payload["sub"] == "admin"
    assert "admin" in payload["roles"]
    assert token.startswith("Bearer ")


# Krav 3: Man kan ændre password på admin-brugeren.
def test_krav3_change_password_admin():
    # Given: Standard admin oprettet automatisk
    service = User_service(TEST_DB)
    token = service.get_bearer_token("admin", "admin")

    # When: Admin skifter sit password
    service.change_password(token, "admin", "nyt_admin_password")

    # Then: Nyt password virker og gammelt gør ikke
    assert Auth_service.verify_password("nyt_admin_password", service._user_db["admin"].password)
    assert not Auth_service.verify_password("admin", service._user_db["admin"].password)

    # Og man kan stadig logge ind med det nye password
    nyt_token = service.get_bearer_token("admin", "nyt_admin_password")
    assert nyt_token.startswith("Bearer ")


# Krav 7: Test-secrets indlæses fra .env-filen (ikke hardcoded).
def test_krav7_secrets_indlæses_fra_env_fil():
    # Given: APP_ENV er ikke sat → testmiljø bruger .env-filen
    # When: Auth_service har allerede indlæst secrets ved import
    # Then: Secrets er tilgængelige og ikke tomme
    assert Auth_service._secret is not None
    assert len(Auth_service._secret) > 0
    assert Auth_service._fernet is not None

    # Og secrets kan bruges til at kryptere/dekryptere og hashe
    krypteret = Auth_service.encrypt_data("test")
    assert Auth_service.decrypt_data(krypteret) == "test"

    hashed = Auth_service.hash_password("test")
    assert Auth_service.verify_password("test", hashed)


# Krav 8: Alle endpoints er tilgængelige og virker via REST API-laget.
def test_krav8_alle_endpoints_via_rest_api():
    # Given: API oprettet — simulerer hvad /docs-brugeren oplever
    api = Auth_rest_api(TEST_DB)
    client = TestClient(api.app)

    # 1. Hent token som standard admin (krav 2)
    r = client.post("/get_bearer_token", json={"username": "admin", "password": "admin"})
    assert r.status_code == 200, f"get_bearer_token fejlede: {r.text}"
    token = r.json()["token"]
    assert token.startswith("Bearer ")

    # 2. Registrer ny bruger (krav 4)
    r = client.post("/register_user", json={
        "username": "rest@test.dk", "password": "pw123",
        "first_name": "Rest", "last_name": "Bruger", "roles": ["user"]
    })
    assert r.status_code == 200, f"register_user fejlede: {r.text}"

    # 3. Deaktiver brugeren (krav 5 — admin deaktiverer)
    r = client.post("/deactivate_user",
                    json={"username": "rest@test.dk"},
                    headers={"token": token})
    assert r.status_code == 200, f"deactivate_user fejlede: {r.text}"

    # 4. Reaktiver brugeren som admin (krav 6)
    r = client.post("/activate_user",
                    json={"username": "rest@test.dk"},
                    headers={"token": token})
    assert r.status_code == 200, f"activate_user fejlede: {r.text}"

    # 5. Skift password på admin (krav 3)
    r = client.post("/change_password",
                    json={"old_password": "admin", "new_password": "nyt123"},
                    headers={"token": token})
    assert r.status_code == 200, f"change_password fejlede: {r.text}"

    # 6. Verificér nyt password virker
    r = client.post("/get_bearer_token", json={"username": "admin", "password": "nyt123"})
    assert r.status_code == 200, f"login med nyt password fejlede: {r.text}"
