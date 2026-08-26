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
        # We return Saudi Arabia's total imports.
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
        # gives countries importing the product.
        # --------------------------------------------------

        statement = statement.group_by(TradeData.reporter_country_id).order_by(
            func.sum(TradeData.trade_value_usd).desc()
        )

        return list(self.db.execute(statement).all())

    # ==================================================
    # BUYER SEARCH FROM A SPECIFIC ORIGIN
    # ==================================================

    def find_buyer_countries_from_origin(
        self,
        hs_code_id: int,
        origin_country_id: int,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[tuple[int, float]]:

        statement = select(
            TradeData.partner_country_id,
            func.sum(TradeData.trade_value_usd).label("total_trade_value_usd"),
        ).where(
            TradeData.hs_code_id == hs_code_id,
            TradeData.trade_flow == "export",
            TradeData.reporter_country_id == origin_country_id,
        )

        # --------------------------------------------------
        # Optional time filters
        # --------------------------------------------------

        if period_start is not None:
            statement = statement.where(TradeData.period_start >= period_start)

        if period_end is not None:
            statement = statement.where(TradeData.period_start <= period_end)

        # --------------------------------------------------
        # Origin-based buyer search
        #
        # Example:
        #
        # "Who buys electrical panels from India?"
        #
        # reporter_country = India
        # partner_country  = buyer
        #
        # Therefore:
        #
        # GROUP BY partner_country_id
        # --------------------------------------------------

        statement = statement.group_by(TradeData.partner_country_id).order_by(
            func.sum(TradeData.trade_value_usd).desc()
        )

        return list(self.db.execute(statement).all())

    # ==================================================
    # HISTORICAL TRADE ANALYSIS
    # ==================================================

    def find_trade_history(
        self,
        hs_code_id: int,
        trade_flow: str,
        country_id: int | None = None,
        country_role: str = "reporter",
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[tuple[int, float]]:
        """
        Return yearly trade totals for an HS code.

        Result:

            [
                (2024, 21300000.0),
                (2025, 25600000.0),
            ]

        Parameters
        ----------
        hs_code_id:
            HS code to analyse.

        trade_flow:
            "import" or "export".

        country_id:
            Optional country filter.

        country_role:
            Determines which country column is filtered.

            "reporter":
                Filter reporter_country_id.

            "partner":
                Filter partner_country_id.

        period_start:
            Optional first period.

        period_end:
            Optional last period.
        """

        statement = select(
            func.extract(
                "year",
                TradeData.period_start,
            ).label("trade_year"),
            func.sum(TradeData.trade_value_usd).label("total_trade_value_usd"),
        ).where(
            TradeData.hs_code_id == hs_code_id,
            TradeData.trade_flow == trade_flow,
        )

        # --------------------------------------------------
        # Optional country filter
        # --------------------------------------------------

        if country_id is not None:

            if country_role == "reporter":

                statement = statement.where(TradeData.reporter_country_id == country_id)

            elif country_role == "partner":

                statement = statement.where(TradeData.partner_country_id == country_id)

            else:
                raise ValueError(
                    "country_role must be either " "'reporter' or 'partner'."
                )

        # --------------------------------------------------
        # Optional time filters
        # --------------------------------------------------

        if period_start is not None:
            statement = statement.where(TradeData.period_start >= period_start)

        if period_end is not None:
            statement = statement.where(TradeData.period_start <= period_end)

        # --------------------------------------------------
        # Group by year
        # --------------------------------------------------

        statement = statement.group_by(
            func.extract(
                "year",
                TradeData.period_start,
            )
        ).order_by(
            func.extract(
                "year",
                TradeData.period_start,
            )
        )

        rows = self.db.execute(statement).all()

        return [
            (
                int(trade_year),
                float(total_trade_value_usd),
            )
            for trade_year, total_trade_value_usd in rows
        ]

    # ==================================================
    # HISTORICAL TRADE ANALYSIS FOR A COUNTRY PAIR
    # ==================================================

    def find_trade_history_pair(
        self,
        hs_code_id: int,
        trade_flow: str,
        reporter_country_id: int,
        partner_country_id: int,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[tuple[int, float]]:
        """
        Return yearly trade totals for a specific country pair.

        Example:

            India imports electrical panels from Germany.

            reporter_country = India
            partner_country  = Germany

        Or:

            India exports electrical panels to Germany.

            reporter_country = India
            partner_country  = Germany
        """

        statement = select(
            func.extract(
                "year",
                TradeData.period_start,
            ).label("trade_year"),
            func.sum(TradeData.trade_value_usd).label("total_trade_value_usd"),
        ).where(
            TradeData.hs_code_id == hs_code_id,
            TradeData.trade_flow == trade_flow,
            TradeData.reporter_country_id == reporter_country_id,
            TradeData.partner_country_id == partner_country_id,
        )

        # --------------------------------------------------
        # Optional time filters
        # --------------------------------------------------

        if period_start is not None:
            statement = statement.where(TradeData.period_start >= period_start)

        if period_end is not None:
            statement = statement.where(TradeData.period_start <= period_end)

        # --------------------------------------------------
        # Group by year
        # --------------------------------------------------

        statement = statement.group_by(
            func.extract(
                "year",
                TradeData.period_start,
            )
        ).order_by(
            func.extract(
                "year",
                TradeData.period_start,
            )
        )

        rows = self.db.execute(statement).all()

        return [
            (
                int(trade_year),
                float(total_trade_value_usd),
            )
            for trade_year, total_trade_value_usd in rows
        ]

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
