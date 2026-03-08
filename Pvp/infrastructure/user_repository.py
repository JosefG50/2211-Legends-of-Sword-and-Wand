from typing import Dict, Optional
from domain.entities.user import User

class UserRepository:
    """
    In-memory repository for Users.
    """

    def __init__(self):
        self._users: Dict[str, User] = {}

    def save(self, user: User) -> None:
        self._users[user.username] = user

    def get(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def exists(self, username: str) -> bool:
        return username in self._users

    def all(self):
        return list(self._users.values())