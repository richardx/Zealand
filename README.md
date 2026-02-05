# Zealand

### Hvad jeg forventer at lære på Softwaresikkerhed
Jeg forventer at lære, hvordan programkvalitet, fejlhåndtering og sikkerhedsdesign, herunder security by design og privacy by design, bruges til at identificere, forebygge og vurdere sårbarheder i programkode og softwarearkitektur samt arbejde med risikovurdering og grundlæggende kryptering.


### Billede af Python test
![alt text](image.png)


### Billede hvor jeg har tilføjet 3 tests.
![alt text](image-1.png)

# Testteknikker i IT-sikkerhed

## Valgt emne: Password-validering og authentication

---

## Ækvivalensklasser

Gruppering af input der opfører sig ens:

| Klasse | Beskrivelse | Eksempel |
|--------|-------------|----------|
| Gyldige passwords | 8-64 tegn, indeholder tal+bogstav+specialtegn | `Secure1!pass` |
| Ugyldige: for korte | Under 8 tegn | `Ab1!` |
| Ugyldige: for lange | Over 64 tegn | `Aaaa...65+ tegn` |
| Ugyldige: mangler specialtegn | Ingen specialtegn | `Password123` |
| Ugyldige: mangler tal | Ingen cifre | `Password!` |
| Ugyldige: mangler bogstav | Ingen bogstaver | `12345678!` |

---

## Grænseværditest

Test af grænser ved password-længde (minimum 8, maximum 64 tegn):

| Input | Antal tegn | Forventet resultat | Kommentar |
|-------|------------|-------------------|-----------|
| `Aa1!aaa` | 7 | Afvist | Lige under minimum |
| `Aa1!aaaa` | 8 | Godkendt | Lige på minimum |
| `Aa1!aaaaa` | 9 | Godkendt | Lige over minimum |
| `A*62 + 1!` | 64 | Godkendt | Lige på maximum |
| `A*63 + 1!` | 65 | Afvist | Lige over maximum |

---

## CRUD(L)

Test af grundlæggende dataoperationer for brugeradministration:

| Operation | Beskrivelse | Sikkerhedsaspekt |
|-----------|-------------|------------------|
| **Create** | Kan en admin oprette en ny bruger? | Valideres input? Hashes password korrekt? |
| **Read** | Kan man hente brugeroplysninger? | Returneres password-hash? (bør ikke!) |
| **Update** | Kan man opdatere en brugers rolle? | Tjekkes authorization? Logges ændringen? |
| **Delete** | Slettes brugeren korrekt? | Soft delete eller hard delete? Audit log? |
| **List** | Vises brugerlisten korrekt? | Pagination? Kan ikke-admins se listen? |

---

## Cycle Process Test

Test af gentagne processer over tid:

- Login → arbejd → logout → login igen (gentag 100+ gange)
- Verificér at sessions håndteres korrekt uden memory leaks
- Verificér at tokens refreshes korrekt over længere tid
- Test at failed login attempts nulstilles korrekt efter succesfuldt login
- Verificér at session timeout fungerer efter inaktivitet

---

## Test Pyramiden

Fordeling af tests fra bund til top:

```
        /\
       /  \     E2E: Fuld brugerrejse (login → handling → logout)
      /----\
     /      \   Integration: Login-flow mod database, API-kald
    /--------\
   /          \  Unit: Password-hashing, input-validering, token-generering
  --------------
```

| Niveau | Eksempler | Antal | Hastighed |
|--------|-----------|-------|-----------|
| Unit tests | Password-hashing, input-validering | Mange | Hurtig (ms) |
| Integration tests | Login mod database, session-oprettelse | Mellem | Medium (sek) |
| E2E tests | Komplet brugerrejse | Få | Langsom (min) |

---

## Decision Table Test

Login-system med forskellige kombinationer:

| Regel | Gyldigt brugernavn | Gyldigt password | Konto låst | MFA korrekt | Resultat |
|-------|-------------------|-----------------|-----------|-------------|----------|
| R1 | Ja | Ja | Nej | Ja | Adgang |
| R2 | Ja | Ja | Nej | Nej | Afvist + "Forkert MFA" |
| R3 | Ja | Ja | Ja | – | Afvist + "Konto låst" |
| R4 | Ja | Nej | Nej | – | Afvist + tæl forsøg op |
| R5 | Ja | Nej | Nej | – | (3. forsøg) Lås konto |
| R6 | Nej | – | – | – | Afvist + log hændelse |

---

## Security Gates placering

| Testteknik | Security Gate | Begrundelse |
|------------|---------------|-------------|
| Ækvivalensklasser | Code/Dev gate | Fanges i unit tests under udvikling |
| Grænseværditest | Code/Dev gate | Fanges i unit tests under udvikling |
| CRUD(L) | Integration gate | Tester samspil mellem komponenter |
| Decision table test | Code/Dev + Integration gate | Logik testes i unit, flows i integration |
| Cycle process test | Release candidate gate | Kræver produktionslignende miljø |
| Test pyramiden | Alle gates | Forskellige testniveauer i forskellige gates |