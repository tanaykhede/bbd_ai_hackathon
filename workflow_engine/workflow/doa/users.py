from typing import Optional
from sqlalchemy.orm import Session
from workflow.db import models
from workflow.auth.security import get_password_hash, verify_password
from workflow.doa.utils import save

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def count_users(db: Session) -> int:
    return db.query(models.User).count()

def create_user(db: Session, username: str, password: str, role: str, usrid: str) -> models.User:
    hashed = get_password_hash(password)
    user = models.User(username=username, hashed_password=hashed, role=role, usrid=usrid)
    return save(db, user)

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
