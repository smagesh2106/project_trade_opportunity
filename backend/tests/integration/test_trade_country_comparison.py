from app.analytics.trade_comparison import compare_trade_opportunities


def _opportunities():
    return [
        {
            "country_id": 4,
            "country_name": "Germany",
            "iso2": "DE",
            "iso3": "DEU",
            "trade_value_usd": 10_500_000,
            "market_share_percent": 41.02,
            "yoy_growth_percent": 16.67,
            "opportunity_score": 70.00,
        },
        {
            "country_id": 3,
            "country_name": "United Arab Emirates",
            "iso2": "AE",
            "iso3": "ARE",
            "trade_value_usd": 4_600_000,
            "market_share_percent": 17.97,
            "yoy_growth_percent": 31.43,
            "opportunity_score": 60.43,
        },
    ]


def test_germany_vs_uae_comparison():
    opportunities = _opportunities()

    result = compare_trade_opportunities(
        opportunities[0],
        opportunities[1],
    )

    assert result.trade_value_winner == 4
    assert result.market_share_winner == 4
    assert result.yoy_growth_winner == 3
    assert result.opportunity_score_winner == 4
    assert result.overall_winner == 4

    print("\nGermany vs United Arab Emirates:")
    print(f"Trade value winner: {result.trade_value_winner}")
    print(f"Market share winner: {result.market_share_winner}")
    print(f"YoY growth winner: {result.yoy_growth_winner}")
    print(f"Opportunity score winner: {result.opportunity_score_winner}")
    print(f"Overall winner: {result.overall_winner}")


if __name__ == "__main__":
    test_germany_vs_uae_comparison()
