from datetime import date

from app.ingestion.periods import (
    is_current_or_future_year,
    next_annual_period,
    parse_annual_period,
)


def test_next_annual_period():
    assert next_annual_period(date(2025, 1, 1)) == "2026"


def test_parse_annual_period():
    assert parse_annual_period("2025") == 2025


def test_parse_annual_period_rejects_invalid():
    try:
        parse_annual_period("2025-01")
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected invalid annual period to be rejected."
        )


def test_current_or_future_year():
    reference = date(2026, 9, 2)

    assert is_current_or_future_year(
        "2026",
        reference,
    )

    assert not is_current_or_future_year(
        "2025",
        reference,
    )


if __name__ == "__main__":
    test_next_annual_period()
    print("PASS next annual period")

    test_parse_annual_period()
    print("PASS annual period parsing")

    test_parse_annual_period_rejects_invalid()
    print("PASS invalid annual period rejection")

    test_current_or_future_year()
    print("PASS current/future year detection")

    print("Incremental period tests passed.")
