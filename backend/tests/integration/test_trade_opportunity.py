from datetime import date

from app.db.session import SessionLocal
from app.repositories.country import CountryRepository
from app.repositories.trade_data import TradeDataRepository
from app.services.trade_opportunity import TradeOpportunityService


def test_supplier_search_india():
    db = SessionLocal()

    try:
        trade_repository = TradeDataRepository(db)
        country_repository = CountryRepository(db)

        service = TradeOpportunityService(
            trade_repository=trade_repository,
            country_repository=country_repository,
        )

        result = service.find_suppliers(
            hs_code_id=4,
            hs_code="853710",
            hs_description=("For a voltage not exceeding 1,000 V"),
            target_country_id=1,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
        )

        assert result.hs_code == "853710"
        assert result.period_start == date(2025, 1, 1)

        assert len(result.opportunities) == 4

        assert result.opportunities[0].country_name == "Germany"
        assert result.opportunities[0].iso2 == "DE"
        assert result.opportunities[0].trade_value_usd == 10_500_000

        assert result.opportunities[1].country_name == "United States"
        assert result.opportunities[1].trade_value_usd == 8_200_000

        assert result.opportunities[2].country_name == ("United Arab Emirates")
        assert result.opportunities[2].trade_value_usd == 4_600_000

        assert result.opportunities[3].country_name == ("Saudi Arabia")
        assert result.opportunities[3].trade_value_usd == 2_300_000

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
    test_supplier_search_india()
