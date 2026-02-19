from pydantic import BaseModel
from enum import Enum
from typing import List


class Role(str, Enum):
    user = "user"
    admin = "admin"


class User(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    active: bool = True
    roles: List[Role] = []

    def toDict(self):
        return {
            "username": self.username,
            "password": self.password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "active": self.active,
            "roles": self.roles,
        }
