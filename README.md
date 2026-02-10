# Zealand

### Hvad jeg forventer at lære på Softwaresikkerhed
Jeg forventer at lære, hvordan programkvalitet, fejlhåndtering og sikkerhedsdesign, herunder security by design og privacy by design, bruges til at identificere, forebygge og vurdere sårbarheder i programkode og softwarearkitektur samt arbejde med risikovurdering og grundlæggende kryptering.


### Billede af Python test
![alt text](image.png)


### Billede hvor jeg har tilføjet 3 tests.
![alt text](image-1.png)

# Testteknikker i IT-sikkerhed

## Valgt emne: Login-system

Et login-system hvor brugeren indtaster brugernavn og password. Systemet skal håndtere validering, fejlede forsøg og kontolåsning.

---

## Ækvivalensklasser

| Klasse | Eksempel |
|--------|----------|
| Gyldigt brugernavn | `lars@firma.dk` |
| Ugyldigt brugernavn (tomt) | `` |
| Ugyldigt brugernavn (findes ikke) | `ikkeeksisterende@firma.dk` |
| Gyldigt password | `Hemlig123!` |
| Ugyldigt password (forkert) | `forkertpassword` |

---

## Grænseværditest

Kontoen låses efter 3 fejlede loginforsøg:

| Antal fejlede forsøg | Forventet resultat |
|---------------------|-------------------|
| 2 | Adgang nægtet, konto åben |
| 3 | Adgang nægtet, konto låses |
| 4 | Adgang nægtet, konto forbliver låst |

---

## CRUD(L)

| Operation | Test |
|-----------|------|
| **Create** | Opret ny bruger med brugernavn og password |
| **Read** | Hent brugeroplysninger (uden at vise password) |
| **Update** | Skift password for en bruger |
| **Delete** | Slet en bruger fra systemet |
| **List** | Vis alle brugere (kun for admin) |

---

## Cycle Process Test

- Bruger logger ind og ud 100 gange i træk
- Verificér at session håndteres korrekt hver gang
- Ingen memory leaks eller akkumulerede fejl

---

## Test Pyramiden

| Niveau | Eksempel |
|--------|----------|
| Unit test | Validér at password-hashing virker |
| Integration test | Test login mod database |
| E2E test | Fuld brugerrejse: login → se data → logout |

---

## Decision Table Test

| Brugernavn findes | Password korrekt | Konto låst | Resultat |
|-------------------|-----------------|-----------|----------|
| Ja | Ja | Nej | Adgang |
| Ja | Ja | Ja | Afvist |
| Ja | Nej | Nej | Afvist + tæl forsøg |
| Nej | – | – | Afvist |

---

## Security Gates

| Testteknik | Security Gate |
|------------|---------------|
| Ækvivalensklasser | Code/Dev gate |
| Grænseværditest | Code/Dev gate |
| CRUD(L) | Integration gate |
| Cycle process test | Release candidate gate |
| Test pyramiden | Alle gates |
| Decision table test | Code/Dev gate |



## PyTest (Leg)

Data-dreven unit test der kombinerer Decision Table Test og Grænseværditest.

Testen bruger `@pytest.mark.parametrize` til at køre samme testfunktion med forskellige input-data. Hver række i parametrene repræsenterer et testscenarie fra vores Decision Table (kombinationer af brugernavn, password, kontostatus) og Grænseværditest (antal fejlede loginforsøg ved grænsen på 3).

Se filen: [test_login.py](test_login.py)

**Test resultat:**

![Test resultat](image-2.png)


# Kryptering

## Hvorfor er det smart at bruge en flat file database?

En flat file database er en simpel måde at gemme data på, hvor alt ligger i én fil (f.eks. JSON). Det er smart fordi:

- **Simpelt setup** – ingen installation af databasesoftware som MySQL eller PostgreSQL. Man skal bare have en JSON-fil.
- **Let at forstå** – dataen er menneskelæsbar. Man kan åbne filen og se alt dataen direkte.
- **Portabelt** – hele databasen er én fil, som nemt kan kopieres, deles eller flyttes.
- **Ingen afhængigheder** – kræver ikke en databaseserver der kører i baggrunden.
- **Godt til små projekter** – perfekt til prototyper, tests og mindre applikationer.

### Ulemper

- Skalerer ikke godt til store datamængder.
- Ingen avanceret søgning eller filtrering som SQL.
- Risiko for datatab hvis flere processer skriver til filen samtidig.

---

## Unit Tests

Testene er skrevet med Pythons `unittest` modul og tester alle CRUD-operationer (Create, Read, Update, Delete) samt edge cases.

### Test resultater

![alt text](image-3.png)
> – Screenshot af terminal output fra `python3 -m unittest test.py -v`

---

### Gode test navne

Alle tests er navngivet beskrivende, så man kan se hvad de tester:

| Test navn | Beskrivelse |
|---|---|
| `test_create_user` | Tester at en bruger kan oprettes |
| `test_create_user_with_empty_fields` | Tester oprettelse med tomme felter |
| `test_read_user` | Tester at en bruger kan hentes |
| `test_read_user_not_found` | Tester opslag med ugyldigt id |
| `test_read_user_negative_id` | Tester opslag med negativt id |
| `test_update_user` | Tester at en bruger kan opdateres |
| `test_update_user_not_found` | Tester opdatering af bruger der ikke findes |
| `test_update_user_with_unknown_field` | Tester opdatering med ukendt felt |
| `test_delete_user` | Tester at en bruger kan slettes |
| `test_delete_user_not_found` | Tester sletning af bruger der ikke findes |
| `test_delete_user_does_not_remove_others` | Tester at sletning ikke påvirker andre |

---

### Risikokommentarer

Hver test har en kort kommentar der beskriver risikoen hvis testen ikke består. Eksempler:

```python
# Risiko: Brugere kan ikke oprettes i systemet.
def test_create_user(self):

# Risiko: Systemet crasher ved opslag på id der ikke findes.
def test_read_user_not_found(self):

# Risiko: Ukendte felter kan tilføjes til brugerobjektet.
def test_update_user_with_unknown_field(self):
```

> **[INDSÆT SCREENSHOT HER]** – Screenshot af koden i `test.py` der viser risikokommentarerne over hver test.

---

### Given, When, Then

Alle test cases følger Given-When-Then mønsteret som kommentarer:

```python
def test_create_user(self):
    # Given: En tom database
    # When: En bruger oprettes
    user = create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
    # Then: Brugeren returneres med korrekte data
    self.assertEqual(user["first_name"], "Anders")
```

> **[INDSÆT SCREENSHOT HER]** – Screenshot af koden i `test.py` der viser Given/When/Then kommentarerne.