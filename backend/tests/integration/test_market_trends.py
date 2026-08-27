from app.analytics.market_trends import calculate_market_trend


def test_market_trend():
    """
    Test market trend calculation using India's
    electrical-panel import history.
    """

    trade_history = [
        (2024, 21_300_000),
        (2025, 25_600_000),
    ]

    trend = calculate_market_trend(trade_history)

    assert trend.trade_history == [
        (2024, 21_300_000.0),
        (2025, 25_600_000.0),
    ]

    assert trend.yoy_growth is not None

    assert trend.yoy_growth.previous_year == 2024
    assert trend.yoy_growth.current_year == 2025

    assert trend.yoy_growth.previous_value_usd == 21_300_000
    assert trend.yoy_growth.current_value_usd == 25_600_000

    assert (
        round(
            trend.yoy_growth.yoy_growth_percent,
            2,
        )
        == 20.19
    )

    print("\nIndia electrical-panel market trend:")

    for year, trade_value in trend.trade_history:
        print(f"{year}: " f"${trade_value:,.2f}")

    print("YoY growth: " f"{trend.yoy_growth.yoy_growth_percent:.2f}%")


def test_market_trend_single_year():
    """
    A single year should produce history but no YoY growth.
    """

    trade_history = [
        (2025, 25_600_000),
    ]

    trend = calculate_market_trend(trade_history)

    assert trend.trade_history == [
        (2025, 25_600_000.0),
    ]

    assert trend.yoy_growth is None

    print("\nSingle-year history correctly returned " "no YoY growth.")


def test_market_trend_unsorted_history():
    """
    Market trend should defensively sort the history.
    """

    trade_history = [
        (2025, 25_600_000),
        (2024, 21_300_000),
    ]

    trend = calculate_market_trend(trade_history)

    assert trend.trade_history == [
        (2024, 21_300_000.0),
        (2025, 25_600_000.0),
    ]

    assert trend.yoy_growth is not None

    assert (
        round(
            trend.yoy_growth.yoy_growth_percent,
            2,
        )
        == 20.19
    )

    print("\nUnsorted history correctly " "returned in chronological order.")


def test_market_trend_empty_history():
    """
    Empty history should be rejected.
    """

    try:
        calculate_market_trend([])

        assert False, "Expected ValueError for empty trade history."

    except ValueError as exc:
        assert str(exc) == ("Cannot calculate market trend " "without trade history.")

        print("\nEmpty trade history correctly rejected:")
        print(f"  {exc}")


def test_market_trend_zero_previous_year():
    """
    Zero previous-year value should be rejected because
    YoY growth cannot be calculated.
    """

    trade_history = [
        (2024, 0),
        (2025, 10_000_000),
    ]

    try:
        calculate_market_trend(trade_history)

        assert False, "Expected ValueError for zero previous-year value."

    except ValueError as exc:
        assert str(exc) == (
            "Cannot calculate YoY growth when "
            "the previous year's trade value is zero."
        )

        print("\nZero previous-year value correctly rejected:")
        print(f"  {exc}")


if __name__ == "__main__":
    test_market_trend()
    test_market_trend_single_year()
    test_market_trend_unsorted_history()
    test_market_trend_empty_history()
    test_market_trend_zero_previous_year()
