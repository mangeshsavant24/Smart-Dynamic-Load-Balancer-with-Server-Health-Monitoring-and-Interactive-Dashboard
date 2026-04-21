from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker


# Compute DB directory relative to project root (two levels above this file)
BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "db"
DB_PATH = DB_DIR / "load_balancer.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}, echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    """Create all tables if they do not exist."""

    from . import models  # noqa: F401

    try:
        # checkfirst=True avoids recreating existing tables, but we still
        # defensively handle OperationalError in case of legacy conflicts.
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except OperationalError:
        # If tables already exist with a compatible schema, we can ignore this.
        # For serious schema mismatches, delete db/load_balancer.db manually.
        pass

