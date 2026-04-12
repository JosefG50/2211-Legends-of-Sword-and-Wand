from typing import Optional
from sqlalchemy.orm import Session
from infrastructure.models.user_model import UserModel
from domain.entities.user import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, user_entity: User) -> None:
        # 1. Map Entity to Model
        db_user = UserModel(username=user_entity.username)
        # 2. Add and Commit to Postgres
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

    def get(self, username: str) -> Optional[User]:
        # Query the DB for the model
        db_user = self.db.query(UserModel).filter(UserModel.username == username).first()
        if not db_user:
            return None
        # Map Model back to Domain Entity
        return User(username=db_user.username)

    def exists(self, username: str) -> bool:
        return self.db.query(UserModel).filter(UserModel.username == username).count() > 0