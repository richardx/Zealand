import unittest
import sys
import os
import json
from flat_file_db import (
    create_user, get_user, get_all_users, update_user, delete_user,
    _save_db, DB_FILE, KEY_FILE,
    encrypt, decrypt, hash_password, verify_password
)

# Terminal farver
YELLOW = "\033[93m"
RESET = "\033[0m"


def note(msg):
    """Printer en farvet note på egen linje under testen."""
    sys.stderr.write(f"\n      {YELLOW}✓ [FORVENTET] {msg}{RESET}\n\n")


class TestCRUD(unittest.TestCase):

    def setUp(self):
        _save_db([])

    def tearDown(self):
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)

    # --- CREATE ---

    # Risiko: Brugere kan ikke oprettes i systemet.
    def test_create_user(self):
        # Given: En tom database
        # When: En bruger oprettes
        user = create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
        # Then: Brugeren returneres med person_id
        self.assertEqual(user["person_id"], 1)

    # Risiko: Tomme felter accepteres uden validering.
    def test_create_user_with_empty_fields(self):
        # Given: En tom database
        # When: En bruger oprettes med tomme strenge
        user = create_user("", "", "", "", "")
        # Then: Brugeren oprettes alligevel
        self.assertEqual(user["person_id"], 1)
        note("Tomme felter accepteres - ingen validering")

    # --- READ ---

    # Risiko: Brugere kan ikke hentes fra databasen.
    def test_read_user(self):
        # Given: En database med én bruger
        create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
        # When: Brugeren hentes
        user = get_user(1)
        # Then: Dekrypteret data returneres
        self.assertEqual(user["first_name"], "Anders")

    # Risiko: Systemet crasher ved opslag på id der ikke findes.
    def test_read_user_not_found(self):
        # Given: En tom database
        # When: En bruger med ugyldigt id hentes
        user = get_user(999)
        # Then: None returneres
        self.assertIsNone(user)
        note("None returneret - id 999 findes ikke")

    # Risiko: Systemet crasher ved negativt id.
    def test_read_user_negative_id(self):
        # Given: En tom database
        # When: En bruger med negativt id hentes
        user = get_user(-1)
        # Then: None returneres
        self.assertIsNone(user)
        note("None returneret - negativt id ugyldigt")

    # --- UPDATE ---

    # Risiko: Brugerdata kan ikke opdateres.
    def test_update_user(self):
        # Given: En database med én bruger
        create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
        # When: Brugeren opdateres
        updated = update_user(1, {"first_name": "Maria"})
        # Then: Navnet er ændret
        self.assertEqual(updated["first_name"], "Maria")

    # Risiko: Systemet crasher ved opdatering af bruger der ikke findes.
    def test_update_user_not_found(self):
        # Given: En tom database
        # When: En bruger med ugyldigt id opdateres
        result = update_user(999, {"first_name": "Test"})
        # Then: None returneres
        self.assertIsNone(result)
        note("None returneret - bruger findes ikke")

    # Risiko: Ukendte felter kan tilføjes til brugerobjektet.
    def test_update_user_with_unknown_field(self):
        # Given: En database med én bruger
        create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
        # When: Et felt der ikke eksisterer forsøges opdateret
        updated = update_user(1, {"email": "anders@test.dk"})
        # Then: Det ukendte felt tilføjes IKKE
        self.assertNotIn("email", updated)
        note("Ukendt felt ignoreres")

    # --- DELETE ---

    # Risiko: Brugere kan ikke slettes fra databasen.
    def test_delete_user(self):
        # Given: En database med én bruger
        create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
        # When: Brugeren slettes
        result = delete_user(1)
        # Then: Brugeren er væk
        self.assertTrue(result)
        self.assertIsNone(get_user(1))

    # Risiko: Systemet rapporterer fejlagtigt at en bruger er slettet.
    def test_delete_user_not_found(self):
        # Given: En tom database
        # When: En bruger med ugyldigt id forsøges slettet
        result = delete_user(999)
        # Then: False returneres
        self.assertFalse(result)
        note("False returneret - bruger findes ikke")

    # Risiko: Sletning af én bruger påvirker andre brugere.
    def test_delete_user_does_not_remove_others(self):
        # Given: En database med to brugere
        create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
        create_user("Maria", "Nielsen", "Søndergade", "5", "password456")
        # When: Bruger 1 slettes
        delete_user(1)
        # Then: Bruger 2 eksisterer stadig
        self.assertIsNotNone(get_user(2))
        self.assertEqual(len(get_all_users()), 1)

    # --- KRYPTERING ---

    # Risiko: Persondata gemmes i klartekst i JSON-filen.
    def test_data_is_encrypted_in_file(self):
        # Given: En bruger oprettes
        create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
        # When: Vi læser rå data fra JSON-filen
        with open(DB_FILE, "r") as f:
            raw = json.load(f)
        # Then: Persondata er IKKE i klartekst
        self.assertNotEqual(raw[0]["first_name"], "Anders")
        self.assertNotEqual(raw[0]["last_name"], "Jensen")
        self.assertNotEqual(raw[0]["address"], "Hovedgaden")

    # Risiko: Krypteret data kan ikke dekrypteres korrekt.
    def test_data_is_decrypted_on_read(self):
        # Given: En bruger oprettes med krypteret data
        create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
        # When: Brugeren hentes
        user = get_user(1)
        # Then: Data er dekrypteret
        self.assertEqual(user["first_name"], "Anders")
        self.assertEqual(user["address"], "Hovedgaden")

    # Risiko: Kryptering/dekryptering fungerer ikke korrekt.
    def test_encrypt_decrypt_roundtrip(self):
        # Given: En klartekst
        original = "Hemmelig besked"
        # When: Teksten krypteres og dekrypteres
        encrypted = encrypt(original)
        decrypted = decrypt(encrypted)
        # Then: Resultatet er det samme som originalen
        self.assertEqual(decrypted, original)
        self.assertNotEqual(encrypted, original)

    # --- HASHING ---

    # Risiko: Passwords gemmes i klartekst.
    def test_password_is_hashed_in_file(self):
        # Given: En bruger oprettes med password "hemmelig123"
        create_user("Anders", "Jensen", "Hovedgaden", "12A", "hemmelig123")
        # When: Vi læser rå data fra JSON-filen
        with open(DB_FILE, "r") as f:
            raw = json.load(f)
        # Then: Password er IKKE i klartekst
        self.assertNotEqual(raw[0]["password"], "hemmelig123")

    # Risiko: Korrekte passwords afvises.
    def test_verify_password_correct(self):
        # Given: Et hashet password
        hashed = hash_password("hemmelig123")
        # When: Det korrekte password verificeres
        result = verify_password("hemmelig123", hashed)
        # Then: Verificeringen er True
        self.assertTrue(result)

    # Risiko: Forkerte passwords accepteres.
    def test_verify_password_wrong(self):
        # Given: Et hashet password
        hashed = hash_password("hemmelig123")
        # When: Et forkert password verificeres
        result = verify_password("forkert", hashed)
        # Then: Verificeringen er False
        self.assertFalse(result)
        note("Forkert password afvist korrekt")


if __name__ == "__main__":
    unittest.main()