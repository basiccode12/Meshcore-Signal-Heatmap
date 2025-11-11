"""Database models and helpers for Meshcore heatmap data."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from .settings import settings

EngineType = Engine

# Ensure SQLite enforces foreign key constraints.
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[override]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


engine: EngineType = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PingSample(Base):
    """ORM model capturing a single ping telemetry record."""

    __tablename__ = "ping_samples"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    origin_node_id = Column(String, nullable=False, index=True)
    target_node_id = Column(String, nullable=False, index=True)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude_m = Column(Float, nullable=True)

    rssi_dbm = Column(Float, nullable=True)
    snr_db = Column(Float, nullable=True)
    round_trip_ms = Column(Float, nullable=True)

    hardware_model = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    antenna_model = Column(String, nullable=True)
    antenna_gain_dbi = Column(Float, nullable=True)
    antenna_polarization = Column(String, nullable=True)
    tx_power_dbm = Column(Float, nullable=True)
    frequency_mhz = Column(Float, nullable=True)

    channel_id = Column(String, nullable=True)
    region = Column(String, nullable=True)


def init_db() -> None:
    """Create database tables."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    finally:
        session.close()


