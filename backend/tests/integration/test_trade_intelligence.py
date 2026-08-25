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

    # ==================================================
    # Repositories
    # ==================================================

    product_repository = ProductRepository(db)

    country_repository = CountryRepository(db)

    trade_repository = TradeDataRepository(db)

    # ==================================================
    # Intelligence components
    # ==================================================

    product_matcher = ProductMatcher(product_repository)

    country_matcher = CountryMatcher(country_repository)

    hs_resolver = HSResolver()

    trade_query_builder = TradeQueryBuilder(
        product_matcher=product_matcher,
        country_matcher=country_matcher,
        hs_resolver=hs_resolver,
    )

    # ==================================================
    # Services
    # ==================================================

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


# ======================================================
# SUPPLIER SEARCH
# ======================================================


def test_specific_country_query():
    """
    Test supplier search for a specific destination.

    Query:

        Find suppliers of electrical panels to India

    Meaning:

        Find countries supplying electrical panels to India.
    """

    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        query = "Find suppliers of electrical panels to India"

        trade_query = service.build_trade_query(query)

        print("\nTradeQuery:")
        print(f"  Original: {trade_query.original_query}")
        print(f"  Intent: {trade_query.intent.value}")

        if trade_query.product:
            print(f"  Product: {trade_query.product.name}")
            print(f"  Product confidence: " f"{trade_query.product.confidence}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        if trade_query.country:
            print(f"  Country: " f"{trade_query.country.name}")

        print("  HS codes:")

        for hs_code in trade_query.hs_codes:
            print(f"    {hs_code.code} " f"(confidence={hs_code.confidence})")

        # ==================================================
        # Validate TradeQuery
        # ==================================================

        assert trade_query.intent.value == "supplier_search"

        assert trade_query.product is not None

        assert trade_query.product.name == "Electrical Control Panels"

        assert trade_query.product.confidence == 1.0

        assert trade_query.country_scope.value == "specific"

        assert trade_query.country_role.value == "destination"

        assert trade_query.country is not None

        assert trade_query.country.name == "India"

        assert trade_query.country.iso2 == "IN"

        assert trade_query.country.iso3 == "IND"

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        # ==================================================
        # Execute analysis
        # ==================================================

        result = service.analyze(query)

        # ==================================================
        # Validate result
        # ==================================================

        assert result.hs_code == "853710"

        assert result.hs_description == "For a voltage not exceeding 1,000 V"

        assert len(result.opportunities) == 4

        assert result.opportunities[0].country_name == "Germany"

        assert result.opportunities[0].iso3 == "DEU"

        assert result.opportunities[0].trade_value_usd == 10_500_000

        assert result.opportunities[1].country_name == "United States"

        assert result.opportunities[1].iso3 == "USA"

        assert result.opportunities[1].trade_value_usd == 8_200_000

        assert result.opportunities[2].country_name == "United Arab Emirates"

        assert result.opportunities[2].iso3 == "ARE"

        assert result.opportunities[2].trade_value_usd == 4_600_000

        assert result.opportunities[3].country_name == "Saudi Arabia"

        assert result.opportunities[3].iso3 == "SAU"

        assert result.opportunities[3].trade_value_usd == 2_300_000

        # ==================================================
        # Display
        # ==================================================

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
    Test global supplier search.

    Query:

        Find suppliers of electrical panels

    Meaning:

        Find countries exporting electrical panels globally.

    Current synthetic dataset:

        India          $35M
        Germany        $25M
        United States  $20M
        UAE            $12M
        Saudi Arabia    $7M
    """

    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        query = "Find suppliers of electrical panels"

        trade_query = service.build_trade_query(query)

        print("\nGlobal TradeQuery:")
        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        if trade_query.product:
            print(f"  Product: " f"{trade_query.product.name}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        print(f"  Country: " f"{trade_query.country}")

        # ==================================================
        # Validate TradeQuery
        # ==================================================

        assert trade_query.intent.value == "supplier_search"

        assert trade_query.product is not None

        assert trade_query.product.name == "Electrical Control Panels"

        assert trade_query.country_scope.value == "all"

        assert trade_query.country_role.value == "unspecified"

        assert trade_query.country is None

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        # ==================================================
        # Execute analysis
        # ==================================================

        result = service.analyze(query)

        # ==================================================
        # Validate result
        # ==================================================

        assert result.hs_code == "853710"

        assert result.hs_description == "For a voltage not exceeding 1,000 V"

        assert len(result.opportunities) == 5

        # India
        assert result.opportunities[0].country_name == "India"

        assert result.opportunities[0].iso3 == "IND"

        assert result.opportunities[0].trade_value_usd == 35_000_000

        # Germany
        assert result.opportunities[1].country_name == "Germany"

        assert result.opportunities[1].iso3 == "DEU"

        assert result.opportunities[1].trade_value_usd == 25_000_000

        # USA
        assert result.opportunities[2].country_name == "United States"

        assert result.opportunities[2].iso3 == "USA"

        assert result.opportunities[2].trade_value_usd == 20_000_000

        # UAE
        assert result.opportunities[3].country_name == "United Arab Emirates"

        assert result.opportunities[3].iso3 == "ARE"

        assert result.opportunities[3].trade_value_usd == 12_000_000

        # Saudi Arabia
        assert result.opportunities[4].country_name == "Saudi Arabia"

        assert result.opportunities[4].iso3 == "SAU"

        assert result.opportunities[4].trade_value_usd == 7_000_000

        # ==================================================
        # Display
        # ==================================================

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
    Supplier location search is intentionally unsupported.

    Query:

        Find suppliers of electrical panels in India

    Meaning:

        Find supplier companies physically located in India.

    The current trade data model contains country-to-country
    trade flows, not supplier company locations.
    """

    db = SessionLocal()

    try:
        service = create_trade_intelligence_service(db)

        query = "Find suppliers of electrical panels in India"

        trade_query = service.build_trade_query(query)

        print("\nSupplier Location TradeQuery:")

        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        if trade_query.product:
            print(f"  Product: " f"{trade_query.product.name}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        if trade_query.country:
            print(f"  Country: " f"{trade_query.country.name}")

        print("  HS codes: " f"{[hs.code for hs in trade_query.hs_codes]}")

        # ==================================================
        # Validate TradeQuery
        # ==================================================

        assert trade_query.intent.value == "supplier_search"

        assert trade_query.product is not None

        assert trade_query.product.name == "Electrical Control Panels"

        assert trade_query.country_scope.value == "specific"

        assert trade_query.country_role.value == "location"

        assert trade_query.country is not None

        assert trade_query.country.name == "India"

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        # ==================================================
        # Analysis should reject this query
        # ==================================================

        try:

            service.analyze(query)

        except ValueError as exc:

            message = str(exc).lower()

            assert "supplier location searches" in message

            print("\nSupplier location query " "correctly rejected:")

            print(f"  {exc}")

        else:

            raise AssertionError("Expected supplier location " "query to be rejected.")

    finally:
        db.close()


# ======================================================
# UNKNOWN PRODUCT
# ======================================================


def test_unknown_product():
    """
    Test that an unknown product is rejected.

    Query:

        Find suppliers of solar powered bananas

    The product should not resolve because it does not
    exist in the product catalog.
    """

    db = SessionLocal()

    try:

        service = create_trade_intelligence_service(db)

        query = "Find suppliers of solar powered bananas"

        trade_query = service.build_trade_query(query)

        print("\nUnknown product TradeQuery:")

        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        if trade_query.product:

            print(f"  Product: " f"{trade_query.product.name}")

        else:

            print("  Product: None")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        print(f"  Country: " f"{trade_query.country}")

        print(f"  HS codes: " f"{trade_query.hs_codes}")

        # ==================================================
        # Product should not resolve
        # ==================================================

        assert trade_query.product is None

        # ==================================================
        # No product means no HS mappings
        # ==================================================

        assert trade_query.hs_codes == []

        # ==================================================
        # Analysis must reject the query
        # ==================================================

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


# ======================================================
# BUYER SEARCH
# ======================================================


def test_global_buyer_query():
    """
    Test a global buyer-search query.

    Query:

        Who imports electrical panels?

    Meaning:

        Find countries importing electrical panels globally.

    Current synthetic dataset:

        India = $25.6M
    """

    db = SessionLocal()

    try:

        service = create_trade_intelligence_service(db)

        query = "Who imports electrical panels?"

        # ==================================================
        # Build TradeQuery
        # ==================================================

        trade_query = service.build_trade_query(query)

        print("\nGlobal Buyer TradeQuery:")

        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        if trade_query.product:

            print(f"  Product: " f"{trade_query.product.name}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        print(f"  Country: " f"{trade_query.country}")

        print("  HS codes:")

        for hs_code in trade_query.hs_codes:

            print(f"    {hs_code.code} " f"(confidence={hs_code.confidence})")

        # ==================================================
        # Validate TradeQuery
        # ==================================================

        assert trade_query.intent.value == "buyer_search"

        assert trade_query.product is not None

        assert trade_query.product.name == "Electrical Control Panels"

        assert trade_query.country_scope.value == "all"

        assert trade_query.country_role.value == "unspecified"

        assert trade_query.country is None

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        # ==================================================
        # Execute analysis
        # ==================================================

        result = service.analyze(query)

        # ==================================================
        # Validate result
        # ==================================================

        assert result.hs_code == "853710"

        assert result.hs_description == "For a voltage not exceeding 1,000 V"

        assert len(result.opportunities) == 1

        assert result.opportunities[0].country_name == "India"

        assert result.opportunities[0].iso3 == "IND"

        assert result.opportunities[0].trade_value_usd == 25_600_000

        # ==================================================
        # Display
        # ==================================================

        print("\nGlobal buyer opportunities:")

        for opportunity in result.opportunities:

            print(
                f"{opportunity.rank}. "
                f"{opportunity.country_name} "
                f"({opportunity.iso3}) - "
                f"${opportunity.trade_value_usd:,.2f}"
            )

    finally:

        db.close()


def test_specific_buyer_query():
    """
    Test buyer-search for a specific country.

    Query:

        Who imports electrical panels in India?

    Meaning:

        Show India's import activity for the product.

    The current trade_data model provides country-level
    trade flows, not individual importer companies.
    """

    db = SessionLocal()

    try:

        service = create_trade_intelligence_service(db)

        query = "Who imports electrical panels in India?"

        # ==================================================
        # Build TradeQuery
        # ==================================================

        trade_query = service.build_trade_query(query)

        print("\nSpecific Buyer TradeQuery:")

        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        if trade_query.product:

            print(f"  Product: " f"{trade_query.product.name}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        if trade_query.country:

            print(f"  Country: " f"{trade_query.country.name}")

        print("  HS codes:")

        for hs_code in trade_query.hs_codes:

            print(f"    {hs_code.code} " f"(confidence={hs_code.confidence})")

        # ==================================================
        # Validate TradeQuery
        # ==================================================

        assert trade_query.intent.value == "buyer_search"

        assert trade_query.product is not None

        assert trade_query.product.name == "Electrical Control Panels"

        assert trade_query.country_scope.value == "specific"

        # "in India" currently means the buyer/importer
        # country for buyer_search.

        assert trade_query.country_role.value == "location"

        assert trade_query.country is not None

        assert trade_query.country.name == "India"

        assert trade_query.country.iso2 == "IN"

        assert trade_query.country.iso3 == "IND"

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        # ==================================================
        # Execute analysis
        # ==================================================

        result = service.analyze(query)

        # ==================================================
        # Validate result
        # ==================================================

        assert result.hs_code == "853710"

        assert result.hs_description == "For a voltage not exceeding 1,000 V"

        assert len(result.opportunities) == 1

        assert result.opportunities[0].country_name == "India"

        assert result.opportunities[0].iso3 == "IND"

        assert result.opportunities[0].trade_value_usd == 25_600_000

        # ==================================================
        # Display
        # ==================================================

        print("\nBuyer opportunities for India:")

        for opportunity in result.opportunities:

            print(
                f"{opportunity.rank}. "
                f"{opportunity.country_name} "
                f"({opportunity.iso3}) - "
                f"${opportunity.trade_value_usd:,.2f}"
            )

    finally:

        db.close()


# ======================================================
# INDIA ORIGIN BUYER SEARCH
# ======================================================


def test_specific_buyer_from_india_query():
    """
    Test the important business use case:

        Who buys electrical panels from India?

    Meaning:

        Find countries importing electrical panels
        originating from India.

    Current synthetic dataset:

        Germany        $14M
        United States  $11M
        UAE              $6M
        Saudi Arabia     $4M
    """

    db = SessionLocal()

    try:

        service = create_trade_intelligence_service(db)

        query = "Who buys electrical panels from India?"

        # ==================================================
        # Build TradeQuery
        # ==================================================

        trade_query = service.build_trade_query(query)

        print("\nIndia-Origin Buyer TradeQuery:")

        print(f"  Original: " f"{trade_query.original_query}")

        print(f"  Intent: " f"{trade_query.intent.value}")

        if trade_query.product:

            print(f"  Product: " f"{trade_query.product.name}")

        print(f"  Country scope: " f"{trade_query.country_scope.value}")

        print(f"  Country role: " f"{trade_query.country_role.value}")

        if trade_query.country:

            print(f"  Country: " f"{trade_query.country.name}")

        print("  HS codes:")

        for hs_code in trade_query.hs_codes:

            print(f"    {hs_code.code} " f"(confidence={hs_code.confidence})")

        # ==================================================
        # Validate TradeQuery
        # ==================================================

        assert trade_query.intent.value == "buyer_search"

        assert trade_query.product is not None

        assert trade_query.product.name == "Electrical Control Panels"

        assert trade_query.country_scope.value == "specific"

        assert trade_query.country_role.value == "origin"

        assert trade_query.country is not None

        assert trade_query.country.name == "India"

        assert trade_query.country.iso3 == "IND"

        assert len(trade_query.hs_codes) == 1

        assert trade_query.hs_codes[0].code == "853710"

        # ==================================================
        # Execute analysis
        # ==================================================

        result = service.analyze(query)

        # ==================================================
        # Validate result
        # ==================================================

        assert result.hs_code == "853710"

        assert result.hs_description == "For a voltage not exceeding 1,000 V"

        assert len(result.opportunities) == 4

        assert result.opportunities[0].country_name == "Germany"

        assert result.opportunities[0].iso3 == "DEU"

        assert result.opportunities[0].trade_value_usd == 14_000_000

        assert result.opportunities[1].country_name == "United States"

        assert result.opportunities[1].iso3 == "USA"

        assert result.opportunities[1].trade_value_usd == 11_000_000

        assert result.opportunities[2].country_name == "United Arab Emirates"

        assert result.opportunities[2].iso3 == "ARE"

        assert result.opportunities[2].trade_value_usd == 6_000_000

        assert result.opportunities[3].country_name == "Saudi Arabia"

        assert result.opportunities[3].iso3 == "SAU"

        assert result.opportunities[3].trade_value_usd == 4_000_000

        # ==================================================
        # Display
        # ==================================================

        print("\nBuyer opportunities for exports " "from India:")

        for opportunity in result.opportunities:

            print(
                f"{opportunity.rank}. "
                f"{opportunity.country_name} "
                f"({opportunity.iso3}) - "
                f"${opportunity.trade_value_usd:,.2f}"
            )

    finally:

        db.close()


# ======================================================
# MAIN
# ======================================================


if __name__ == "__main__":

    test_specific_country_query()

    test_all_country_query()

    test_supplier_location_query()

    test_unknown_product()

    test_global_buyer_query()

    test_specific_buyer_query()

    test_specific_buyer_from_india_query()
