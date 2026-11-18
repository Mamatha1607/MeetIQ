
"""
Defines request and response schemas for user authentication.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """
    Validates incoming user registration data.
    """

    email: EmailStr
    password: str = Field(
        min_length=12,
        max_length=128,
    )


class UserResponse(BaseModel):
    """
    Defines the user information returned by the API.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime


class UserLogin(BaseModel):
    """
    Validates incoming login credentials.
    """

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Defines the JWT response returned after login.
    """

    access_token: str
    token_type: str = "bearer"
