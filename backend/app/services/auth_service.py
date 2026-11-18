
"""
Provides user registration and authentication services.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User


class UserAlreadyExistsError(Exception):
    """
    Raised when a user registers with an existing email.
    """


def register_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    """
    Registers a new user with a securely hashed password.
    """

    normalized_email = email.strip().lower()

    # Check whether the email is already registered.
    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if existing_user is not None:
        raise UserAlreadyExistsError(
            "An account with this email already exists."
        )

    user = User(
        email=normalized_email,
        hashed_password=hash_password(password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        # Handle concurrent registration attempts safely.
        db.rollback()
        raise UserAlreadyExistsError(
            "An account with this email already exists."
        ) from exc

    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    """
    Authenticates a user using email and password.

    Returns the user if credentials are valid.
    Returns None otherwise.
    """

    normalized_email = email.strip().lower()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user
