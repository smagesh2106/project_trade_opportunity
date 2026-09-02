from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ======================================================
# SUPPLIER SEARCH API
# ======================================================


def test_trade_analyze_supplier_query():
    """
    Test the Trade Intelligence API for a supplier query.

    Query:

        Find suppliers of electrical panels to India

    Expected:

        Germany
        United States of America
        United Arab Emirates
        Saudi Arabia
    """

    response = client.post(
        "/api/v1/trade/analyze",
        json={"query": "Find suppliers of electrical panels to India"},
    )

    # --------------------------------------------------
    # HTTP response
    # --------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    # --------------------------------------------------
    # Top-level response
    # --------------------------------------------------

    assert data["hs_code"] == "853710"

    assert data["hs_description"] == "For a voltage not exceeding 1,000 V"

    assert data["period_start"] == "2025-01-01"

    assert data["period_end"] == "2025-12-31"

    # --------------------------------------------------
    # Opportunities
    # --------------------------------------------------

    opportunities = data["opportunities"]

    assert len(opportunities) == 4

    # --------------------------------------------------
    # Germany
    # --------------------------------------------------

    assert opportunities[0]["rank"] == 1
    assert opportunities[0]["country_id"] == 4
    assert opportunities[0]["country_name"] == "Germany"
    assert opportunities[0]["iso2"] == "DE"
    assert opportunities[0]["iso3"] == "DEU"
    assert opportunities[0]["trade_value_usd"] == 10_500_000

    # --------------------------------------------------
    # United States
    # --------------------------------------------------

    assert opportunities[1]["rank"] == 2
    assert opportunities[1]["country_id"] == 5
    assert opportunities[1]["country_name"] == "United States of America"
    assert opportunities[1]["iso2"] == "US"
    assert opportunities[1]["iso3"] == "USA"
    assert opportunities[1]["trade_value_usd"] == 8_200_000

    # --------------------------------------------------
    # United Arab Emirates
    # --------------------------------------------------

    assert opportunities[2]["rank"] == 3
    assert opportunities[2]["country_id"] == 3
    assert opportunities[2]["country_name"] == "United Arab Emirates"
    assert opportunities[2]["iso2"] == "AE"
    assert opportunities[2]["iso3"] == "ARE"
    assert opportunities[2]["trade_value_usd"] == 4_600_000

    # --------------------------------------------------
    # Saudi Arabia
    # --------------------------------------------------

    assert opportunities[3]["rank"] == 4
    assert opportunities[3]["country_id"] == 2
    assert opportunities[3]["country_name"] == "Saudi Arabia"
    assert opportunities[3]["iso2"] == "SA"
    assert opportunities[3]["iso3"] == "SAU"
    assert opportunities[3]["trade_value_usd"] == 2_300_000

    print("\nTrade Intelligence API supplier test passed.")

    for opportunity in opportunities:
        print(
            f"{opportunity['rank']}. "
            f"{opportunity['country_name']} "
            f"({opportunity['iso3']}) - "
            f"${opportunity['trade_value_usd']:,.2f}"
        )


# ======================================================
# GLOBAL SUPPLIER SEARCH API
# ======================================================


