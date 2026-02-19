import sys
import os

# Tilføj Kryptering-mappen til path så vi kan importere flat_file_db
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "Kryptering"))

# Sæt arbejdsmappe til Api & Auth, så db-filer gemmes her
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import flat_file_db as db
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Bruger API", description="REST API med flat-file database og kryptering")


# --- Pydantic modeller ---

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    address: str
    street_number: str
    password: str
    enabled: bool = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address: Optional[str] = None
    street_number: Optional[str] = None
    password: Optional[str] = None
    enabled: Optional[bool] = None


# --- Endpoints ---

@app.post("/users", status_code=201, summary="Opret bruger")
def create_user(user: UserCreate):
    """Opretter en ny bruger. Persondata krypteres, password hashes."""
    result = db.create_user(
        user.first_name,
        user.last_name,
        user.address,
        user.street_number,
        user.password,
        user.enabled,
    )
    # Returner dekrypteret version (create_user returnerer krypteret)
    return db.get_user(result["person_id"])


@app.get("/users", summary="List alle brugere")
def list_users():
    """Returnerer alle brugere med dekrypteret persondata."""
    return db.get_all_users()


@app.get("/users/{person_id}", summary="Hent bruger")
def get_user(person_id: int):
    """Henter én bruger ud fra person_id."""
    user = db.get_user(person_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Bruger ikke fundet")
    return user


@app.put("/users/{person_id}", summary="Opdater bruger")
def update_user(person_id: int, updates: UserUpdate):
    """Opdaterer felter på en eksisterende bruger. Send kun de felter der skal ændres."""
    # Fjern felter der er None (ikke sendt med)
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Ingen felter at opdatere")
    result = db.update_user(person_id, update_data)
    if result is None:
        raise HTTPException(status_code=404, detail="Bruger ikke fundet")
    return result


@app.delete("/users/{person_id}", summary="Slet bruger")
def delete_user(person_id: int):
    """Sletter en bruger permanent."""
    success = db.delete_user(person_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bruger ikke fundet")
    return {"message": f"Bruger {person_id} slettet"}
