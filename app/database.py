import time
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 5, delay: float = 2.0) -> None:
    """Create all tables with retry logic for container startup."""
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            print(f"✓ Database initialized successfully (attempt {attempt})")
            return
        except Exception as e:
            if attempt == retries:
                print(f"✗ Database initialization failed after {retries} attempts")
                raise
            print(
                f"⚠ DB connection attempt {attempt}/{retries} failed: {e}. "
                f"Retrying in {delay}s..."
            )
            time.sleep(delay)
