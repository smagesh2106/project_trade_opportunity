from app.intelligence.trade_query_builder import TradeQueryBuilder
from app.schemas.intelligence import TradeIntent, TradeQuery
from app.services.openai_service import OpenAIService
from app.services.trade_opportunity import TradeOpportunityService


class TradeIntelligenceService:
    """
    Orchestrates the complete Trade Opportunity Explorer
    intelligence pipeline.

    Flow:

        Natural language query
                ↓
        OpenAIService
                ↓
        QueryUnderstanding
                ↓
        TradeQueryBuilder
                ↓
        TradeQuery
                ↓
        TradeOpportunityService
                ↓
        TradeOpportunityResponse
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
        Convert a natural-language query into a resolved
        TradeQuery.

        This method performs:

            Query understanding
            Product matching
            Country matching
            HS resolution

        but does NOT execute trade analysis.
        """

        if not query or not query.strip():
            raise ValueError("Trade query cannot be empty.")

        understanding = self.openai_service.understand_query(query.strip())

        trade_query = self.trade_query_builder.build(
            original_query=query.strip(),
            understanding=understanding,
        )

        return trade_query

    def analyze(
        self,
        query: str,
    ):
        """
        Execute the complete trade intelligence pipeline.

        Natural language
            ↓
        Query understanding
            ↓
        Product / country / HS resolution
            ↓
        TradeQuery validation
            ↓
        TradeOpportunityService
            ↓
        Trade opportunities
        """

        trade_query = self.build_trade_query(query)

        # --------------------------------------------------
        # Product validation
        # --------------------------------------------------

        if trade_query.product is None:
            raise ValueError(
                "Product could not be resolved from the query: "
                f"{trade_query.original_query}"
            )

        # --------------------------------------------------
        # HS code validation
        # --------------------------------------------------

        if not trade_query.hs_codes:
            raise ValueError(
                "No HS code could be resolved for product: "
                f"{trade_query.product.name}"
            )

        # --------------------------------------------------
        # Country validation
        #
        # TradeQuery itself already validates the relationship
        # between country_scope and country.
        #
        # We only need to ensure a specific-country query
        # actually contains a resolved country.
        # --------------------------------------------------

        if (
            trade_query.country_scope.value == "specific"
            and trade_query.country is None
        ):
            raise ValueError(
                "Country could not be resolved from the query: "
                f"{trade_query.original_query}"
            )

        # --------------------------------------------------
        # Intent validation
        # --------------------------------------------------

        if trade_query.intent != TradeIntent.SUPPLIER_SEARCH:
            raise ValueError(
                "Trade intent is not yet supported: " f"{trade_query.intent.value}"
            )

        # --------------------------------------------------
        # Execute trade analysis
        # --------------------------------------------------

        return self.trade_opportunity_service.analyze(trade_query)
