from sqlalchemy.orm import Session
from domain.entities.user import User
from infrastructure.models.user_model import UserModel


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def save(self, user: User) -> None:
        model = UserModel(username=user.username)

        existing = self.db.get(UserModel, user.username)

        if existing:
            existing.username = user.username
        else:
            self.db.add(model)

        self.db.commit()

    def get(self, username: str):

        model = self.db.get(UserModel, username)

        if not model:
            return None

        return User(username=model.username)

    def exists(self, username: str) -> bool:
        return self.db.get(UserModel, username) is not None

    def all(self):
        models = self.db.query(UserModel).all()
        return [User(username=m.username) for m in models]