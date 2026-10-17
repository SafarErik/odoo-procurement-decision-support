"""SQLAlchemy engine/session construction without schema mutation."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from application.errors import RepositoryError


def create_session_factory(database_url: str) -> tuple[Engine, sessionmaker[Session]]:
    """Create an explicit engine/session factory without mutating the schema."""

    if not isinstance(database_url, str) or not database_url.strip():
        raise RepositoryError("invalid_database_configuration", "A database URL is required.")
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
    except SQLAlchemyError as error:
        raise RepositoryError(
            "invalid_database_configuration", "The database engine could not be configured."
        ) from error
    return engine, sessionmaker(bind=engine, expire_on_commit=False)
