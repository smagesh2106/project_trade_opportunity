from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductHSCode(Base):
    __tablename__ = "product_hs_codes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    hs_code_id: Mapped[int] = mapped_column(
        ForeignKey("hs_codes.id", ondelete="RESTRICT"),
        nullable=False,
    )

    mapping_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    product: Mapped["Product"] = relationship(
        back_populates="hs_mappings",
    )

    hs_code: Mapped["HSCode"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "hs_code_id",
            name="uq_product_hs_code",
        ),
    )