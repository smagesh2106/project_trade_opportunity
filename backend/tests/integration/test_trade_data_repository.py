from datetime import date

from app.db.session import SessionLocal
from app.repositories.trade_data import TradeDataRepository


def test_trade_data_repository():

    db = SessionLocal()

    try:

        repository = TradeDataRepository(db)

        hs_code_id = 4

        period_start = date(2025, 1, 1)
        period_end = date(2025, 12, 31)

        # ==================================================
        # Supplier search
        # ==================================================

        supplier_results = repository.find_supplier_countries(
            hs_code_id=hs_code_id,
            target_country_id=1,
            period_start=period_start,
            period_end=period_end,
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

        assert supplier_results[0][0] == 4
        assert float(supplier_results[0][1]) == 10_500_000

        assert supplier_results[1][0] == 5
        assert float(supplier_results[1][1]) == 8_200_000

        assert supplier_results[2][0] == 3
        assert float(supplier_results[2][1]) == 4_600_000

        assert supplier_results[3][0] == 2
        assert float(supplier_results[3][1]) == 2_300_000

        # ==================================================
        # Global supplier search
        # ==================================================

        global_supplier_results = repository.find_global_supplier_countries(
            hs_code_id=hs_code_id,
            period_start=period_start,
            period_end=period_end,
        )

        print("\nGlobal supplier countries:")

        for country_id, trade_value in global_supplier_results:
            print(
                f"Country ID: {country_id}, "
                f"Trade value: "
                f"${float(trade_value):,.2f}"
            )

        # 2025 global exports:
        #
        # Germany        25.0M
        # USA            20.0M
        # UAE            12.0M
        # Saudi Arabia    7.0M

        assert len(global_supplier_results) == 5

        assert global_supplier_results[1][0] == 4
        assert float(global_supplier_results[1][1]) == 25_000_000

        assert global_supplier_results[2][0] == 5
        assert float(global_supplier_results[2][1]) == 20_000_000

        assert global_supplier_results[3][0] == 3
        assert float(global_supplier_results[3][1]) == 12_000_000

        assert global_supplier_results[4][0] == 2
        assert float(global_supplier_results[4][1]) == 7_000_000

        # ==================================================
        # Global buyer search
        # ==================================================

        global_buyer_results = repository.find_global_buyer_countries(
            hs_code_id=hs_code_id,
            period_start=period_start,
            period_end=period_end,
        )

        print("\nGlobal buyer countries:")

        for country_id, trade_value in global_buyer_results:
            print(
                f"Country ID: {country_id}, "
                f"Import value: "
                f"${float(trade_value):,.2f}"
            )

        # Current synthetic 2025 data contains:
        #
        # India imports:
        #   Germany        10.5M
        #   USA             8.2M
        #   UAE             4.6M
        #   Saudi Arabia    2.3M
        #
        # Total India imports = 25.6M

        assert len(global_buyer_results) == 1

        assert global_buyer_results[0][0] == 1

        assert float(global_buyer_results[0][1]) == 25_600_000

        # ==================================================
        # Specific buyer country
        # ==================================================

        buyer_results = repository.find_buyer_countries(
            hs_code_id=hs_code_id,
            target_country_id=1,
            period_start=period_start,
            period_end=period_end,
        )

        print("\nBuyer country: India")

        for country_id, trade_value in buyer_results:
            print(
                f"Country ID: {country_id}, "
                f"Import value: "
                f"${float(trade_value):,.2f}"
            )

        assert len(buyer_results) == 1

        assert buyer_results[0][0] == 1

        assert float(buyer_results[0][1]) == 25_600_000

        # ==================================================
        # Buyer search from a specific origin
        # ==================================================

        buyer_from_india_results = repository.find_buyer_countries_from_origin(
            hs_code_id=hs_code_id,
            origin_country_id=1,
            period_start=period_start,
            period_end=period_end,
        )

        print("\nBuyer countries for exports from India:")

        for country_id, trade_value in buyer_from_india_results:
            print(
                f"Country ID: {country_id}, "
                f"Export value from India: "
                f"${float(trade_value):,.2f}"
            )

        # --------------------------------------------------
        # Current synthetic dataset does not yet contain
        # India export records for this HS code.
        #
        # Therefore the expected result is currently [].
        #
        # We will add India export seed data in the next
        # step and then change this assertion.
        # --------------------------------------------------

        assert len(buyer_from_india_results) == 4

        assert buyer_from_india_results[0][0] == 4
        assert float(buyer_from_india_results[0][1]) == 14_000_000

        assert buyer_from_india_results[1][0] == 5
        assert float(buyer_from_india_results[1][1]) == 11_000_000

        assert buyer_from_india_results[2][0] == 3
        assert float(buyer_from_india_results[2][1]) == 6_000_000

        assert buyer_from_india_results[3][0] == 2
        assert float(buyer_from_india_results[3][1]) == 4_000_000

        print("\nIndia-origin buyer search correctly " "returned no records: []")

        # ==================================================
        # Unknown HS code
        # ==================================================

        unknown_results = repository.find_global_buyer_countries(
            hs_code_id=999999,
            period_start=period_start,
            period_end=period_end,
        )

        assert unknown_results == []

        print("\nUnknown HS code correctly returned: []")

    finally:
        db.close()


if __name__ == "__main__":
    test_trade_data_repository()
