"""Authentication endpoints for local username/password login."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.db_models import User
from app.models.schemas import LoginRequest, LoginResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Login or create a user account.
    If username does not exist, create it.
    If username exists, log in regardless of password.
    """
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=422, detail="Username cannot be empty.")

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        user = User(username=username, password_hash="")
        db.add(user)
        db.commit()
        db.refresh(user)
        return LoginResponse(user=UserOut.model_validate(user), created=True)

    return LoginResponse(user=UserOut.model_validate(user), created=False)