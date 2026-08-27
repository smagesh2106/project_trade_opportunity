from dataclasses import dataclass


@dataclass(frozen=True)
class TradeComparison:
    """
    Deterministic comparison between two trade opportunities.

    The comparison identifies which country performs better
    for each available trade metric.

    Metrics:

        trade_value:
            Higher trade value wins.

        market_share:
            Higher market share wins.

        yoy_growth:
            Higher YoY growth wins.

        opportunity_score:
            Higher opportunity score wins.

        overall:
            Country with the greater number of metric wins.

    Ties are represented as None for that metric.
    """

    country_a_id: int
    country_a_name: str

    country_b_id: int
    country_b_name: str

    trade_value_winner: int | None
    market_share_winner: int | None
    yoy_growth_winner: int | None
    opportunity_score_winner: int | None

    overall_winner: int | None

    country_a_wins: int
    country_b_wins: int


def _compare_values(
    country_a_id: int,
    country_a_value: float | None,
    country_b_id: int,
    country_b_value: float | None,
) -> int | None:
    """
    Compare two metric values.

    Returns:

        country_a_id
            when country A has the higher value.

        country_b_id
            when country B has the higher value.

        None
            when the values are equal or either value is unavailable.
    """

    if country_a_value is None or country_b_value is None:
        return None

    country_a_value = float(country_a_value)
    country_b_value = float(country_b_value)

    if country_a_value > country_b_value:
        return country_a_id

    if country_b_value > country_a_value:
        return country_b_id

    return None


def compare_trade_opportunities(
    country_a: dict,
    country_b: dict,
) -> TradeComparison:
    """
    Compare two trade opportunities.

    Expected input:

        {
            "country_id": 4,
            "country_name": "Germany",
            "trade_value_usd": 10_500_000,
            "market_share_percent": 41.02,
            "yoy_growth_percent": 16.67,
            "opportunity_score": 70.00,
        }

    and:

        {
            "country_id": 3,
            "country_name": "United Arab Emirates",
            "trade_value_usd": 4_600_000,
            "market_share_percent": 17.97,
            "yoy_growth_percent": 31.43,
            "opportunity_score": 60.43,
        }

    Returns a deterministic comparison based on four metrics.

    The overall winner is the country with the greater
    number of metric wins.

    If both countries have the same number of wins,
    overall_winner is None.
    """

    country_a_id = int(country_a["country_id"])
    country_b_id = int(country_b["country_id"])

    country_a_name = str(country_a["country_name"])
    country_b_name = str(country_b["country_name"])

    trade_value_winner = _compare_values(
        country_a_id=country_a_id,
        country_a_value=country_a.get("trade_value_usd"),
        country_b_id=country_b_id,
        country_b_value=country_b.get("trade_value_usd"),
    )

    market_share_winner = _compare_values(
        country_a_id=country_a_id,
        country_a_value=country_a.get("market_share_percent"),
        country_b_id=country_b_id,
        country_b_value=country_b.get("market_share_percent"),
    )

    yoy_growth_winner = _compare_values(
        country_a_id=country_a_id,
        country_a_value=country_a.get("yoy_growth_percent"),
        country_b_id=country_b_id,
        country_b_value=country_b.get("yoy_growth_percent"),
    )

    opportunity_score_winner = _compare_values(
        country_a_id=country_a_id,
        country_a_value=country_a.get("opportunity_score"),
        country_b_id=country_b_id,
        country_b_value=country_b.get("opportunity_score"),
    )

    winners = [
        trade_value_winner,
        market_share_winner,
        yoy_growth_winner,
        opportunity_score_winner,
    ]

    country_a_wins = sum(winner == country_a_id for winner in winners)

    country_b_wins = sum(winner == country_b_id for winner in winners)

    if country_a_wins > country_b_wins:
        overall_winner = country_a_id

    elif country_b_wins > country_a_wins:
        overall_winner = country_b_id

    else:
        overall_winner = None

    return TradeComparison(
        country_a_id=country_a_id,
        country_a_name=country_a_name,
        country_b_id=country_b_id,
        country_b_name=country_b_name,
        trade_value_winner=trade_value_winner,
        market_share_winner=market_share_winner,
        yoy_growth_winner=yoy_growth_winner,
        opportunity_score_winner=opportunity_score_winner,
        overall_winner=overall_winner,
        country_a_wins=country_a_wins,
        country_b_wins=country_b_wins,
    )
