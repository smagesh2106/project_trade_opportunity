from app.analytics.opportunity_score import (
    calculate_opportunity_score,
)


def test_opportunity_score():

    # --------------------------------------------------
    # Example market:
    #
    # Germany:
    #   Trade value = $10.5M
    #   YoY growth  = 25%
    #   Market share = 41.02%
    #
    # USA:
    #   Trade value = $8.2M
    #   YoY growth  = 15%
    #   Market share = 32.03%
    #
    # UAE:
    #   Trade value = $4.6M
    #   YoY growth  = 10%
    #   Market share = 17.97%
    #
    # Saudi:
    #   Trade value = $2.3M
    #   YoY growth  = 5%
    #   Market share = 8.98%
    # --------------------------------------------------

    result = calculate_opportunity_score(
        trade_value_usd=10_500_000,
        all_trade_values_usd=[
            10_500_000,
            8_200_000,
            4_600_000,
            2_300_000,
        ],
        yoy_growth_percent=25.0,
        all_yoy_growth_percent=[
            25.0,
            15.0,
            10.0,
            5.0,
        ],
        market_share_percent=41.02,
        all_market_share_percent=[
            41.02,
            32.03,
            17.97,
            8.98,
        ],
        concentration_percent=73.05,
        concentration_min_percent=50.0,
        concentration_max_percent=80.0,
    )

    # --------------------------------------------------
    # Germany is the maximum value in all comparison
    # dimensions.
    # --------------------------------------------------

    assert result.demand_score == 100.0

    assert result.growth_score == 100.0

    assert result.market_share_score == 100.0

    # 73.05 between 50 and 80.
    expected_concentration_score = ((73.05 - 50.0) / (80.0 - 50.0)) * 100.0

    assert round(
        result.concentration_score,
        2,
    ) == round(
        expected_concentration_score,
        2,
    )

    # --------------------------------------------------
    # Weighted total
    # --------------------------------------------------

    expected_total = (
        (100.0 * 0.40)
        + (100.0 * 0.30)
        + (100.0 * 0.15)
        + (result.concentration_score * 0.15)
    )

    assert round(
        result.total_score,
        2,
    ) == round(
        expected_total,
        2,
    )

    print("\nOpportunity score:")

    print(f"Demand score: " f"{result.demand_score:.2f}")

    print(f"Growth score: " f"{result.growth_score:.2f}")

    print(f"Market share score: " f"{result.market_share_score:.2f}")

    print(f"Concentration score: " f"{result.concentration_score:.2f}")

    print(f"Total opportunity score: " f"{result.total_score:.2f}")


def test_equal_values_receive_full_score():

    result = calculate_opportunity_score(
        trade_value_usd=10_000_000,
        all_trade_values_usd=[
            10_000_000,
            10_000_000,
        ],
        yoy_growth_percent=10.0,
        all_yoy_growth_percent=[
            10.0,
            10.0,
        ],
        market_share_percent=50.0,
        all_market_share_percent=[
            50.0,
            50.0,
        ],
        concentration_percent=70.0,
        concentration_min_percent=70.0,
        concentration_max_percent=70.0,
    )

    assert result.demand_score == 100.0
    assert result.growth_score == 100.0
    assert result.market_share_score == 100.0
    assert result.concentration_score == 100.0
    assert result.total_score == 100.0


def test_missing_trade_values_are_rejected():

    try:

        calculate_opportunity_score(
            trade_value_usd=10_000_000,
            all_trade_values_usd=[],
            yoy_growth_percent=10.0,
            all_yoy_growth_percent=[10.0],
            market_share_percent=50.0,
            all_market_share_percent=[50.0],
            concentration_percent=70.0,
            concentration_min_percent=50.0,
            concentration_max_percent=80.0,
        )

    except ValueError as exc:

        assert "trade values are required" in str(exc).lower()

        print("\nMissing trade values correctly rejected:")

        print(f"  {exc}")

    else:

        raise AssertionError("Expected missing trade values " "to be rejected.")


def test_missing_growth_values_are_rejected():

    try:

        calculate_opportunity_score(
            trade_value_usd=10_000_000,
            all_trade_values_usd=[
                10_000_000,
            ],
            yoy_growth_percent=10.0,
            all_yoy_growth_percent=[],
            market_share_percent=50.0,
            all_market_share_percent=[50.0],
            concentration_percent=70.0,
            concentration_min_percent=50.0,
            concentration_max_percent=80.0,
        )

    except ValueError as exc:

        assert "yoy growth values are required" in str(exc).lower()

        print("\nMissing YoY values correctly rejected:")

        print(f"  {exc}")

    else:

        raise AssertionError("Expected missing YoY values " "to be rejected.")


def test_missing_market_share_values_are_rejected():

    try:

        calculate_opportunity_score(
            trade_value_usd=10_000_000,
            all_trade_values_usd=[
                10_000_000,
            ],
            yoy_growth_percent=10.0,
            all_yoy_growth_percent=[
                10.0,
            ],
            market_share_percent=50.0,
            all_market_share_percent=[],
            concentration_percent=70.0,
            concentration_min_percent=50.0,
            concentration_max_percent=80.0,
        )

    except ValueError as exc:

        assert "market share values are required" in str(exc).lower()

        print("\nMissing market-share values correctly rejected:")

        print(f"  {exc}")

    else:

        raise AssertionError("Expected missing market-share values " "to be rejected.")


if __name__ == "__main__":

    test_opportunity_score()

    test_equal_values_receive_full_score()

    test_missing_trade_values_are_rejected()

    test_missing_growth_values_are_rejected()

    test_missing_market_share_values_are_rejected()
