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


def test_import_opportunity_to_india():
    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        query = "Which countries should India source " "electrical panels from?"

        trade_query = service.build_trade_query(query)

        print("\nImport Opportunity TradeQuery:")
        print(f"  Original: {trade_query.original_query}")
        print(f"  Intent: {trade_query.intent.value}")

        if trade_query.product:
            print(f"  Product: {trade_query.product.name}")
            print("  Product confidence: " f"{trade_query.product.confidence}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        if trade_query.country:
            print(f"  Country: {trade_query.country.name}")

        print("  HS codes:")

        for hs_code in trade_query.hs_codes:
            print(f"    {hs_code.code} " f"(confidence={hs_code.confidence})")

        # ==================================================
        # Validate TradeQuery
        # ==================================================

        assert trade_query.intent.value == "import_opportunity"

        assert trade_query.product is not None

        assert trade_query.product.name == "Electrical Control Panels"

        assert trade_query.country_scope.value == "specific"

        assert trade_query.country_role.value == "destination"

        assert trade_query.country is not None

        assert trade_query.country.name == "India"

        assert trade_query.country.iso2 == "IN"

        assert trade_query.country.iso3 == "IND"

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        # ==================================================
        # Analyze
        # ==================================================

        result = service.analyze(query)

        print("\nImport opportunities:")

        for opportunity in result.opportunities:
            print(
                f"{opportunity.rank}. "
                f"{opportunity.country_name} "
                f"({opportunity.iso3}) - "
                f"${opportunity.trade_value_usd:,.2f}"
            )

        # ==================================================
        # Validate results
        # ==================================================

        assert len(result.opportunities) == 4

        assert result.opportunities[0].country_name == "Germany"
        assert result.opportunities[0].trade_value_usd == 10_500_000.0

        assert result.opportunities[1].country_name == "United States"
        assert result.opportunities[1].trade_value_usd == 8_200_000.0

        assert result.opportunities[2].country_name == "United Arab Emirates"
        assert result.opportunities[2].trade_value_usd == 4_600_000.0

        assert result.opportunities[3].country_name == "Saudi Arabia"
        assert result.opportunities[3].trade_value_usd == 2_300_000.0

        # Analytics should be populated.
        for opportunity in result.opportunities:
            assert opportunity.market_share_percent is not None
            assert opportunity.yoy_growth_percent is not None
            assert opportunity.opportunity_score is not None

    finally:
        db.close()


if __name__ == "__main__":
    test_import_opportunity_to_india()
