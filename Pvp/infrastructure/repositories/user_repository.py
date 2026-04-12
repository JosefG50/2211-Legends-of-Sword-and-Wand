from typing import Optional, List
from sqlalchemy.orm import Session
from domain.entities.user import User
from infrastructure.models.user_model import UserModel

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, user: User) -> None:
        """
        DANGER: We are disabling 'save' for PvP to prevent it from 
        interfering with the PvE login/registration process.
        """
        print(f"PvP tried to save user {user.username}, but PvP is in Read-Only mode.")
        pass 

    def get(self, username: str) -> Optional[User]:
        # PvP can still look up users to see if they exist in the shared DB
        model = self.db.query(UserModel).filter(UserModel.username == username).first()
        if not model:
            return None
        return User(username=model.username)

    def exists(self, username: str) -> bool:
        return self.db.query(UserModel).filter(UserModel.username == username).first() is not None

    def all(self) -> List[User]:
        models = self.db.query(UserModel).all()
        return [User(username=m.username) for m in models]