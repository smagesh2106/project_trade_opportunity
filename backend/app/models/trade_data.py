from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TradeData(Base):
    __tablename__ = "trade_data"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    reporter_country_id: Mapped[int] = mapped_column(
        ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False,
    )

    partner_country_id: Mapped[int] = mapped_column(
        ForeignKey("countries.id", ondelete="RESTRICT"),
        nullable=False,
    )

    hs_code_id: Mapped[int] = mapped_column(
        ForeignKey("hs_codes.id", ondelete="RESTRICT"),
        nullable=False,
    )

    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    period_end: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    period_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    trade_flow: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    trade_value: Mapped[float | None] = mapped_column(
        Numeric(20, 4),
        nullable=True,
    )

    trade_value_currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
    )

    trade_value_usd: Mapped[float | None] = mapped_column(
        Numeric(20, 4),
        nullable=True,
    )

    quantity: Mapped[float | None] = mapped_column(
        Numeric(20, 6),
        nullable=True,
    )

    quantity_unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="RESTRICT"),
        nullable=False,
    )

    source_record_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    data_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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


Index(
    "ix_trade_data_reporter_hs_period",
    TradeData.reporter_country_id,
    TradeData.hs_code_id,
    TradeData.period_start,
)

Index(
    "ix_trade_data_partner_hs_period",
    TradeData.partner_country_id,
    TradeData.hs_code_id,
    TradeData.period_start,
)

Index(
    "ix_trade_data_hs_flow_period",
    TradeData.hs_code_id,
    TradeData.trade_flow,
    TradeData.period_start,
)