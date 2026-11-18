
"""
Loads and manages the application's configuration settings.

All configuration values are read from environment variables
or the .env file using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Defines the application's configuration settings.
    """

    # Database configuration
    database_url: str
    test_database_url: str

    # JWT authentication configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# Single configuration object used throughout the application.
settings = Settings()
