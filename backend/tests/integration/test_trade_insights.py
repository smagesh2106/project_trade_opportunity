from app.analytics.trade_insights import generate_trade_insights


def test_trade_insights():

    opportunities = [
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
            "country_id": 5,
            "country_name": "United States of America",
            "iso2": "US",
            "iso3": "USA",
            "trade_value_usd": 8_200_000,
            "market_share_percent": 32.03,
            "yoy_growth_percent": 17.14,
            "opportunity_score": 55.54,
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
        {
            "country_id": 2,
            "country_name": "Saudi Arabia",
            "iso2": "SA",
            "iso3": "SAU",
            "trade_value_usd": 2_300_000,
            "market_share_percent": 8.98,
            "yoy_growth_percent": 27.78,
            "opportunity_score": 37.58,
        },
    ]

    insights = generate_trade_insights(opportunities)

    assert len(insights) == 5

    # --------------------------------------------------
    # Market leader
    # --------------------------------------------------

    leader = next(item for item in insights if item.insight_type == "market_leader")

    assert leader.country_id == 4
    assert "Germany" in leader.title
    assert "41.02%" in leader.description

    # --------------------------------------------------
    # Fastest growth
    # --------------------------------------------------

    fastest = next(item for item in insights if item.insight_type == "fastest_growth")

    assert fastest.country_id == 3
    assert "United Arab Emirates" in fastest.title
    assert "31.43%" in fastest.description

    # --------------------------------------------------
    # Highest opportunity score
    # --------------------------------------------------

    highest_score = next(
        item for item in insights if item.insight_type == "highest_opportunity_score"
    )

    assert highest_score.country_id == 4
    assert "70.00" in highest_score.description

    # --------------------------------------------------
    # Emerging supplier
    # --------------------------------------------------

    emerging = next(
        item for item in insights if item.insight_type == "emerging_supplier"
    )

    assert emerging.country_id == 3
    assert "17.97%" in emerging.description
    assert "31.43%" in emerging.description

    # --------------------------------------------------
    # Concentration
    # --------------------------------------------------

    concentration = next(
        item for item in insights if item.insight_type == "market_concentration"
    )

    assert concentration.country_id is None
    assert "73.05%" in concentration.description

    print("\nTrade insights:")

    for insight in insights:
        print(f"- [{insight.insight_type}] " f"{insight.title}")
        print(f"  {insight.description}")


def test_empty_trade_insights():

    insights = generate_trade_insights([])

    assert insights == []

    print("\nEmpty opportunity list correctly " "returned no insights.")


if __name__ == "__main__":
    test_trade_insights()
    test_empty_trade_insights()
