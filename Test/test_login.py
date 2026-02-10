import pytest


def validate_login(username: str, password: str, account_locked: bool, failed_attempts: int) -> dict:
    """
    Simuleret login-validering.
    Returnerer dict med 'success', 'message' og 'failed_attempts'.
    """
    # Tjek om konto er låst
    if account_locked:
        return {"success": False, "message": "Konto låst", "failed_attempts": failed_attempts}
    
    # Tjek brugernavn
    if not username or username != "lars@firma.dk":
        return {"success": False, "message": "Ugyldigt brugernavn", "failed_attempts": failed_attempts + 1}
    
    # Tjek password
    if password != "Hemlig123!":
        new_attempts = failed_attempts + 1
        if new_attempts >= 3:
            return {"success": False, "message": "Konto låst", "failed_attempts": new_attempts}
        return {"success": False, "message": "Forkert password", "failed_attempts": new_attempts}
    
    return {"success": True, "message": "Adgang", "failed_attempts": 0}


# Decision Table Test + Grænseværditest
@pytest.mark.parametrize("username,password,account_locked,failed_attempts,expected_success,expected_message", [
    # Decision Table: Kombinationer af brugernavn, password og kontostatus
    ("lars@firma.dk", "Hemlig123!", False, 0, True, "Adgang"),
    ("lars@firma.dk", "Hemlig123!", True, 0, False, "Konto låst"),
    ("lars@firma.dk", "forkert", False, 0, False, "Forkert password"),
    ("", "Hemlig123!", False, 0, False, "Ugyldigt brugernavn"),
    ("ikkeeksisterende@firma.dk", "Hemlig123!", False, 0, False, "Ugyldigt brugernavn"),
    
    # Grænseværditest: Fejlede loginforsøg (grænse ved 3)
    ("lars@firma.dk", "forkert", False, 1, False, "Forkert password"),  # 2. forsøg - konto åben
    ("lars@firma.dk", "forkert", False, 2, False, "Konto låst"),        # 3. forsøg - konto låses
    ("lars@firma.dk", "forkert", True, 3, False, "Konto låst"),         # 4. forsøg - forbliver låst
])
def test_login_validation(username, password, account_locked, failed_attempts, expected_success, expected_message):
    result = validate_login(username, password, account_locked, failed_attempts)
    assert result["success"] == expected_success
    assert result["message"] == expected_message