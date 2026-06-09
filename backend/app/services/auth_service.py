from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db_models.user import User
from app.schemas.auth_schema import UserRegisterRequest
from app.utils.security import hash_password, verify_password


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_username_or_email(db: Session, username_or_email: str) -> User | None:
    statement = select(User).where(
        or_(User.username == username_or_email, User.email == username_or_email)
    )
    return db.scalar(statement)


def get_existing_user(db: Session, username: str, email: str) -> User | None:
    statement = select(User).where(or_(User.username == username, User.email == email))
    return db.scalar(statement)


def create_user(db: Session, payload: UserRegisterRequest) -> User:
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username_or_email: str, password: str) -> User | None:
    user = get_user_by_username_or_email(db, username_or_email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user
