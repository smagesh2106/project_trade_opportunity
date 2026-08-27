from app.analytics.trade_recommendations import (
    generate_trade_recommendations,
)


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
            "country_id": 5,
            "country_name": "United States",
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


def test_export_recommendations():
    recommendations = generate_trade_recommendations(
        _opportunities(),
        "export_opportunity",
    )

    assert len(recommendations) == 2
    assert recommendations[0].country_id == 4
    assert recommendations[0].priority == "high"
    assert recommendations[0].recommendation_type == "primary_target"
    assert "Germany" in recommendations[0].title
    assert "export market" in recommendations[0].action

    assert recommendations[1].country_id == 3
    assert recommendations[1].recommendation_type == "emerging_alternative"
    assert "31.43%" in recommendations[1].rationale

    print("\nExport recommendations:")
    for recommendation in recommendations:
        print(f"- [{recommendation.priority}] {recommendation.title}")
        print(f"  Why: {recommendation.rationale}")
        print(f"  Action: {recommendation.action}")


def test_import_recommendations():
    recommendations = generate_trade_recommendations(
        _opportunities(),
        "import_opportunity",
    )

    assert len(recommendations) == 2
    assert recommendations[0].country_id == 4
    assert "source from" in recommendations[0].title
    assert recommendations[1].country_id == 3


def test_supplier_search_recommendations():
    recommendations = generate_trade_recommendations(
        _opportunities(),
        "supplier_search",
    )

    assert len(recommendations) == 2
    assert recommendations[0].country_id == 4
    assert "supplier" in recommendations[0].title


def test_empty_recommendations():
    recommendations = generate_trade_recommendations(
        [],
        "export_opportunity",
    )

    assert recommendations == []

    print("\nEmpty opportunity list correctly returned no recommendations.")


if __name__ == "__main__":
    test_export_recommendations()
    test_import_recommendations()
    test_supplier_search_recommendations()
    test_empty_recommendations()
