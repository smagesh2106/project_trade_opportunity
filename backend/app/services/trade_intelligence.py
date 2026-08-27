from datetime import date

from app.intelligence.trade_query_builder import TradeQueryBuilder
from app.schemas.intelligence import TradeQuery
from app.schemas.trade_opportunity import TradeOpportunityResponse
from app.services.openai_service import OpenAIService
from app.services.trade_opportunity import TradeOpportunityService


class TradeIntelligenceService:
    """
    Orchestrates the complete trade-intelligence pipeline.

    Pipeline:

        User query
            ↓
        OpenAI query understanding
            ↓
        Product / Country resolution
            ↓
        HS code resolution
            ↓
        TradeQuery
            ↓
        Trade opportunity analysis
    """

    def __init__(
        self,
        openai_service: OpenAIService,
        trade_query_builder: TradeQueryBuilder,
        trade_opportunity_service: TradeOpportunityService,
    ):
        self.openai_service = openai_service
        self.trade_query_builder = trade_query_builder
        self.trade_opportunity_service = trade_opportunity_service

    def build_trade_query(
        self,
        query: str,
    ) -> TradeQuery:
        """
        Convert a natural-language query into a resolved TradeQuery.
        """

        understanding = self.openai_service.understand_query(query)

        return self.trade_query_builder.build(
            original_query=query,
            understanding=understanding,
        )

    def analyze(
        self,
        query: str,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> TradeOpportunityResponse:
        """
        Build a TradeQuery and execute trade analysis.

        Product resolution is mandatory for trade analysis.
        If the product cannot be resolved, fail early with
        a message that identifies the original query.
        """

        trade_query = self.build_trade_query(query)

        # --------------------------------------------------
        # Product resolution validation
        # --------------------------------------------------

        if trade_query.product is None:
            raise ValueError(
                f"Product could not be resolved from the query: " f"{query}"
            )

        # --------------------------------------------------
        # HS resolution validation
        # --------------------------------------------------

        if not trade_query.hs_codes:
            raise ValueError(
                f"No HS code could be resolved for the product " f"in query: {query}"
            )

        # --------------------------------------------------
        # Execute trade opportunity analysis
        # --------------------------------------------------

        return self.trade_opportunity_service.analyze(
            trade_query=trade_query,
            period_start=period_start,
            period_end=period_end,
        )
