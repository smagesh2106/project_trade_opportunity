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

    # --------------------------------------------------
    # Repositories
    # --------------------------------------------------

    product_repository = ProductRepository(db)

    country_repository = CountryRepository(db)

    trade_repository = TradeDataRepository(db)

    # --------------------------------------------------
    # Intelligence components
    # --------------------------------------------------

    product_matcher = ProductMatcher(
        repository=product_repository,
    )

    country_matcher = CountryMatcher(
        repository=country_repository,
    )

    hs_resolver = HSResolver()

    # --------------------------------------------------
    # TradeQuery builder
    # --------------------------------------------------

    trade_query_builder = TradeQueryBuilder(
        product_matcher=product_matcher,
        country_matcher=country_matcher,
        hs_resolver=hs_resolver,
    )

    # --------------------------------------------------
    # OpenAI service
    # --------------------------------------------------

    openai_service = OpenAIService()

    # --------------------------------------------------
    # Trade opportunity service
    # --------------------------------------------------

    trade_opportunity_service = TradeOpportunityService(
        trade_repository=trade_repository,
        country_repository=country_repository,
    )

    # --------------------------------------------------
    # Final orchestrator
    # --------------------------------------------------

    return TradeIntelligenceService(
        openai_service=openai_service,
        trade_query_builder=trade_query_builder,
        trade_opportunity_service=trade_opportunity_service,
    )


