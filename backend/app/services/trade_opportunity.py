from datetime import date

from app.analytics.market_share import calculate_market_shares
from app.analytics.market_trends import calculate_market_trend
from app.analytics.opportunity_score import calculate_opportunity_score
from app.analytics.trade_trends import calculate_yoy_growth
from app.analytics.trade_insights import generate_trade_insights
from app.analytics.trade_recommendations import generate_trade_recommendations
from app.analytics.trade_comparison import compare_trade_opportunities
from app.schemas.trade_comparison import TradeComparisonResponse

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
from app.schemas.trade_insight import TradeInsight as TradeInsightSchema
from app.schemas.trade_recommendation import (
    TradeRecommendation as TradeRecommendationSchema,
)

from app.schemas.trade_trends import (
    MarketTrendPoint,
    MarketTrendResponse,
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
    ) -> TradeOpportunityResponse | MarketTrendResponse:

        # --------------------------------------------------
        # Resolve analysis period
        # --------------------------------------------------

        period_start, period_end = self._resolve_analysis_period(
            period_start=period_start,
            period_end=period_end,
        )

        # --------------------------------------------------
        # Market analysis
        # --------------------------------------------------

        if trade_query.intent == TradeIntent.MARKET_ANALYSIS:
            return self._analyze_market_analysis(
                trade_query=trade_query,
                period_start=period_start,
                period_end=period_end,
            )

        if trade_query.intent == TradeIntent.COMPARISON:
            return self._analyze_comparison(
                trade_query=trade_query,
                period_start=period_start,
                period_end=period_end,
            )

        # --------------------------------------------------
        # Validate supported opportunity intents
        # --------------------------------------------------

        if trade_query.intent not in {
            TradeIntent.SUPPLIER_SEARCH,
            TradeIntent.BUYER_SEARCH,
            TradeIntent.EXPORT_OPPORTUNITY,
            TradeIntent.IMPORT_OPPORTUNITY,
        }:
            raise ValueError(f"Unsupported trade intent: {trade_query.intent.value}")

        # --------------------------------------------------
        # Resolve HS code
        # --------------------------------------------------

        if not trade_query.hs_codes:
            raise ValueError("No HS code could be resolved from the query.")

        hs_code = trade_query.hs_codes[0]
        hs_code_id = hs_code.id

        # --------------------------------------------------
        # Find trade opportunities
        # --------------------------------------------------

        trade_results = self._find_trade_opportunities(
            trade_query=trade_query,
            hs_code_id=hs_code_id,
            period_start=period_start,
            period_end=period_end,
        )

        if not trade_results:
            return TradeOpportunityResponse(
                hs_code=hs_code.code,
                hs_description=hs_code.description,
                period_start=period_start,
                period_end=period_end,
                opportunities=[],
                insights=[],
                recommendations=[],
                comparison=None,
            )

        # --------------------------------------------------
        # Build opportunity analytics
        # --------------------------------------------------

        opportunities = self._build_trade_opportunities(
            trade_query=trade_query,
            hs_code=hs_code,
            trade_results=trade_results,
            period_start=period_start,
            period_end=period_end,
        )

        # --------------------------------------------------
        # Build insight inputs
        # --------------------------------------------------

        insight_inputs = [
            {
                "country_id": opportunity.country_id,
                "country_name": opportunity.country_name,
                "iso2": opportunity.iso2,
                "iso3": opportunity.iso3,
                "trade_value_usd": opportunity.trade_value_usd,
                "market_share_percent": opportunity.market_share_percent,
                "yoy_growth_percent": opportunity.yoy_growth_percent,
                "opportunity_score": opportunity.opportunity_score,
            }
            for opportunity in opportunities
        ]

        # --------------------------------------------------
        # Business insights
        # --------------------------------------------------

        generated_insights = generate_trade_insights(
            opportunities=insight_inputs,
        )

        # generate_trade_insights() returns analytics insight objects
        # identified by country_id. Resolve presentation fields from the
        # opportunity inputs rather than assuming they exist on the
        # analytics insight object.
        opportunity_by_country_id = {
            item["country_id"]: item for item in insight_inputs
        }

        insights = []
        for insight in generated_insights:
            country_data = opportunity_by_country_id.get(insight.country_id)

            # Ignore an orphaned insight rather than failing the entire
            # trade analysis response.
            if country_data is None:
                continue

            insights.append(
                TradeInsightSchema(
                    insight_type=insight.insight_type,
                    country_id=insight.country_id,
                    country_name=country_data["country_name"],
                    iso2=country_data["iso2"],
                    iso3=country_data["iso3"],
                    title=insight.title,
                    description=insight.description,
                )
            )

        # --------------------------------------------------
        # Business recommendations
        # --------------------------------------------------

        generated_recommendations = generate_trade_recommendations(
            opportunities=insight_inputs,
            intent=trade_query.intent.value,
        )

        recommendations = [
            TradeRecommendationSchema(
                recommendation_type=recommendation.recommendation_type,
                priority=recommendation.priority,
                country_id=recommendation.country_id,
                country_name=next(
                    (
                        item["country_name"]
                        for item in insight_inputs
                        if item["country_id"] == recommendation.country_id
                    ),
                    None,
                ),
                iso2=next(
                    (
                        item["iso2"]
                        for item in insight_inputs
                        if item["country_id"] == recommendation.country_id
                    ),
                    None,
                ),
                iso3=next(
                    (
                        item["iso3"]
                        for item in insight_inputs
                        if item["country_id"] == recommendation.country_id
                    ),
                    None,
                ),
                title=recommendation.title,
                rationale=recommendation.rationale,
                action=recommendation.action,
            )
            for recommendation in generated_recommendations
        ]

        # --------------------------------------------------
        # Return final response
        # --------------------------------------------------

        return TradeOpportunityResponse(
            hs_code=hs_code.code,
            hs_description=hs_code.description,
            period_start=period_start,
            period_end=period_end,
            opportunities=opportunities,
            insights=insights,
            recommendations=recommendations,
            comparison=None,
        )

    def _analyze_comparison(
        self,
        trade_query: TradeQuery,
        period_start: date,
        period_end: date,
    ) -> TradeOpportunityResponse:
        """
        Compare two explicitly named countries using supplier-to-destination
        trade data and the existing deterministic opportunity analytics.
        """

        if not trade_query.hs_codes:
            raise ValueError("Comparison requires at least one resolved HS code.")

        if trade_query.country is None:
            raise ValueError("Comparison requires a destination country.")

        if trade_query.country_role != CountryRole.DESTINATION:
            raise ValueError(
                "Supplier comparison currently requires the destination country "
                "to be specified."
            )

        if len(trade_query.comparison_countries) != 2:
            raise ValueError(
                "Comparison currently requires exactly two comparison countries."
            )

        comparison_ids = {country.id for country in trade_query.comparison_countries}

        if len(comparison_ids) != 2:
            raise ValueError("Comparison countries must be distinct.")

        hs_code = trade_query.hs_codes[0]

        trade_results = self.trade_repository.find_supplier_countries(
            hs_code_id=hs_code.id,
            target_country_id=trade_query.country.id,
            period_start=period_start,
            period_end=period_end,
        )

        available_ids = {country_id for country_id, _ in trade_results}
        missing_names = [
            country.name
            for country in trade_query.comparison_countries
            if country.id not in available_ids
        ]

        if missing_names:
            raise ValueError(
                "Trade data is not available for all comparison countries: "
                + ", ".join(missing_names)
            )

        supplier_query = trade_query.model_copy(
            update={"intent": TradeIntent.SUPPLIER_SEARCH}
        )

        # Build analytics against the complete supplier market first.
        # This preserves the normal market-share, YoY and opportunity-score
        # context. We then select only the two requested countries for the
        # comparison.
        all_opportunities = self._build_trade_opportunities(
            trade_query=supplier_query,
            hs_code=hs_code,
            trade_results=trade_results,
            period_start=period_start,
            period_end=period_end,
        )

        opportunity_by_country_id = {
            opportunity.country_id: opportunity for opportunity in all_opportunities
        }

        opportunities = [
            opportunity_by_country_id[country.id]
            for country in trade_query.comparison_countries
        ]

        country_a = opportunity_by_country_id[trade_query.comparison_countries[0].id]
        country_b = opportunity_by_country_id[trade_query.comparison_countries[1].id]

        comparison_result = compare_trade_opportunities(
            country_a=country_a.model_dump(),
            country_b=country_b.model_dump(),
        )

        comparison = TradeComparisonResponse(
            country_a_id=comparison_result.country_a_id,
            country_a_name=comparison_result.country_a_name,
            country_b_id=comparison_result.country_b_id,
            country_b_name=comparison_result.country_b_name,
            trade_value_winner=comparison_result.trade_value_winner,
            market_share_winner=comparison_result.market_share_winner,
            yoy_growth_winner=comparison_result.yoy_growth_winner,
            opportunity_score_winner=comparison_result.opportunity_score_winner,
            overall_winner=comparison_result.overall_winner,
            country_a_wins=comparison_result.country_a_wins,
            country_b_wins=comparison_result.country_b_wins,
        )

        return TradeOpportunityResponse(
            hs_code=hs_code.code,
            hs_description=hs_code.description,
            period_start=period_start,
            period_end=period_end,
            opportunities=opportunities,
            insights=[],
            recommendations=[],
            comparison=comparison,
        )

    def _find_trade_opportunities(
        self,
        trade_query: TradeQuery,
        hs_code_id: int,
        period_start: date,
        period_end: date,
    ) -> list[tuple[int, float]]:

        # ==================================================
        # SUPPLIER SEARCH
        # ==================================================

        if trade_query.intent == TradeIntent.SUPPLIER_SEARCH:

            return self._analyze_supplier_search(
                trade_query=trade_query,
                hs_code_id=hs_code_id,
                period_start=period_start,
                period_end=period_end,
            )

        # ==================================================
        # BUYER SEARCH
        # ==================================================

        if trade_query.intent == TradeIntent.BUYER_SEARCH:

            return self._analyze_buyer_search(
                trade_query=trade_query,
                hs_code_id=hs_code_id,
                period_start=period_start,
                period_end=period_end,
            )

        # ==================================================
        # EXPORT OPPORTUNITY
        # ==================================================

        if trade_query.intent == TradeIntent.EXPORT_OPPORTUNITY:

            return self._analyze_export_opportunity(
                trade_query=trade_query,
                hs_code_id=hs_code_id,
                period_start=period_start,
                period_end=period_end,
            )

        # ==================================================
        # IMPORT OPPORTUNITY
        # ==================================================

        if trade_query.intent == TradeIntent.IMPORT_OPPORTUNITY:

            return self._analyze_import_opportunity(
                trade_query=trade_query,
                hs_code_id=hs_code_id,
                period_start=period_start,
                period_end=period_end,
            )

        raise ValueError(f"Unsupported trade intent: {trade_query.intent.value}")

    def _build_trade_opportunities(
        self,
        trade_query: TradeQuery,
        hs_code,
        trade_results: list[tuple[int, float]],
        period_start: date,
        period_end: date,
    ) -> list[TradeOpportunity]:

        # ==================================================
        # MARKET SHARE
        # ==================================================

        market_shares = calculate_market_shares(trade_results)

        market_share_by_country = {
            item.country_id: item.market_share_percent for item in market_shares
        }

        # --------------------------------------------------
        # Trade concentration
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

        for country_id, _trade_value in trade_results:

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

        all_trade_values = [float(trade_value) for _, trade_value in trade_results]

        all_market_share_values = [
            float(item.market_share_percent) for item in market_shares
        ]

        for rank, (country_id, trade_value) in enumerate(
            trade_results,
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

        return opportunities

    def _analyze_market_analysis(
        self,
        trade_query: TradeQuery,
        period_start: date,
        period_end: date,
    ) -> MarketTrendResponse:

        if not trade_query.hs_codes:
            raise ValueError("Market analysis requires at least one resolved HS code.")

        hs_code_id = trade_query.hs_codes[0].id

        return self._analyze_market(
            trade_query=trade_query,
            hs_code_id=hs_code_id,
            period_start=period_start,
            period_end=period_end,
        )

    # ==================================================
    # MARKET ANALYSIS
    # ==================================================

    def _analyze_market(
        self,
        trade_query: TradeQuery,
        hs_code_id: int,
        period_start: date,
        period_end: date,
    ) -> MarketTrendResponse:

        # --------------------------------------------------
        # Market analysis currently requires a specific
        # country.
        # --------------------------------------------------

        if trade_query.country_scope != CountryScope.SPECIFIC:
            raise ValueError("Market analysis currently requires a specific country.")

        if trade_query.country is None:
            raise ValueError("Country is required for market analysis.")

        # --------------------------------------------------
        # Determine the trade flow.
        #
        # destination:
        #     country is the importing/reporting country
        #
        # origin:
        #     country is the exporting/reporting country
        # --------------------------------------------------

        if trade_query.country_role == CountryRole.DESTINATION:
            trade_flow = "import"

        elif trade_query.country_role == CountryRole.ORIGIN:
            trade_flow = "export"

        else:
            raise ValueError(
                "Market analysis requires the country role "
                "to be destination or origin."
            )

        history = self.trade_repository.find_trade_history(
            hs_code_id=hs_code_id,
            trade_flow=trade_flow,
            country_id=trade_query.country.id,
            country_role="reporter",
            period_start=period_start,
            period_end=period_end,
        )

        if not history:
            return MarketTrendResponse(
                hs_code=trade_query.hs_codes[0].code,
                hs_description=trade_query.hs_codes[0].description,
                country_id=trade_query.country.id,
                country_name=trade_query.country.name,
                iso2=trade_query.country.iso2,
                iso3=trade_query.country.iso3,
                trade_flow=trade_flow,
                history=[],
                yoy_growth_percent=None,
            )

        trend = calculate_market_trend(history)

        history_points = [
            MarketTrendPoint(
                year=year,
                trade_value_usd=trade_value,
            )
            for year, trade_value in trend.trade_history
        ]

        return MarketTrendResponse(
            hs_code=trade_query.hs_codes[0].code,
            hs_description=trade_query.hs_codes[0].description,
            country_id=trade_query.country.id,
            country_name=trade_query.country.name,
            iso2=trade_query.country.iso2,
            iso3=trade_query.country.iso3,
            trade_flow=trade_flow,
            history=history_points,
            yoy_growth_percent=(
                round(
                    float(trend.yoy_growth.yoy_growth_percent),
                    2,
                )
                if trend.yoy_growth is not None
                else None
            ),
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
    # EXPORT OPPORTUNITY
    # ==================================================

    def _analyze_export_opportunity(
        self,
        trade_query: TradeQuery,
        hs_code_id: int,
        period_start: date,
        period_end: date,
    ) -> list[tuple[int, float]]:

        if trade_query.country_scope != CountryScope.SPECIFIC:
            raise ValueError("Export opportunity requires a specific origin country.")

        if trade_query.country is None:
            raise ValueError("Country is required for export opportunity.")

        if trade_query.country_role != CountryRole.ORIGIN:
            raise ValueError(
                "Export opportunity requires the country to be the origin."
            )

        return self.trade_repository.find_buyer_countries_from_origin(
            hs_code_id=hs_code_id,
            origin_country_id=trade_query.country.id,
            period_start=period_start,
            period_end=period_end,
        )

    # ==================================================
    # IMPORT OPPORTUNITY
    # ==================================================

    def _analyze_import_opportunity(
        self,
        trade_query: TradeQuery,
        hs_code_id: int,
        period_start: date,
        period_end: date,
    ) -> list[tuple[int, float]]:

        # --------------------------------------------------
        # Import opportunity answers:
        #
        # "Which countries should I source this product
        #  from for the destination country?"
        #
        # Example:
        #
        # "Which countries should India source electrical
        #  panels from?"
        #
        # destination = India
        # partner      = supplier
        # --------------------------------------------------

        if trade_query.country_scope != CountryScope.SPECIFIC:
            raise ValueError(
                "Import opportunity requires a specific destination country."
            )

        if trade_query.country is None:
            raise ValueError("Country is required for import opportunity.")

        if trade_query.country_role != CountryRole.DESTINATION:
            raise ValueError(
                "Import opportunity requires the country " "to be the destination."
            )

        return self.trade_repository.find_supplier_countries(
            hs_code_id=hs_code_id,
            target_country_id=trade_query.country.id,
            period_start=period_start,
            period_end=period_end,
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

            if (
                trade_query.country_scope == CountryScope.SPECIFIC
                and trade_query.country is not None
                and trade_query.country_role == CountryRole.DESTINATION
            ):
                return self.trade_repository.find_trade_history_pair(
                    hs_code_id=hs_code_id,
                    trade_flow="import",
                    reporter_country_id=trade_query.country.id,
                    partner_country_id=country_id,
                    period_start=period_start,
                    period_end=period_end,
                )

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

            if (
                trade_query.country_scope == CountryScope.SPECIFIC
                and trade_query.country is not None
                and trade_query.country_role == CountryRole.ORIGIN
            ):
                return self.trade_repository.find_trade_history_pair(
                    hs_code_id=hs_code_id,
                    trade_flow="export",
                    reporter_country_id=trade_query.country.id,
                    partner_country_id=country_id,
                    period_start=period_start,
                    period_end=period_end,
                )

            return self.trade_repository.find_trade_history(
                hs_code_id=hs_code_id,
                trade_flow="import",
                country_id=country_id,
                country_role="reporter",
                period_start=period_start,
                period_end=period_end,
            )

        # ==================================================
        # EXPORT OPPORTUNITY
        # ==================================================

        if trade_query.intent == TradeIntent.EXPORT_OPPORTUNITY:

            if (
                trade_query.country_scope == CountryScope.SPECIFIC
                and trade_query.country is not None
                and trade_query.country_role == CountryRole.ORIGIN
            ):
                return self.trade_repository.find_trade_history_pair(
                    hs_code_id=hs_code_id,
                    trade_flow="export",
                    reporter_country_id=trade_query.country.id,
                    partner_country_id=country_id,
                    period_start=period_start,
                    period_end=period_end,
                )

            return self.trade_repository.find_trade_history(
                hs_code_id=hs_code_id,
                trade_flow="export",
                country_id=country_id,
                country_role="reporter",
                period_start=period_start,
                period_end=period_end,
            )

        # ==================================================
        # IMPORT OPPORTUNITY
        # ==================================================

        if trade_query.intent == TradeIntent.IMPORT_OPPORTUNITY:

            if (
                trade_query.country_scope == CountryScope.SPECIFIC
                and trade_query.country is not None
                and trade_query.country_role == CountryRole.DESTINATION
            ):
                return self.trade_repository.find_trade_history_pair(
                    hs_code_id=hs_code_id,
                    trade_flow="import",
                    reporter_country_id=trade_query.country.id,
                    partner_country_id=country_id,
                    period_start=period_start,
                    period_end=period_end,
                )

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

        # --------------------------------------------------
        # Neither boundary supplied:
        #
        # Use the configured default analysis period.
        # --------------------------------------------------

        if period_start is None and period_end is None:
            return DEFAULT_PERIOD_START, DEFAULT_PERIOD_END

        # --------------------------------------------------
        # Only start supplied:
        #
        # Use the supplied start year and complete the
        # period through December 31 of that same year.
        #
        # Example:
        #   2024-01-01 -> 2024-12-31
        # --------------------------------------------------

        if period_start is not None and period_end is None:
            period_end = date(
                period_start.year,
                12,
                31,
            )

        # --------------------------------------------------
        # Only end supplied:
        #
        # Use the supplied end year and start from
        # January 1 of that same year.
        #
        # Example:
        #   2024-12-31 -> 2024-01-01
        # --------------------------------------------------

        elif period_start is None and period_end is not None:
            period_start = date(
                period_end.year,
                1,
                1,
            )

        # --------------------------------------------------
        # Both boundaries supplied:
        #
        # Preserve the exact period requested by the caller.
        # --------------------------------------------------

        if period_start > period_end:
            raise ValueError("period_start cannot be after period_end.")

        return period_start, period_end
