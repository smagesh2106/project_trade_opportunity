from datetime import date

from app.ingestion.periods import next_annual_period


def test_next_period_after_2025():
    assert next_annual_period(date(2025, 1, 1)) == "2026"


def test_incremental_period_logic_is_annual():
    latest = date(2025, 1, 1)

    next_period = next_annual_period(latest)

    assert next_period.isdigit()
    assert len(next_period) == 4
    assert next_period == "2026"


if __name__ == "__main__":
    test_next_period_after_2025()
    print("PASS next incremental period")

    test_incremental_period_logic_is_annual()
    print("PASS incremental annual period logic")

    print("Incremental ingestion tests passed.")