def test_specific_country_query():
    """
    Test a valid supplier-search query where the country
    is the destination.

    Query:

        Find suppliers of electrical panels to India

    Meaning:

        India = destination/importing country

        Germany, USA, UAE, Saudi Arabia = supplier countries
    """

    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        # --------------------------------------------------
        # IMPORTANT:
        #
        # "to India" means India is the destination.
        #
        # This is the query that our current trade-data
        # model can answer.
        # --------------------------------------------------

        query = "Find suppliers of electrical panels to India"

        # --------------------------------------------------
        # Build TradeQuery
        # --------------------------------------------------

        trade_query = service.build_trade_query(query)

        print("\nTradeQuery:")
        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        if trade_query.product:
            print(f"  Product: " f"{trade_query.product.name}")

            print(f"  Product confidence: " f"{trade_query.product.confidence}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        if trade_query.country:
            print(f"  Country: " f"{trade_query.country.name}")

        print("  HS codes:")

        for hs_code in trade_query.hs_codes:
            print(f"    {hs_code.code} " f"(confidence={hs_code.confidence})")

        # --------------------------------------------------
        # Validate TradeQuery
        # --------------------------------------------------

        assert trade_query.intent.value == ("supplier_search")

        assert trade_query.product is not None

        assert trade_query.product.name == ("Electrical Control Panels")

        assert trade_query.product.confidence == 1.0

        assert trade_query.country_scope.value == ("specific")

        assert trade_query.country_role.value == ("destination")

        assert trade_query.country is not None

        assert trade_query.country.name == "India"

        assert trade_query.country.iso2 == "IN"

        assert trade_query.country.iso3 == "IND"

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        assert trade_query.hs_codes[0].confidence == 0.95

        # --------------------------------------------------
        # Execute trade analysis
        # --------------------------------------------------

        result = service.analyze(query)

        # --------------------------------------------------
        # Validate result
        # --------------------------------------------------

        assert result.hs_code == "853710"

        assert result.hs_description == ("For a voltage not exceeding 1,000 V")

        assert len(result.opportunities) == 4

        # --------------------------------------------------
        # Germany
        # --------------------------------------------------

        assert result.opportunities[0].country_name == ("Germany")

        assert result.opportunities[0].iso3 == "DEU"

        assert result.opportunities[0].trade_value_usd == (10_500_000)

        # --------------------------------------------------
        # United States
        # --------------------------------------------------

        assert result.opportunities[1].country_name == ("United States")

        assert result.opportunities[1].iso3 == "USA"

        assert result.opportunities[1].trade_value_usd == (8_200_000)

        # --------------------------------------------------
        # United Arab Emirates
        # --------------------------------------------------

        assert result.opportunities[2].country_name == ("United Arab Emirates")

        assert result.opportunities[2].iso3 == "ARE"

        assert result.opportunities[2].trade_value_usd == (4_600_000)

        # --------------------------------------------------
        # Saudi Arabia
        # --------------------------------------------------

        assert result.opportunities[3].country_name == ("Saudi Arabia")

        assert result.opportunities[3].iso3 == "SAU"

        assert result.opportunities[3].trade_value_usd == (2_300_000)

        # --------------------------------------------------
        # Display results
        # --------------------------------------------------

        print("\nTrade opportunities:")

        for opportunity in result.opportunities:
            print(
                f"{opportunity.rank}. "
                f"{opportunity.country_name} "
                f"({opportunity.iso3}) - "
                f"${opportunity.trade_value_usd:,.2f}"
            )

    finally:
        db.close()


def test_all_country_query():
    """
    Test a valid supplier-search query without a country.

    Query:

        Find suppliers of electrical panels

    Meaning:

        Search supplier countries globally.
    """

    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        query = "Find suppliers of electrical panels"

        # --------------------------------------------------
        # Build TradeQuery
        # --------------------------------------------------

        trade_query = service.build_trade_query(query)

        print("\nGlobal TradeQuery:")

        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        if trade_query.product:
            print(f"  Product: " f"{trade_query.product.name}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        print(f"  Country: " f"{trade_query.country}")

        # --------------------------------------------------
        # Validate TradeQuery
        # --------------------------------------------------

        assert trade_query.intent.value == ("supplier_search")

        assert trade_query.product is not None

        assert trade_query.product.name == ("Electrical Control Panels")

        assert trade_query.country_scope.value == "all"

        assert trade_query.country_role.value == ("unspecified")

        assert trade_query.country is None

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        # --------------------------------------------------
        # Execute analysis
        # --------------------------------------------------

        result = service.analyze(query)

        # --------------------------------------------------
        # Validate global results
        # --------------------------------------------------

        assert result.hs_code == "853710"

        assert result.hs_description == ("For a voltage not exceeding 1,000 V")

        assert len(result.opportunities) == 4

        # --------------------------------------------------
        # Germany
        # --------------------------------------------------

        assert result.opportunities[0].country_name == ("Germany")

        assert result.opportunities[0].iso3 == "DEU"

        assert result.opportunities[0].trade_value_usd == (25_000_000)

        # --------------------------------------------------
        # United States
        # --------------------------------------------------

        assert result.opportunities[1].country_name == ("United States")

        assert result.opportunities[1].iso3 == "USA"

        assert result.opportunities[1].trade_value_usd == (20_000_000)

        # --------------------------------------------------
        # United Arab Emirates
        # --------------------------------------------------

        assert result.opportunities[2].country_name == ("United Arab Emirates")

        assert result.opportunities[2].iso3 == "ARE"

        assert result.opportunities[2].trade_value_usd == (12_000_000)

        # --------------------------------------------------
        # Saudi Arabia
        # --------------------------------------------------

        assert result.opportunities[3].country_name == ("Saudi Arabia")

        assert result.opportunities[3].iso3 == "SAU"

        assert result.opportunities[3].trade_value_usd == (7_000_000)

        # --------------------------------------------------
        # Display results
        # --------------------------------------------------

        print("\nGlobal supplier opportunities:")

        for opportunity in result.opportunities:
            print(
                f"{opportunity.rank}. "
                f"{opportunity.country_name} "
                f"({opportunity.iso3}) - "
                f"${opportunity.trade_value_usd:,.2f}"
            )

    finally:
        db.close()


def test_supplier_location_query():
    """
    Test a supplier-location query.

    Query:

        Find suppliers of electrical panels in India

    Meaning:

        Find supplier companies located in India.

    This is intentionally NOT supported yet because the
    current trade_data model contains country-to-country
    trade flows rather than supplier company locations.
    """

    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        query = "Find suppliers of electrical panels in India"

        # --------------------------------------------------
        # Build TradeQuery
        # --------------------------------------------------

        trade_query = service.build_trade_query(query)

        print("\nSupplier Location TradeQuery:")

        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        print(f"  Product: " f"{trade_query.product.name}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        print(f"  Country: " f"{trade_query.country.name}")

        print(f"  HS codes: " f"{[hs.code for hs in trade_query.hs_codes]}")

        # --------------------------------------------------
        # Validate interpretation
        # --------------------------------------------------

        assert trade_query.intent.value == ("supplier_search")

        assert trade_query.product is not None

        assert trade_query.product.name == ("Electrical Control Panels")

        assert trade_query.country_scope.value == ("specific")

        assert trade_query.country_role.value == ("location")

        assert trade_query.country is not None

        assert trade_query.country.name == "India"

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        # --------------------------------------------------
        # The query should be rejected because the current
        # trade dataset cannot identify supplier companies.
        # --------------------------------------------------

        try:
            service.analyze(query)

        except ValueError as exc:

            message = str(exc).lower()

            assert "supplier location searches" in message

            print("\nSupplier location query correctly " "rejected:")

            print(f"  {exc}")

        else:

            raise AssertionError("Expected supplier location query " "to be rejected.")

    finally:
        db.close()


def test_unknown_product():
    """
    Test an unresolved product.

    Query:

        Find suppliers of solar powered bananas

    Expected:

        Product cannot be resolved.
        Trade analysis must be rejected.
    """

    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        query = "Find suppliers of solar powered bananas"

        # --------------------------------------------------
        # Build TradeQuery
        # --------------------------------------------------

        trade_query = service.build_trade_query(query)

        print("\nUnknown product TradeQuery:")

        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        print(f"  Product: " f"{trade_query.product}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        print(f"  Country: " f"{trade_query.country}")

        print(f"  HS codes: " f"{trade_query.hs_codes}")

        # --------------------------------------------------
        # Product should not resolve
        # --------------------------------------------------

        assert trade_query.product is None

        # --------------------------------------------------
        # No product means no HS mappings
        # --------------------------------------------------

        assert trade_query.hs_codes == []

        # --------------------------------------------------
        # Analysis must reject the query
        # --------------------------------------------------

        try:

            service.analyze(query)

        except ValueError as exc:

            message = str(exc).lower()

            assert "product could not be resolved" in message

            print("\nUnknown product correctly rejected:")

            print(f"  {exc}")

        else:

            raise AssertionError(
                "Expected TradeIntelligenceService.analyze() "
                "to reject an unresolved product."
            )

    finally:
        db.close()


if __name__ == "__main__":
    test_specific_country_query()
    test_all_country_query()
    test_supplier_location_query()
    test_unknown_product()
