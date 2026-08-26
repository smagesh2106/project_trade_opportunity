from app.analytics.trade_trends import calculate_yoy_growth


def test_india_electrical_panel_yoy_growth():

    trade_history = [
        (2024, 21_300_000),
        (2025, 25_600_000),
    ]

    trend = calculate_yoy_growth(trade_history)

    assert trend is not None

    assert trend.previous_year == 2024
    assert trend.current_year == 2025

    assert trend.previous_value_usd == 21_300_000
    assert trend.current_value_usd == 25_600_000

    # Expected:
    #
    # ((25.6M - 21.3M) / 21.3M) * 100
    #
    # = approximately 20.1878%

    assert round(trend.yoy_growth_percent, 2) == 20.19

    print("\nIndia electrical-panel YoY growth:")

    print(f"{trend.previous_year}: " f"${trend.previous_value_usd:,.2f}")

    print(f"{trend.current_year}: " f"${trend.current_value_usd:,.2f}")

    print(f"YoY growth: " f"{trend.yoy_growth_percent:.2f}%")


def test_negative_yoy_growth():

    trade_history = [
        (2024, 25_000_000),
        (2025, 20_000_000),
    ]

    trend = calculate_yoy_growth(trade_history)

    assert trend is not None

    assert round(trend.yoy_growth_percent, 2) == -20.00

    print("\nNegative YoY growth: " f"{trend.yoy_growth_percent:.2f}%")


def test_single_year_returns_none():

    trade_history = [
        (2025, 25_600_000),
    ]

    trend = calculate_yoy_growth(trade_history)

    assert trend is None

    print("\nSingle-year history correctly " "returned no YoY growth.")


def test_zero_previous_year_is_rejected():

    trade_history = [
        (2024, 0),
        (2025, 10_000_000),
    ]

    try:

        calculate_yoy_growth(trade_history)

    except ValueError as exc:

        message = str(exc).lower()

        assert "previous year's trade value is zero" in message

        print("\nZero previous-year value correctly rejected:")

        print(f"  {exc}")

    else:

        raise AssertionError(
            "Expected zero previous-year trade value " "to be rejected."
        )


if __name__ == "__main__":

    test_india_electrical_panel_yoy_growth()
    test_negative_yoy_growth()
    test_single_year_returns_none()
    test_zero_previous_year_is_rejected()
