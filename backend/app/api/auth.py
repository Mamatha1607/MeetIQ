
"""
Defines API endpoints for user registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.models.user import User

from app.db.session import get_db
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)
from app.services.auth_service import (
    register_user,
    authenticate_user,
    UserAlreadyExistsError,
)
from app.core.jwt import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    """
    Registers a new user.
    """

    try:
        user = register_user(
            db=db,
            email=payload.email,
            password=payload.password,
        )

        return user

    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticates a user and returns a JWT access token.
    """

    user = authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the currently authenticated user's profile.
    """

    return current_user
