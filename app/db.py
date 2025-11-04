import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from .config import DATABASE_URL
from .models import Base


logger = logging.getLogger("db")

# Create synchronous SQLAlchemy engine using DATABASE_URL
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured.")
    except Exception as exc:
        logger.exception("Failed to create tables: %s", exc)
        raise


def check_db_connection() -> bool:
    """Ping database by executing a trivial query."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except OperationalError as exc:
        logger.exception("Database connection failed: %s", exc)
        raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()