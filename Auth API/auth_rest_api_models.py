from pydantic import BaseModel
from typing import List

from models import Role


class RegisterUserRequest(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    roles: List[Role]


class GetBearerTokenRequest(BaseModel):
    username: str
    password: str


class ActivateUserRequest(BaseModel):
    username: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
