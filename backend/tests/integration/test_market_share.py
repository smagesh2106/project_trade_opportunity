from app.analytics.market_share import calculate_market_shares


def test_india_electrical_panel_market_share():

    trade_results = [
        (4, 10_500_000),
        (5, 8_200_000),
        (3, 4_600_000),
        (2, 2_300_000),
    ]

    results = calculate_market_shares(trade_results)

    assert len(results) == 4

    # --------------------------------------------------
    # Total market
    # --------------------------------------------------

    assert results[0].total_market_value_usd == 25_600_000

    # --------------------------------------------------
    # Germany
    # --------------------------------------------------

    assert results[0].country_id == 4

    assert results[0].trade_value_usd == 10_500_000

    assert (
        round(
            results[0].market_share_percent,
            2,
        )
        == 41.02
    )

    # --------------------------------------------------
    # United States
    # --------------------------------------------------

    assert results[1].country_id == 5

    assert results[1].trade_value_usd == 8_200_000

    assert (
        round(
            results[1].market_share_percent,
            2,
        )
        == 32.03
    )

    # --------------------------------------------------
    # UAE
    # --------------------------------------------------

    assert results[2].country_id == 3

    assert results[2].trade_value_usd == 4_600_000

    assert (
        round(
            results[2].market_share_percent,
            2,
        )
        == 17.97
    )

    # --------------------------------------------------
    # Saudi Arabia
    # --------------------------------------------------

    assert results[3].country_id == 2

    assert results[3].trade_value_usd == 2_300_000

    assert (
        round(
            results[3].market_share_percent,
            2,
        )
        == 8.98
    )

    # --------------------------------------------------
    # Market shares should add up to 100%.
    #
    # Small floating-point tolerance is used.
    # --------------------------------------------------

    total_share = sum(result.market_share_percent for result in results)

    assert round(total_share, 6) == 100.0

    # --------------------------------------------------
    # Display
    # --------------------------------------------------

    print("\nIndia electrical-panel market share:")

    for result in results:

        print(
            f"Country ID: {result.country_id}, "
            f"Trade value: "
            f"${result.trade_value_usd:,.2f}, "
            f"Market share: "
            f"{result.market_share_percent:.2f}%"
        )


def test_empty_trade_results_are_rejected():

    try:

        calculate_market_shares([])

    except ValueError as exc:

        message = str(exc).lower()

        assert "without trade results" in message

        print("\nEmpty trade results correctly rejected:")

        print(f"  {exc}")

    else:

        raise AssertionError("Expected empty trade results " "to be rejected.")


def test_zero_market_value_is_rejected():

    trade_results = [
        (4, 0),
        (5, 0),
    ]

    try:

        calculate_market_shares(trade_results)

    except ValueError as exc:

        message = str(exc).lower()

        assert "total market value is zero" in message

        print("\nZero market value correctly rejected:")

        print(f"  {exc}")

    else:

        raise AssertionError("Expected zero market value " "to be rejected.")


def test_market_share_preserves_input_order():

    trade_results = [
        (10, 50),
        (20, 30),
        (30, 20),
    ]

    results = calculate_market_shares(trade_results)

    assert [result.country_id for result in results] == [10, 20, 30]

    assert [
        round(
            result.market_share_percent,
            2,
        )
        for result in results
    ] == [50.0, 30.0, 20.0]


if __name__ == "__main__":

    test_india_electrical_panel_market_share()

    test_empty_trade_results_are_rejected()

    test_zero_market_value_is_rejected()

    test_market_share_preserves_input_order()
