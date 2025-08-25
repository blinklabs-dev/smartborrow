from sqlalchemy.orm import Session
from .. import models, schemas
from ..core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(models.user.User).filter(models.user.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.user.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
