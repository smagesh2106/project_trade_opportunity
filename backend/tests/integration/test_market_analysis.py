from app.db.session import SessionLocal

from app.intelligence.country_matcher import CountryMatcher
from app.intelligence.hs_resolver import HSResolver
from app.intelligence.product_matcher import ProductMatcher
from app.intelligence.trade_query_builder import TradeQueryBuilder

from app.repositories.country import CountryRepository
from app.repositories.product import ProductRepository
from app.repositories.trade_data import TradeDataRepository

from app.services.openai_service import OpenAIService
from app.services.trade_intelligence import TradeIntelligenceService
from app.services.trade_opportunity import TradeOpportunityService


def create_trade_intelligence_service(db):
    """
    Build the complete Trade Intelligence dependency graph.
    """

    product_repository = ProductRepository(db)

    country_repository = CountryRepository(db)

    trade_repository = TradeDataRepository(db)

    product_matcher = ProductMatcher(product_repository)

    country_matcher = CountryMatcher(country_repository)

    hs_resolver = HSResolver()

    trade_query_builder = TradeQueryBuilder(
        product_matcher=product_matcher,
        country_matcher=country_matcher,
        hs_resolver=hs_resolver,
    )

    openai_service = OpenAIService()

    trade_opportunity_service = TradeOpportunityService(
        trade_repository=trade_repository,
        country_repository=country_repository,
    )

    return TradeIntelligenceService(
        openai_service=openai_service,
        trade_query_builder=trade_query_builder,
        trade_opportunity_service=trade_opportunity_service,
    )


def test_market_analysis_imports_to_india():
    """
    Test market analysis for India's electrical-panel imports.
    """

    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        query = "How are electrical panel imports into India trending?"

        trade_query = service.build_trade_query(query)

        print("\nMarket Analysis TradeQuery:")
        print(f"  Original: {trade_query.original_query}")
        print(f"  Intent: {trade_query.intent.value}")

        if trade_query.product:
            print(f"  Product: {trade_query.product.name}")
            print("  Product confidence: " f"{trade_query.product.confidence}")

        print("  Country scope: " f"{trade_query.country_scope.value}")

        print("  Country role: " f"{trade_query.country_role.value}")

        if trade_query.country:
            print("  Country: " f"{trade_query.country.name}")

        print("  HS codes:")

        for hs_code in trade_query.hs_codes:
            print(f"    {hs_code.code} " f"(confidence={hs_code.confidence})")

        assert trade_query.intent.value == "market_analysis"

        assert trade_query.product is not None
        assert trade_query.product.name == ("Electrical Control Panels")

        assert trade_query.country_scope.value == "specific"

        assert trade_query.country_role.value == "destination"

        assert trade_query.country is not None
        assert trade_query.country.name == "India"

        assert len(trade_query.hs_codes) == 1
        assert trade_query.hs_codes[0].code == "853710"

        result = service.analyze(query)

        assert result.hs_code == "853710"
        assert result.hs_description == ("For a voltage not exceeding 1,000 V")

        assert result.country_name == "India"
        assert result.trade_flow == "import"

        assert len(result.history) == 1

        assert result.history[0].year == 2025
        assert result.history[0].trade_value_usd == 25_600_000

        assert result.yoy_growth_percent is None

        print("\nIndia electrical-panel import trend:")

        for point in result.history:
            print(f"{point.year}: " f"${point.trade_value_usd:,.2f}")

        print("YoY growth: " f"{result.yoy_growth_percent}")

    finally:
        db.close()


if __name__ == "__main__":
    test_market_analysis_imports_to_india()
