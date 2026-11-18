import reflex as rx

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
    text,
    true,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)

__all__ = ["Base", "RSVP", "RecommendedItem", "AdminOwner"]


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class RecommendedItem(Base):
    __tablename__ = "recommended_item"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    normalized_name: Mapped[str] = mapped_column(
        String, nullable=False, unique=True
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default_factory=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


class AdminOwner(Base):
    __tablename__ = "admin_owner"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_admin_owner_singleton"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=False,
        default=1,
        server_default=text("1"),
    )
    sub: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )
    name: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )


class RSVP(Base):
    __tablename__ = "rsvp"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    guest_name: Mapped[str] = mapped_column(String, nullable=False, default="")
    recommended_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("recommended_item.id"),
        nullable=True,
        unique=True,
        default=None,
    )
    contribution: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="Nothing — just bringing myself",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default_factory=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