def test_trade_analyze_global_supplier_query():
    """
    Test:

        Find suppliers of electrical panels
    """

    response = client.post(
        "/api/v1/trade/analyze",
        json={"query": "Find suppliers of electrical panels"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["hs_code"] == "853710"

    opportunities = data["opportunities"]

    # --------------------------------------------------
    # Current synthetic dataset
    #
    # India exports = 35M
    # Germany      = 25M
    # USA          = 20M
    # UAE          = 12M
    # Saudi Arabia = 7M
    # --------------------------------------------------

    assert len(opportunities) == 5

    assert opportunities[0]["country_name"] == "India"
    assert opportunities[0]["trade_value_usd"] == 35_000_000

    assert opportunities[1]["country_name"] == "Germany"
    assert opportunities[1]["trade_value_usd"] == 25_000_000

    assert opportunities[2]["country_name"] == "United States of America"
    assert opportunities[2]["trade_value_usd"] == 20_000_000

    assert opportunities[3]["country_name"] == "United Arab Emirates"
    assert opportunities[3]["trade_value_usd"] == 12_000_000

    assert opportunities[4]["country_name"] == "Saudi Arabia"
    assert opportunities[4]["trade_value_usd"] == 7_000_000

    print("\nTrade Intelligence API global supplier test passed.")


# ======================================================
# BUYER SEARCH API
# ======================================================


def test_trade_analyze_global_buyer_query():
    """
    Test:

        Who imports electrical panels?
    """

    response = client.post(
        "/api/v1/trade/analyze",
        json={"query": "Who imports electrical panels?"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["hs_code"] == "853710"

    opportunities = data["opportunities"]

    assert len(opportunities) == 1

    assert opportunities[0]["country_name"] == "India"

    assert opportunities[0]["iso3"] == "IND"

    assert opportunities[0]["trade_value_usd"] == 25_600_000

    print("\nTrade Intelligence API global buyer test passed.")


# ======================================================
# EMPTY QUERY
# ======================================================


def test_trade_analyze_empty_query():
    """
    Empty queries should be rejected by the API.
    """

    response = client.post(
        "/api/v1/trade/analyze",
        json={"query": ""},
    )

    assert response.status_code == 400

    data = response.json()

    assert data["detail"] == "Trade query cannot be empty."

    print("\nEmpty trade query correctly rejected.")


# ======================================================
# UNKNOWN PRODUCT
# ======================================================


def test_trade_analyze_unknown_product():
    """
    Unknown products should be rejected by the API.
    """

    response = client.post(
        "/api/v1/trade/analyze",
        json={"query": "Find suppliers of solar powered bananas"},
    )

    assert response.status_code == 400

    data = response.json()

    assert "product could not be resolved" in data["detail"].lower()

    print("\nUnknown product correctly rejected through API.")

    print(f"  {data['detail']}")


# ======================================================
# SPECIFIC BUYER
# ======================================================


def test_trade_analyze_specific_buyer_query():
    """
    Test:

        Who imports electrical panels in India?
    """

    response = client.post(
        "/api/v1/trade/analyze",
        json={"query": "Who imports electrical panels in India?"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["hs_code"] == "853710"

    opportunities = data["opportunities"]

    assert len(opportunities) == 1

    assert opportunities[0]["country_name"] == "India"

    assert opportunities[0]["iso3"] == "IND"

    assert opportunities[0]["trade_value_usd"] == 25_600_000

    print("\nTrade Intelligence API specific buyer test passed.")


# ======================================================
# INDIA-ORIGIN BUYER SEARCH
# ======================================================


def test_trade_analyze_buyer_from_india_query():
    """
    Test:

        Who buys electrical panels from India?
    """

    response = client.post(
        "/api/v1/trade/analyze",
        json={"query": "Who buys electrical panels from India?"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["hs_code"] == "853710"

    opportunities = data["opportunities"]

    assert len(opportunities) == 4

    assert opportunities[0]["country_name"] == "Germany"
    assert opportunities[0]["trade_value_usd"] == 14_000_000

    assert opportunities[1]["country_name"] == "United States of America"
    assert opportunities[1]["trade_value_usd"] == 11_000_000

    assert opportunities[2]["country_name"] == "United Arab Emirates"
    assert opportunities[2]["trade_value_usd"] == 6_000_000

    assert opportunities[3]["country_name"] == "Saudi Arabia"
    assert opportunities[3]["trade_value_usd"] == 4_000_000

    print("\nTrade Intelligence API India-origin buyer test passed.")


# ======================================================
# COUNTRY COMPARISON API
# ======================================================


def test_trade_analyze_country_comparison_query():
    """
    Test a natural-language country comparison query.

    Query:

        Compare Germany and United Arab Emirates for electrical panels to India
    """

    response = client.post(
        "/api/v1/trade/analyze",
        json={
            "query": (
                "Compare Germany and United Arab Emirates "
                "for electrical panels to India"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["hs_code"] == "853710"
    assert data["hs_description"] == "For a voltage not exceeding 1,000 V"
    assert data["period_start"] == "2025-01-01"
    assert data["period_end"] == "2025-12-31"

    opportunities = data["opportunities"]

    assert len(opportunities) == 2

    assert opportunities[0]["country_id"] == 4
    assert opportunities[0]["country_name"] == "Germany"
    assert opportunities[0]["iso3"] == "DEU"
    assert opportunities[0]["trade_value_usd"] == 10_500_000

    assert opportunities[1]["country_id"] == 3
    assert opportunities[1]["country_name"] == "United Arab Emirates"
    assert opportunities[1]["iso3"] == "ARE"
    assert opportunities[1]["trade_value_usd"] == 4_600_000

    comparison = data["comparison"]

    assert comparison is not None

    assert comparison["country_a_id"] == 4
    assert comparison["country_a_name"] == "Germany"

    assert comparison["country_b_id"] == 3
    assert comparison["country_b_name"] == "United Arab Emirates"

    assert comparison["trade_value_winner"] == 4
    assert comparison["trade_value_winner_name"] == "Germany"

    assert comparison["market_share_winner"] == 4
    assert comparison["market_share_winner_name"] == "Germany"

    assert comparison["yoy_growth_winner"] == 3
    assert comparison["yoy_growth_winner_name"] == "United Arab Emirates"

    assert comparison["opportunity_score_winner"] == 4
    assert comparison["opportunity_score_winner_name"] == "Germany"

    assert comparison["overall_winner"] == 4
    assert comparison["overall_winner_name"] == "Germany"
    assert comparison["country_a_wins"] == 3
    assert comparison["country_b_wins"] == 1

    print("\nTrade Intelligence API country comparison test passed.")
    print(
        f"Compared {comparison['country_a_name']} vs " f"{comparison['country_b_name']}"
    )
    print(
        f"Overall winner: {comparison['overall_winner_name']} "
        f"(country_id={comparison['overall_winner']})"
    )


# ======================================================
# MAIN
# ======================================================


if __name__ == "__main__":

    test_trade_analyze_supplier_query()

    test_trade_analyze_global_supplier_query()

    test_trade_analyze_global_buyer_query()

    test_trade_analyze_empty_query()

    test_trade_analyze_unknown_product()

    test_trade_analyze_specific_buyer_query()

    test_trade_analyze_buyer_from_india_query()

    test_trade_analyze_country_comparison_query()
