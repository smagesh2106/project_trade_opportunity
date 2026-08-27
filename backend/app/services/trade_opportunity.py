from datetime import date

from app.analytics.market_share import calculate_market_shares
from app.analytics.opportunity_score import calculate_opportunity_score
from app.analytics.trade_trends import calculate_yoy_growth

from app.repositories.country import CountryRepository
from app.repositories.trade_data import TradeDataRepository

from app.schemas.intelligence import (
    CountryRole,
    CountryScope,
    TradeIntent,
    TradeQuery,
)

from app.schemas.trade_opportunity import (
    TradeOpportunity,
    TradeOpportunityResponse,
)

DEFAULT_PERIOD_START = date(2025, 1, 1)
DEFAULT_PERIOD_END = date(2025, 12, 31)


class TradeOpportunityService:
    def __init__(
        self,
        trade_repository: TradeDataRepository,
        country_repository: CountryRepository,
    ):
        self.trade_repository = trade_repository
        self.country_repository = country_repository

    # ==================================================
    # MAIN ANALYSIS
    # ==================================================

    def analyze(
        self,
        trade_query: TradeQuery,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> TradeOpportunityResponse:

        # --------------------------------------------------
        # Validate intent
        # --------------------------------------------------

        if trade_query.intent not in (
            TradeIntent.SUPPLIER_SEARCH,
            TradeIntent.BUYER_SEARCH,
        ):
            raise ValueError(f"Unsupported trade intent: {trade_query.intent.value}")

        # --------------------------------------------------
        # Product is required
        # --------------------------------------------------

        if trade_query.product is None:
            raise ValueError(
                f"Product could not be resolved from the query: "
                f"{trade_query.original_query}"
            )

        # --------------------------------------------------
        # At least one HS code is required
        # --------------------------------------------------

        if not trade_query.hs_codes:
            raise ValueError("At least one HS code is required for trade analysis.")

        # --------------------------------------------------
        # First version:
        #
        # Use the first resolved HS code.
        # --------------------------------------------------

        hs_code = trade_query.hs_codes[0]

        period_start, period_end = self._resolve_analysis_period(
            period_start=period_start,
            period_end=period_end,
        )

        # ==================================================
        # TRADE OPPORTUNITY SEARCH
        # ==================================================

        if trade_query.intent == TradeIntent.SUPPLIER_SEARCH:

            results = self._analyze_supplier_search(
                trade_query=trade_query,
                hs_code_id=hs_code.id,
                period_start=period_start,
                period_end=period_end,
            )

        elif trade_query.intent == TradeIntent.BUYER_SEARCH:

            results = self._analyze_buyer_search(
                trade_query=trade_query,
                hs_code_id=hs_code.id,
                period_start=period_start,
                period_end=period_end,
            )

        else:
            raise ValueError(f"Unsupported trade intent: {trade_query.intent.value}")

        # --------------------------------------------------
        # Empty results
        # --------------------------------------------------

        if not results:
            return TradeOpportunityResponse(
                hs_code=hs_code.code,
                hs_description=hs_code.description,
                period_start=period_start,
                period_end=period_end,
                opportunities=[],
            )

        # ==================================================
        # MARKET SHARE
        # ==================================================

        market_shares = calculate_market_shares(results)

        market_share_by_country = {
            item.country_id: item.market_share_percent for item in market_shares
        }

        # --------------------------------------------------
        # Supplier concentration
        #
        # First-version concentration metric:
        #
        # Sum of the two largest market shares.
        # --------------------------------------------------

        sorted_market_shares = sorted(
            (float(item.market_share_percent) for item in market_shares),
            reverse=True,
        )

        concentration_percent = sum(sorted_market_shares[:2])

        if sorted_market_shares:
            concentration_min_percent = min(sorted_market_shares)
            concentration_max_percent = max(sorted_market_shares)
        else:
            concentration_min_percent = 0.0
            concentration_max_percent = 0.0

        # ==================================================
        # YOY GROWTH
        # ==================================================

        yoy_growth_by_country: dict[int, float | None] = {}

        for country_id, _trade_value in results:

            history = self._get_country_trade_history(
                trade_query=trade_query,
                hs_code_id=hs_code.id,
                country_id=country_id,
                period_start=None,
                period_end=period_end,
            )

            trend = calculate_yoy_growth(history)

            if trend is None:
                yoy_growth_by_country[country_id] = None
            else:
                yoy_growth_by_country[country_id] = float(trend.yoy_growth_percent)

        # --------------------------------------------------
        # Opportunity scoring requires comparable YoY
        # values.
        #
        # Countries without sufficient historical data are
        # temporarily excluded from the score comparison.
        # --------------------------------------------------

        available_yoy_values = [
            value for value in yoy_growth_by_country.values() if value is not None
        ]

        # If no historical values exist, use 0.0 as a
        # neutral growth value for the scoring calculation.
        if not available_yoy_values:
            available_yoy_values = [0.0]

        # ==================================================
        # OPPORTUNITY RESULTS
        # ==================================================

        opportunities: list[TradeOpportunity] = []

        all_trade_values = [float(trade_value) for _, trade_value in results]

        all_market_share_values = [
            float(item.market_share_percent) for item in market_shares
        ]

        for rank, (country_id, trade_value) in enumerate(
            results,
            start=1,
        ):

            country = self.country_repository.get_by_id(country_id)

            if country is None:
                continue

            market_share_percent = float(market_share_by_country[country_id])

            yoy_growth_percent = yoy_growth_by_country[country_id]

            # --------------------------------------------------
            # Use neutral 0% growth when historical data is
            # unavailable.
            # --------------------------------------------------

            scoring_yoy_growth = (
                float(yoy_growth_percent) if yoy_growth_percent is not None else 0.0
            )

            score = calculate_opportunity_score(
                trade_value_usd=float(trade_value),
                all_trade_values_usd=all_trade_values,
                yoy_growth_percent=scoring_yoy_growth,
                all_yoy_growth_percent=available_yoy_values,
                market_share_percent=market_share_percent,
                all_market_share_percent=all_market_share_values,
                concentration_percent=concentration_percent,
                concentration_min_percent=concentration_min_percent,
                concentration_max_percent=concentration_max_percent,
            )

            opportunities.append(
                TradeOpportunity(
                    rank=rank,
                    country_id=country.id,
                    country_name=country.name,
                    iso2=country.iso2,
                    iso3=country.iso3,
                    trade_value_usd=float(trade_value),
                    market_share_percent=round(
                        market_share_percent,
                        2,
                    ),
                    yoy_growth_percent=(
                        round(
                            float(yoy_growth_percent),
                            2,
                        )
                        if yoy_growth_percent is not None
                        else None
                    ),
                    opportunity_score=score.total_score,
                    period_start=period_start,
                    period_end=period_end,
                )
            )

        return TradeOpportunityResponse(
            hs_code=hs_code.code,
            hs_description=hs_code.description,
            period_start=period_start,
            period_end=period_end,
            opportunities=opportunities,
        )

    # ==================================================
    # SUPPLIER SEARCH
    # ==================================================

    def _analyze_supplier_search(
        self,
        trade_query: TradeQuery,
        hs_code_id: int,
        period_start: date,
        period_end: date,
    ) -> list[tuple[int, float]]:

        # --------------------------------------------------
        # Specific country
        # --------------------------------------------------

        if trade_query.country_scope == CountryScope.SPECIFIC:

            if trade_query.country is None:
                raise ValueError("Country is required for specific country searches.")

            # --------------------------------------------------
            # LOCATION
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.LOCATION:
                raise ValueError(
                    "Supplier location searches are not yet "
                    "supported by the trade data model. "
                    "The current dataset contains "
                    "country-to-country trade flows, "
                    "not supplier company locations."
                )

            # --------------------------------------------------
            # DESTINATION
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.DESTINATION:

                return self.trade_repository.find_supplier_countries(
                    hs_code_id=hs_code_id,
                    target_country_id=trade_query.country.id,
                    period_start=period_start,
                    period_end=period_end,
                )

            # --------------------------------------------------
            # ORIGIN
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.ORIGIN:
                raise ValueError(
                    "Origin-based supplier searches are not "
                    "yet supported for supplier_search."
                )

            raise ValueError(
                f"Unsupported country role: " f"{trade_query.country_role.value}"
            )

        # --------------------------------------------------
        # All countries
        # --------------------------------------------------

        if trade_query.country_scope == CountryScope.ALL:

            return self.trade_repository.find_global_supplier_countries(
                hs_code_id=hs_code_id,
                period_start=period_start,
                period_end=period_end,
            )

        raise ValueError(
            f"Unsupported country scope: " f"{trade_query.country_scope.value}"
        )

    # ==================================================
    # BUYER SEARCH
    # ==================================================

    def _analyze_buyer_search(
        self,
        trade_query: TradeQuery,
        hs_code_id: int,
        period_start: date,
        period_end: date,
    ) -> list[tuple[int, float]]:

        # --------------------------------------------------
        # Specific country
        # --------------------------------------------------

        if trade_query.country_scope == CountryScope.SPECIFIC:

            if trade_query.country is None:
                raise ValueError("Country is required for specific country searches.")

            # --------------------------------------------------
            # LOCATION
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.LOCATION:

                return self.trade_repository.find_buyer_countries(
                    hs_code_id=hs_code_id,
                    target_country_id=trade_query.country.id,
                    period_start=period_start,
                    period_end=period_end,
                )

            # --------------------------------------------------
            # DESTINATION
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.DESTINATION:

                return self.trade_repository.find_buyer_countries(
                    hs_code_id=hs_code_id,
                    target_country_id=trade_query.country.id,
                    period_start=period_start,
                    period_end=period_end,
                )

            # --------------------------------------------------
            # ORIGIN
            # --------------------------------------------------

            if trade_query.country_role == CountryRole.ORIGIN:

                return self.trade_repository.find_buyer_countries_from_origin(
                    hs_code_id=hs_code_id,
                    origin_country_id=trade_query.country.id,
                    period_start=period_start,
                    period_end=period_end,
                )

            raise ValueError(
                f"Unsupported country role: " f"{trade_query.country_role.value}"
            )

        # --------------------------------------------------
        # All countries
        # --------------------------------------------------

        if trade_query.country_scope == CountryScope.ALL:

            return self.trade_repository.find_global_buyer_countries(
                hs_code_id=hs_code_id,
                period_start=period_start,
                period_end=period_end,
            )

        raise ValueError(
            f"Unsupported country scope: " f"{trade_query.country_scope.value}"
        )

    # ==================================================
    # HISTORICAL DATA
    # ==================================================

    def _get_country_trade_history(
        self,
        trade_query: TradeQuery,
        hs_code_id: int,
        country_id: int,
        period_start: date | None,
        period_end: date | None,
    ) -> list[tuple[int, float]]:

        # ==================================================
        # SUPPLIER SEARCH
        # ==================================================

        if trade_query.intent == TradeIntent.SUPPLIER_SEARCH:

            # --------------------------------------------------
            # Specific destination:
            #
            # India imports from Germany
            #
            # reporter = India
            # partner  = Germany
            # --------------------------------------------------

            if (
                trade_query.country_scope == CountryScope.SPECIFIC
                and trade_query.country_role == CountryRole.DESTINATION
                and trade_query.country is not None
            ):

                return self.trade_repository.find_trade_history_pair(
                    hs_code_id=hs_code_id,
                    trade_flow="import",
                    reporter_country_id=trade_query.country.id,
                    partner_country_id=country_id,
                    period_start=period_start,
                    period_end=period_end,
                )

            # --------------------------------------------------
            # Global supplier search:
            #
            # exporter = country
            # --------------------------------------------------

            return self.trade_repository.find_trade_history(
                hs_code_id=hs_code_id,
                trade_flow="export",
                country_id=country_id,
                country_role="reporter",
                period_start=period_start,
                period_end=period_end,
            )

        # ==================================================
        # BUYER SEARCH
        # ==================================================

        if trade_query.intent == TradeIntent.BUYER_SEARCH:

            # --------------------------------------------------
            # Origin-based buyer search:
            #
            # India exports to Germany
            #
            # reporter = India
            # partner  = Germany
            # --------------------------------------------------

            if (
                trade_query.country_scope == CountryScope.SPECIFIC
                and trade_query.country_role == CountryRole.ORIGIN
                and trade_query.country is not None
            ):

                return self.trade_repository.find_trade_history_pair(
                    hs_code_id=hs_code_id,
                    trade_flow="export",
                    reporter_country_id=trade_query.country.id,
                    partner_country_id=country_id,
                    period_start=period_start,
                    period_end=period_end,
                )

            # --------------------------------------------------
            # Specific buyer location:
            #
            # country imports product
            # --------------------------------------------------

            if (
                trade_query.country_scope == CountryScope.SPECIFIC
                and trade_query.country_role
                in (
                    CountryRole.LOCATION,
                    CountryRole.DESTINATION,
                )
            ):

                return self.trade_repository.find_trade_history(
                    hs_code_id=hs_code_id,
                    trade_flow="import",
                    country_id=country_id,
                    country_role="reporter",
                    period_start=period_start,
                    period_end=period_end,
                )

            # --------------------------------------------------
            # Global buyer search:
            #
            # importer = country
            # --------------------------------------------------

            return self.trade_repository.find_trade_history(
                hs_code_id=hs_code_id,
                trade_flow="import",
                country_id=country_id,
                country_role="reporter",
                period_start=period_start,
                period_end=period_end,
            )

        raise ValueError(f"Unsupported trade intent: {trade_query.intent.value}")

    # ==================================================
    # ANALYSIS PERIOD
    # ==================================================

    def _resolve_analysis_period(
        self,
        period_start: date | None,
        period_end: date | None,
    ) -> tuple[date, date]:

        if period_start is None and period_end is None:
            return DEFAULT_PERIOD_START, DEFAULT_PERIOD_END

        if period_start is None:
            period_start = date(period_end.year, 1, 1)

        if period_end is None:
            period_end = date(period_start.year, 12, 31)

        if period_end < period_start:
            raise ValueError("period_end must be on or after period_start.")

        return period_start, period_end
