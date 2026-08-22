from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HSCode(Base):
    __tablename__ = "hs_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    hs_version_id: Mapped[int] = mapped_column(
        ForeignKey("hs_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    level: Mapped[int] = mapped_column(
        nullable=False,
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("hs_codes.id", ondelete="RESTRICT"),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    hs_version: Mapped["HSVersion"] = relationship(
        back_populates="hs_codes",
    )

    parent: Mapped["HSCode | None"] = relationship(
        remote_side="HSCode.id",
        back_populates="children",
    )

    children: Mapped[list["HSCode"]] = relationship(
        back_populates="parent",
    )


Index(
    "ix_hs_codes_version_code",
    HSCode.hs_version_id,
    HSCode.code,
    unique=True,
)

Index(
    "ix_hs_codes_parent_id",
    HSCode.parent_id,
)