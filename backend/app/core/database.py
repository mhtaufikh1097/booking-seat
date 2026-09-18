from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine: Engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def database_status() -> dict[str, object]:
    status: dict[str, object] = {
        "configured": settings.database_is_configured,
        "driver": engine.url.drivername,
        "connection_checked": False,
        "connected": False,
    }
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        status.update(connection_checked=True, connected=True, message="Database connection is available.")
    except Exception as error:  # Health must remain available when MySQL is offline.
        status.update(connection_checked=True, message=f"Database connection unavailable: {error.__class__.__name__}.")
    return status
