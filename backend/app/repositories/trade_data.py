from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import TradeData


class TradeDataRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_supplier_countries(
        self,
        hs_code_id: int,
        target_country_id: int | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[tuple[int, float]]:

        statement = select(
            TradeData.partner_country_id,
            func.sum(TradeData.trade_value_usd).label("total_trade_value_usd"),
        ).where(
            TradeData.hs_code_id == hs_code_id,
            TradeData.trade_flow == "import",
        )

        # --------------------------------------------------
        # Specific target country
        #
        # Example:
        # India wants to find suppliers.
        #
        # reporter_country = India
        # partner_country  = supplier
        # --------------------------------------------------

        if target_country_id is not None:
            statement = statement.where(
                TradeData.reporter_country_id == target_country_id
            )

        # --------------------------------------------------
        # Optional time filters
        # --------------------------------------------------

        if period_start is not None:
            statement = statement.where(TradeData.period_start >= period_start)

        if period_end is not None:
            statement = statement.where(TradeData.period_start <= period_end)

        statement = statement.group_by(TradeData.partner_country_id).order_by(
            func.sum(TradeData.trade_value_usd).desc()
        )

        return list(self.db.execute(statement).all())

    def find_global_supplier_countries(
        self,
        hs_code_id: int,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[tuple[int, float]]:

        statement = select(
            TradeData.reporter_country_id,
            func.sum(TradeData.trade_value_usd).label("total_trade_value_usd"),
        ).where(
            TradeData.hs_code_id == hs_code_id,
            TradeData.trade_flow == "export",
        )

        if period_start is not None:
            statement = statement.where(TradeData.period_start >= period_start)

        if period_end is not None:
            statement = statement.where(TradeData.period_start <= period_end)

        statement = statement.group_by(TradeData.reporter_country_id).order_by(
            func.sum(TradeData.trade_value_usd).desc()
        )

        return list(self.db.execute(statement).all())
