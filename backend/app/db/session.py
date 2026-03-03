from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db import models  # noqa: F401


def _normalize_sqlalchemy_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+"):
        return dsn
    if dsn.startswith("postgresql://"):
        return dsn.replace("postgresql://", "postgresql+psycopg://", 1)
    return dsn


@lru_cache
def get_engine(dsn: str):
    return create_engine(_normalize_sqlalchemy_dsn(dsn), pool_pre_ping=True)


@lru_cache
def get_session_factory(dsn: str):
    return sessionmaker(bind=get_engine(dsn), autoflush=False, autocommit=False, class_=Session)


def init_db(dsn: str) -> None:
    Base.metadata.create_all(bind=get_engine(dsn))
