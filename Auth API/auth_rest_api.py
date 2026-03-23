from fastapi import FastAPI, Header, HTTPException

from user_service import User_service
from auth_rest_api_models import (
    RegisterUserRequest,
    GetBearerTokenRequest,
    ActivateUserRequest,
    ChangePasswordRequest,
)


class Auth_rest_api:

    def __init__(self, database_file: str = "db_user_flat_file.json"):
        self.user_service = User_service(database_file)

        self.app = FastAPI(
            title="Auth API",
            description="Authorization REST API med JWT tokens, kryptering og rollebaseret adgangskontrol.",
        )

        self.app.post("/get_bearer_token",  summary="Log ind og få token")(self.get_bearer_token)
        self.app.post("/register_user",     summary="Registrer ny bruger")(self.register_user)
        self.app.post("/deactivate_user",   summary="Deaktiver bruger (kræver token)")(self.deactivate_user)
        self.app.post("/activate_user",     summary="Reaktiver bruger (kræver admin-token)")(self.activate_user)
        self.app.post("/change_password",   summary="Skift password (kræver token)")(self.change_password)

    # --- Endpoints ---

    def get_bearer_token(self, body: GetBearerTokenRequest):
        """Log ind med brugernavn og password — returnerer et JWT Bearer token."""
        token = self.user_service.get_bearer_token(body.username, body.password)
        return {"token": token}

    def register_user(self, body: RegisterUserRequest):
        """Opret en ny bruger. Username skal være email-format."""
        self.user_service.register_user(
            body.username,
            body.password,
            body.first_name,
            body.last_name,
            body.roles,
        )
        return {"status": "Bruger oprettet"}

    def deactivate_user(
        self,
        body: ActivateUserRequest,
        token: str = Header(..., description="Bearer token fra /get_bearer_token"),
    ):
        """Deaktiver en bruger.
        - Admin kan deaktivere alle brugere
        - En bruger kan kun deaktivere sig selv
        """
        if not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Ugyldigt eller manglende token-header")
        self.user_service.deactivate_user(token, body.username)
        return {"status": f"Bruger '{body.username}' er deaktiveret"}

    def activate_user(
        self,
        body: ActivateUserRequest,
        token: str = Header(..., description="Bearer token fra /get_bearer_token — skal være admin"),
    ):
        """Reaktiver en deaktiveret bruger. Kræver admin-rettigheder."""
        if not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Ugyldigt eller manglende token-header")
        self.user_service.activate_user(token, body.username)
        return {"status": f"Bruger '{body.username}' er reaktiveret"}

    def change_password(
        self,
        body: ChangePasswordRequest,
        token: str = Header(..., description="Bearer token fra /get_bearer_token"),
    ):
        """Skift password. Kræver at man angiver det nuværende password korrekt."""
        if not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Ugyldigt eller manglende token-header")
        self.user_service.change_password(token, body.old_password, body.new_password)
        return {"status": "Password er skiftet"}
