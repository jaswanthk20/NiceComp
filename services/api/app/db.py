from functools import lru_cache
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from .config import settings


@lru_cache
def engine():
    url = settings().database_url
    e = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )
    if url.startswith("sqlite"):

        @event.listens_for(e, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    return e


def session_factory():
    return sessionmaker(engine(), expire_on_commit=False)


def get_db():
    with session_factory()() as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise


def apply_identity(db, user_id: str):
    if db.bind.dialect.name == "postgresql":
        db.execute(text("select set_config('request.jwt.claim.sub', :id, true)"), {"id": user_id})
        db.execute(text("SET LOCAL ROLE nice_api"))
