from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import TradeData


class TradeDataRepository:
    def __init__(self, db: Session):
        self.db = db

    # ==================================================
    # SUPPLIER SEARCH
    # ==================================================

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
        # Specific destination country
        #
        # Example:
        #
        # "Find suppliers of electrical panels to India"
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

    # ==================================================
    # BUYER SEARCH
    # ==================================================

    def find_buyer_countries(
        self,
        hs_code_id: int,
        target_country_id: int | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[tuple[int, float]]:

        statement = select(
            TradeData.reporter_country_id,
            func.sum(TradeData.trade_value_usd).label("total_trade_value_usd"),
        ).where(
            TradeData.hs_code_id == hs_code_id,
            TradeData.trade_flow == "import",
        )

        # --------------------------------------------------
        # Specific country
        #
        # Example:
        #
        # "Who imports electrical panels in Saudi Arabia?"
        #
        # reporter_country = Saudi Arabia
        #
        # We return Saudi Arabia's total imports,
        # grouped by reporter country.
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

        statement = statement.group_by(TradeData.reporter_country_id).order_by(
            func.sum(TradeData.trade_value_usd).desc()
        )

        return list(self.db.execute(statement).all())

    def find_global_buyer_countries(
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
            TradeData.trade_flow == "import",
        )

        # --------------------------------------------------
        # Optional time filters
        # --------------------------------------------------

        if period_start is not None:
            statement = statement.where(TradeData.period_start >= period_start)

        if period_end is not None:
            statement = statement.where(TradeData.period_start <= period_end)

        # --------------------------------------------------
        # Global buyer countries
        #
        # For import records:
        #
        # reporter_country = importing country
        # partner_country  = exporting country
        #
        # Therefore:
        #
        # GROUP BY reporter_country_id
        #
        # gives us countries importing the product.
        # --------------------------------------------------

        statement = statement.group_by(TradeData.reporter_country_id).order_by(
            func.sum(TradeData.trade_value_usd).desc()
        )

        return list(self.db.execute(statement).all())

    # ==================================================
    # PERIOD INFORMATION
    # ==================================================

    def get_latest_period(
        self,
        hs_code_id: int,
        trade_flow: str,
        country_id: int | None = None,
    ) -> tuple[date, date | None] | None:

        statement = select(
            TradeData.period_start,
            TradeData.period_end,
        ).where(
            TradeData.hs_code_id == hs_code_id,
            TradeData.trade_flow == trade_flow,
        )

        if country_id is not None:
            statement = statement.where(TradeData.reporter_country_id == country_id)

        statement = statement.order_by(TradeData.period_start.desc()).limit(1)

        result = self.db.execute(statement).first()

        if result is None:
            return None

        return (
            result.period_start,
            result.period_end,
        )
