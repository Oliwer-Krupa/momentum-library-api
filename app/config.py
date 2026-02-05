import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # In production, DATABASE_URL should be set via environment variable
    # Default is provided for local development only
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://library:library@localhost:5432/library_db"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
