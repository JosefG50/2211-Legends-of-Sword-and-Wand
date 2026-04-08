"""Authentication endpoints for local username/password login."""
import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.db_models import User
from app.models.schemas import LoginRequest, LoginResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Login or create a user account.
    If username does not exist, create it with the provided password.
    If username exists, password must match.
    """
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=422, detail="Username cannot be empty.")

    user = db.query(User).filter(User.username == username).first()
    password_hash = _hash_password(body.password)

    if user is None:
        user = User(username=username, password_hash=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)
        return LoginResponse(user=UserOut.model_validate(user), created=True)

    if user.password_hash != password_hash:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    return LoginResponse(user=UserOut.model_validate(user), created=False)
