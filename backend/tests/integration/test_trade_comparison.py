from app.analytics.trade_comparison import (
    compare_trade_opportunities,
)


def _germany():
    return {
        "country_id": 4,
        "country_name": "Germany",
        "iso2": "DE",
        "iso3": "DEU",
        "trade_value_usd": 10_500_000,
        "market_share_percent": 41.02,
        "yoy_growth_percent": 16.67,
        "opportunity_score": 70.00,
    }


def _uae():
    return {
        "country_id": 3,
        "country_name": "United Arab Emirates",
        "iso2": "AE",
        "iso3": "ARE",
        "trade_value_usd": 4_600_000,
        "market_share_percent": 17.97,
        "yoy_growth_percent": 31.43,
        "opportunity_score": 60.43,
    }


def test_compare_germany_and_uae():
    comparison = compare_trade_opportunities(
        _germany(),
        _uae(),
    )

    assert comparison.trade_value_winner == 4
    assert comparison.market_share_winner == 4
    assert comparison.yoy_growth_winner == 3
    assert comparison.opportunity_score_winner == 4

    assert comparison.country_a_wins == 3
    assert comparison.country_b_wins == 1

    assert comparison.overall_winner == 4

    print("\nGermany vs United Arab Emirates:")
    print(f"Trade value winner: {comparison.trade_value_winner}")
    print(f"Market share winner: {comparison.market_share_winner}")
    print(f"YoY growth winner: {comparison.yoy_growth_winner}")
    print(f"Opportunity score winner: " f"{comparison.opportunity_score_winner}")
    print(f"Overall winner: {comparison.overall_winner}")


def test_equal_values_result_in_tie():
    country_a = {
        "country_id": 1,
        "country_name": "Country A",
        "trade_value_usd": 100.0,
        "market_share_percent": 20.0,
        "yoy_growth_percent": 10.0,
        "opportunity_score": 50.0,
    }

    country_b = {
        "country_id": 2,
        "country_name": "Country B",
        "trade_value_usd": 100.0,
        "market_share_percent": 20.0,
        "yoy_growth_percent": 10.0,
        "opportunity_score": 50.0,
    }

    comparison = compare_trade_opportunities(
        country_a,
        country_b,
    )

    assert comparison.trade_value_winner is None
    assert comparison.market_share_winner is None
    assert comparison.yoy_growth_winner is None
    assert comparison.opportunity_score_winner is None

    assert comparison.country_a_wins == 0
    assert comparison.country_b_wins == 0

    assert comparison.overall_winner is None


def test_missing_metric_is_not_compared():
    country_a = _germany()

    country_b = _uae()
    country_b["yoy_growth_percent"] = None

    comparison = compare_trade_opportunities(
        country_a,
        country_b,
    )

    assert comparison.trade_value_winner == 4
    assert comparison.market_share_winner == 4
    assert comparison.yoy_growth_winner is None
    assert comparison.opportunity_score_winner == 4

    assert comparison.country_a_wins == 3
    assert comparison.country_b_wins == 0
    assert comparison.overall_winner == 4


if __name__ == "__main__":
    test_compare_germany_and_uae()
    test_equal_values_result_in_tie()
    test_missing_metric_is_not_compared()
