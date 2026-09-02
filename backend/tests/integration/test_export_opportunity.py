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


def test_export_opportunity_from_india():
    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        query = (
            "Which countries should India target " "for exporting electrical panels?"
        )

        trade_query = service.build_trade_query(query)

        print("\nExport Opportunity TradeQuery:")
        print(f"  Original: {trade_query.original_query}")
        print(f"  Intent: {trade_query.intent.value}")

        if trade_query.product:
            print(f"  Product: {trade_query.product.name}")
            print("  Product confidence: " f"{trade_query.product.confidence}")

        print(f"  Country scope: {trade_query.country_scope.value}")
        print(f"  Country role: {trade_query.country_role.value}")

        if trade_query.country:
            print(f"  Country: {trade_query.country.name}")

        print("  HS codes:")

        for hs_code in trade_query.hs_codes:
            print(f"    {hs_code.code} " f"(confidence={hs_code.confidence})")

        # ==================================================
        # Validate TradeQuery
        # ==================================================

        assert trade_query.intent.value == "export_opportunity"

        assert trade_query.product is not None
        assert trade_query.product.name == "Electrical Control Panels"

        assert trade_query.country_scope.value == "specific"
        assert trade_query.country_role.value == "origin"

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

        print("\nExport opportunities:")

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

        expected = [
            ("Germany", "DEU", 14_000_000.0),
            ("United States of America", "USA", 11_000_000.0),
            ("United Arab Emirates", "ARE", 6_000_000.0),
            ("Saudi Arabia", "SAU", 4_000_000.0),
        ]

        for opportunity, (
            expected_country,
            expected_iso3,
            expected_trade_value,
        ) in zip(result.opportunities, expected):

            assert opportunity.country_name == expected_country
            assert opportunity.iso3 == expected_iso3
            assert opportunity.trade_value_usd == expected_trade_value

            # These analytics are always calculated by the service.
            assert opportunity.market_share_percent is not None
            assert opportunity.opportunity_score is not None

            # YoY growth is optional when historical data is
            # insufficient. Do not require it to be non-None.
            assert opportunity.yoy_growth_percent is None or isinstance(
                opportunity.yoy_growth_percent, (int, float)
            )

    finally:
        db.close()


if __name__ == "__main__":
    test_export_opportunity_from_india()
