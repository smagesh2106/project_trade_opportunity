from datetime import date

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Country
from app.repositories.hs_code import HSCodeRepository
from app.repositories.trade_data import TradeDataRepository

TEST_SOURCE_NAME = "Development Trade Data"
HS_CODE = "853710"


def _country_by_iso3(db, iso3: str) -> Country:
    country = db.scalar(
        select(Country).where(
            Country.iso3 == iso3,
            Country.active.is_(True),
        )
    )

    assert country is not None, f"Country {iso3} was not found in the test database."

    return country


def test_trade_data_repository():
    db = SessionLocal()

    try:
        repository = TradeDataRepository(db)
        hs_repository = HSCodeRepository(db)

        # --------------------------------------------------
        # Resolve database records by stable business keys.
        #
        # Do not rely on database primary-key values because
        # country/HS IDs can change after syncs or reseeding.
        # --------------------------------------------------

        hs_code = hs_repository.get_by_code(HS_CODE)

        assert hs_code is not None

        hs_code_id = hs_code.id

        india = _country_by_iso3(db, "IND")
        germany = _country_by_iso3(db, "DEU")
        usa = _country_by_iso3(db, "USA")
        uae = _country_by_iso3(db, "ARE")
        saudi_arabia = _country_by_iso3(db, "SAU")

        period_start = date(2025, 1, 1)
        period_end = date(2025, 12, 31)

        # ==================================================
        # Supplier search
        # ==================================================
        #
        # Restrict this integration test to the deterministic
        # development fixture. Without source_name, the
        # repository can also include ingested UN Comtrade
        # records, which makes the expected result dependent
        # on the current contents of the database.
        # ==================================================

        supplier_results = repository.find_supplier_countries(
            hs_code_id=hs_code_id,
            target_country_id=india.id,
            period_start=period_start,
            period_end=period_end,
            source_name=TEST_SOURCE_NAME,
        )

        print("\nSupplier countries for India:")

        for country_id, trade_value in supplier_results:
            print(
                f"Country ID: {country_id}, "
                f"Trade value: "
                f"${float(trade_value):,.2f}"
            )

        # 2025 India imports:
        #
        # Germany        10.5M
        # USA             8.2M
        # UAE             4.6M
        # Saudi Arabia    2.3M

        assert len(supplier_results) == 4

        expected_suppliers = [
            (germany.id, 10_500_000),
            (usa.id, 8_200_000),
            (uae.id, 4_600_000),
            (saudi_arabia.id, 2_300_000),
        ]

        for result, expected in zip(
            supplier_results,
            expected_suppliers,
            strict=True,
        ):
            country_id, trade_value = result
            expected_country_id, expected_trade_value = expected

            assert country_id == expected_country_id
            assert float(trade_value) == expected_trade_value

        # ==================================================
        # Global supplier search
        # ==================================================

        global_supplier_results = repository.find_global_supplier_countries(
            hs_code_id=hs_code_id,
            period_start=period_start,
            period_end=period_end,
            source_name=TEST_SOURCE_NAME,
        )

        print("\nGlobal supplier countries:")

        for country_id, trade_value in global_supplier_results:
            print(
                f"Country ID: {country_id}, "
                f"Trade value: "
                f"${float(trade_value):,.2f}"
            )

        # Synthetic 2025 global exports:
        #
        # India           35.0M
        # Germany         25.0M
        # USA             20.0M
        # UAE             12.0M
        # Saudi Arabia     7.0M

        assert len(global_supplier_results) == 5

        expected_global_suppliers = [
            (india.id, 35_000_000),
            (germany.id, 25_000_000),
            (usa.id, 20_000_000),
            (uae.id, 12_000_000),
            (saudi_arabia.id, 7_000_000),
        ]

        for result, expected in zip(
            global_supplier_results,
            expected_global_suppliers,
            strict=True,
        ):
            country_id, trade_value = result
            expected_country_id, expected_trade_value = expected

            assert country_id == expected_country_id
            assert float(trade_value) == expected_trade_value

        # ==================================================
        # Global buyer search
        # ==================================================

        global_buyer_results = repository.find_global_buyer_countries(
            hs_code_id=hs_code_id,
            period_start=period_start,
            period_end=period_end,
            source_name=TEST_SOURCE_NAME,
        )

        print("\nGlobal buyer countries:")

        for country_id, trade_value in global_buyer_results:
            print(
                f"Country ID: {country_id}, "
                f"Import value: "
                f"${float(trade_value):,.2f}"
            )

        # Current synthetic 2025 import data contains:
        #
        # India imports:
        #   Germany        10.5M
        #   USA             8.2M
        #   UAE             4.6M
        #   Saudi Arabia    2.3M
        #
        # Total India imports = 25.6M

        assert len(global_buyer_results) == 1
        assert global_buyer_results[0][0] == india.id
        assert float(global_buyer_results[0][1]) == 25_600_000

        # ==================================================
        # Specific buyer country
        # ==================================================

        buyer_results = repository.find_buyer_countries(
            hs_code_id=hs_code_id,
            target_country_id=india.id,
            period_start=period_start,
            period_end=period_end,
            source_name=TEST_SOURCE_NAME,
        )

        print("\nBuyer country: India")

        for country_id, trade_value in buyer_results:
            print(
                f"Country ID: {country_id}, "
                f"Import value: "
                f"${float(trade_value):,.2f}"
            )

        assert len(buyer_results) == 1
        assert buyer_results[0][0] == india.id
        assert float(buyer_results[0][1]) == 25_600_000

        # ==================================================
        # Buyer search from a specific origin
        # ==================================================

        buyer_from_india_results = repository.find_buyer_countries_from_origin(
            hs_code_id=hs_code_id,
            origin_country_id=india.id,
            period_start=period_start,
            period_end=period_end,
            source_name=TEST_SOURCE_NAME,
        )

        print("\nBuyer countries for exports from India:")

        for country_id, trade_value in buyer_from_india_results:
            print(
                f"Country ID: {country_id}, "
                f"Export value from India: "
                f"${float(trade_value):,.2f}"
            )

        # Synthetic 2025 India exports:
        #
        # Germany        14.0M
        # USA            11.0M
        # UAE             6.0M
        # Saudi Arabia    4.0M

        assert len(buyer_from_india_results) == 4

        expected_buyers = [
            (germany.id, 14_000_000),
            (usa.id, 11_000_000),
            (uae.id, 6_000_000),
            (saudi_arabia.id, 4_000_000),
        ]

        for result, expected in zip(
            buyer_from_india_results,
            expected_buyers,
            strict=True,
        ):
            country_id, trade_value = result
            expected_country_id, expected_trade_value = expected

            assert country_id == expected_country_id
            assert float(trade_value) == expected_trade_value

        # ==================================================
        # Unknown HS code
        # ==================================================

        unknown_results = repository.find_global_buyer_countries(
            hs_code_id=999999,
            period_start=period_start,
            period_end=period_end,
            source_name=TEST_SOURCE_NAME,
        )

        assert unknown_results == []

        print("\nUnknown HS code correctly returned: []")

    finally:
        db.close()


if __name__ == "__main__":
    test_trade_data_repository()
