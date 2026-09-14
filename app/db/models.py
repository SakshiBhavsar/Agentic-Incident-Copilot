"""SQLAlchemy ORM models for the incident copilot.

Written in SQLAlchemy 2.0 "typed declarative" style: every column is declared as
``Mapped[<python type>]``, so type checkers and IDEs know exactly what each
attribute holds, and nullability is inferred from ``Optional``/``| None``.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, MetaData
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

# Deterministic names for every constraint/index. Without this, Postgres
# auto-generates names, and Alembic can't reliably diff or drop them later.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base shared by all models (and by Alembic, later)."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Default SQL type for each Python annotation used in Mapped[...].
    type_annotation_map = {
        datetime: DateTime(timezone=True),  # always timestamptz, never naive
        dict[str, Any]: JSONB,
    }

    # After INSERT/UPDATE, fetch server-generated values (created_at,
    # updated_at, ...) via RETURNING in the same round trip. In async code this
    # matters: otherwise reading those attributes later would trigger an
    # implicit lazy SELECT, which async SQLAlchemy refuses to do.
    __mapper_args__ = {"eager_defaults": True}


def enum_column(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """Store a Python enum as VARCHAR + CHECK constraint (not a native PG ENUM).

    - ``native_enum=False``: adding a value later is a CHECK change, not an
      ``ALTER TYPE ... ADD VALUE`` migration.
    - ``values_callable``: persist the enum *value* (``"open"``), not the
      member *name* (``"OPEN"``), so raw SQL and dashboards read naturally.
    """
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=32,
        validate_strings=True,
        values_callable=lambda members: [m.value for m in members],
    )


class Severity(enum.StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(enum.StrEnum):
    """Lifecycle of an incident as it moves through the agent."""

    OPEN = "open"  # ingested, not yet picked up by the agent
    DIAGNOSING = "diagnosing"  # agent is retrieving evidence / classifying
    REMEDIATING = "remediating"  # an automated action is in flight
    ESCALATED = "escalated"  # low confidence or high risk -> handed to a human
    RESOLVED = "resolved"


class ActionType(enum.StrEnum):
    """The closed set of remediations the engine may take on its own."""

    RETRY = "retry"
    RESTART = "restart"
    ROLLBACK = "rollback"


class ActionStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[Severity] = mapped_column(enum_column(Severity, "severity"))
    status: Mapped[IncidentStatus] = mapped_column(
        enum_column(IncidentStatus, "incident_status"), default=IncidentStatus.OPEN
    )
    created_at: Mapped[datetime]