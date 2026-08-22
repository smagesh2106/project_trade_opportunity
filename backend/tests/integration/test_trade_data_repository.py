from app.db.session import SessionLocal
from app.repositories.trade_data import TradeDataRepository


def test_supplier_countries_for_india():
    db = SessionLocal()

    try:
        repository = TradeDataRepository(db)

        results = repository.find_supplier_countries(
            hs_code_id=4,
            target_country_id=1,
        )

        assert len(results) == 4

        # Results should be ordered by total trade value.
        # Germany: 9.0M + 10.5M = 19.5M
        # USA:     7.0M +  8.2M = 15.2M
        # UAE:     3.5M +  4.6M =  8.1M
        # Saudi:   1.8M +  2.3M =  4.1M

        assert results[0][0] == 4
        assert float(results[0][1]) == 19_500_000

        assert results[1][0] == 5
        assert float(results[1][1]) == 15_200_000

        assert results[2][0] == 3
        assert float(results[2][1]) == 8_100_000

        assert results[3][0] == 2
        assert float(results[3][1]) == 4_100_000

        print("Supplier countries for India:")

        for country_id, value in results:
            print(f"Country ID: {country_id}, " f"Trade value: ${float(value):,.2f}")

    finally:
        db.close()


def test_global_supplier_countries():
    db = SessionLocal()

    try:
        repository = TradeDataRepository(db)

        results = repository.find_global_supplier_countries(
            hs_code_id=4,
        )

        assert len(results) == 4

        # Global exports:
        #
        # Germany: $25M
        # USA:     $20M
        # UAE:     $12M
        # Saudi:    $7M

        assert results[0][0] == 4
        assert float(results[0][1]) == 25_000_000

        assert results[1][0] == 5
        assert float(results[1][1]) == 20_000_000

        assert results[2][0] == 3
        assert float(results[2][1]) == 12_000_000

        assert results[3][0] == 2
        assert float(results[3][1]) == 7_000_000

        print("Global supplier countries:")

        for country_id, value in results:
            print(f"Country ID: {country_id}, " f"Trade value: ${float(value):,.2f}")

    finally:
        db.close()


def test_no_trade_data_for_unknown_hs_code():
    db = SessionLocal()

    try:
        repository = TradeDataRepository(db)

        results = repository.find_supplier_countries(
            hs_code_id=999,
            target_country_id=1,
        )

        assert results == []

        print("Unknown HS code correctly returned: []")

    finally:
        db.close()


if __name__ == "__main__":
    test_supplier_countries_for_india()
    test_global_supplier_countries()
    test_no_trade_data_for_unknown_hs_code()
