from app.db.session import SessionLocal
from app.repositories.country import CountryRepository
from app.repositories.trade_data import TradeDataRepository
from app.schemas.intelligence import (
    CountryScope,
    ResolvedCountry,
    ResolvedHSCode,
    ResolvedProduct,
    TradeIntent,
    TradeQuery,
)
from app.services.trade_opportunity import TradeOpportunityService


def test_trade_query_specific_country():
    db = SessionLocal()

    try:
        trade_repository = TradeDataRepository(db)
        country_repository = CountryRepository(db)

        service = TradeOpportunityService(
            trade_repository=trade_repository,
            country_repository=country_repository,
        )

        # -----------------------------------------------
        # Construct the same type of TradeQuery produced
        # by our intelligence layer.
        # -----------------------------------------------

        trade_query = TradeQuery(
            original_query=("Find suppliers of electrical panels in India"),
            intent=TradeIntent.SUPPLIER_SEARCH,
            product=ResolvedProduct(
                id=1,
                name="Electrical Control Panels",
                confidence=1.0,
            ),
            country_scope=CountryScope.SPECIFIC,
            country=ResolvedCountry(
                id=1,
                iso2="IN",
                iso3="IND",
                name="India",
                confidence=1.0,
            ),
            hs_codes=[
                ResolvedHSCode(
                    id=4,
                    code="853710",
                    description=("For a voltage not exceeding 1,000 V"),
                    level=6,
                    confidence=0.95,
                    mapping_type="candidate",
                    source="Development seed data",
                )
            ],
        )

        # -----------------------------------------------
        # Analyze
        # -----------------------------------------------

        result = service.analyze(trade_query)

        # -----------------------------------------------
        # Validate
        # -----------------------------------------------

        assert result.hs_code == "853710"

        assert result.hs_description == ("For a voltage not exceeding 1,000 V")

        assert len(result.opportunities) == 4

        assert result.opportunities[0].country_name == "Germany"
        assert result.opportunities[0].iso3 == "DEU"
        assert result.opportunities[0].trade_value_usd == 10_500_000

        assert result.opportunities[1].country_name == ("United States")
        assert result.opportunities[1].iso3 == "USA"
        assert result.opportunities[1].trade_value_usd == 8_200_000

        assert result.opportunities[2].country_name == ("United Arab Emirates")
        assert result.opportunities[2].iso3 == "ARE"
        assert result.opportunities[2].trade_value_usd == 4_600_000

        assert result.opportunities[3].country_name == ("Saudi Arabia")
        assert result.opportunities[3].iso3 == "SAU"
        assert result.opportunities[3].trade_value_usd == 2_300_000

        print("TradeQuery:")
        print(f"  Intent: {trade_query.intent.value}")
        print(f"  Product: " f"{trade_query.product.name}")
        print(f"  Country scope: " f"{trade_query.country_scope.value}")
        print(f"  Country: " f"{trade_query.country.name}")
        print(f"  HS code: " f"{trade_query.hs_codes[0].code}")

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


def test_trade_query_all_countries():
    db = SessionLocal()

    try:
        trade_repository = TradeDataRepository(db)
        country_repository = CountryRepository(db)

        service = TradeOpportunityService(
            trade_repository=trade_repository,
            country_repository=country_repository,
        )

        # -----------------------------------------------
        # No target country
        # -----------------------------------------------

        trade_query = TradeQuery(
            original_query=("Find suppliers of electrical panels"),
            intent=TradeIntent.SUPPLIER_SEARCH,
            product=ResolvedProduct(
                id=1,
                name="Electrical Control Panels",
                confidence=1.0,
            ),
            country_scope=CountryScope.ALL,
            country=None,
            hs_codes=[
                ResolvedHSCode(
                    id=4,
                    code="853710",
                    description=("For a voltage not exceeding 1,000 V"),
                    level=6,
                    confidence=0.95,
                    mapping_type="candidate",
                    source="Development seed data",
                )
            ],
        )

        result = service.analyze(trade_query)

        assert len(result.opportunities) == 4

        assert result.opportunities[0].country_name == "Germany"
        assert result.opportunities[0].trade_value_usd == 25_000_000

        assert result.opportunities[1].country_name == ("United States")
        assert result.opportunities[1].trade_value_usd == 20_000_000

        assert result.opportunities[2].country_name == ("United Arab Emirates")
        assert result.opportunities[2].trade_value_usd == 12_000_000

        assert result.opportunities[3].country_name == ("Saudi Arabia")
        assert result.opportunities[3].trade_value_usd == 7_000_000

        print("\nGlobal supplier search:")

        for opportunity in result.opportunities:
            print(
                f"{opportunity.rank}. "
                f"{opportunity.country_name} "
                f"({opportunity.iso3}) - "
                f"${opportunity.trade_value_usd:,.2f}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    test_trade_query_specific_country()
    test_trade_query_all_countries()
