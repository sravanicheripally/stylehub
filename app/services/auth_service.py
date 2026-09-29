from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.auth import UserRegister


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:

    statement = select(User).where(
        User.email == email
    )

    return db.scalar(statement)


def create_user(
    db: Session,
    user_data: UserRegister,
    role: UserRole = UserRole.CUSTOMER,
) -> User:

    user = User(
        email=user_data.email,
        password_hash=hash_password(
            user_data.password
        ),
        full_name=(
            user_data.full_name
            or user_data.email.partition("@")[0]
        ),
        phone=user_data.phone,
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user