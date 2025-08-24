from typing import Optional
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from workflow.dependencies import get_db
from workflow.doa import users as users_dao
from workflow.auth.security import create_access_token, User, get_current_user, get_optional_user

router = APIRouter(prefix="/auth", tags=["auth"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str  # ignored for self-registration; first user is admin, others are user

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = users_dao.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=access_token)

@router.post("/register", response_model=UserResponse)
def register_user(req: RegisterRequest, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_user)):
    total = users_dao.count_users(db)

    # Determine role: first user becomes admin, subsequent users are regular users
    role = "admin" if total == 0 else "user"

    existing = users_dao.get_user_by_username(db, req.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    # usrid is the logged-in username if present, otherwise "system"
    creator = current_user.username if current_user is not None else "system"
    created = users_dao.create_user(db, req.username, req.password, role, creator)
    return UserResponse(id=created.id, username=created.username, role=created.role)

@router.get("/me", response_model=UserResponse)
def read_current_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_user = users_dao.get_user_by_username(db, current_user.username)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(id=db_user.id, username=db_user.username, role=db_user.role)
