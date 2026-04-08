from typing import Optional, List
from sqlalchemy.orm import Session
from domain.entities.user import User
from infrastructure.models.user_model import UserModel

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, user: User) -> None:
        # 1. Use .filter() to find the user by string username
        existing = self.db.query(UserModel).filter(UserModel.username == user.username).first()

        if existing:
            existing.username = user.username
        else:
            model = UserModel(username=user.username)
            self.db.add(model)

        self.db.commit()

    def get(self, username: str) -> Optional[User]:
        # 2. Use .filter() instead of .get()
        model = self.db.query(UserModel).filter(UserModel.username == username).first()

        if not model:
            return None

        return User(username=model.username)

    def exists(self, username: str) -> bool:
        # 3. Use .filter() to avoid the Integer conversion crash
        return self.db.query(UserModel).filter(UserModel.username == username).first() is not None

    def all(self) -> List[User]:
        models = self.db.query(UserModel).all()
        return [User(username=m.username) for m in models]