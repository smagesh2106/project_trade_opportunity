from dataclasses import dataclass


@dataclass(frozen=True)
class MarketShare:
    """
    Market-share result for one country.

    country_id:
        Country represented by the trade value.

    trade_value_usd:
        Country's trade value.

    total_market_value_usd:
        Total trade value for the market.

    market_share_percent:
        Country's percentage share of the total market.
    """

    country_id: int
    trade_value_usd: float
    total_market_value_usd: float
    market_share_percent: float


def calculate_market_shares(
    trade_results: list[tuple[int, float]],
) -> list[MarketShare]:
    """
    Calculate market share for each country.

    Expected input:

        [
            (4, 10_500_000),
            (5, 8_200_000),
            (3, 4_600_000),
            (2, 2_300_000),
        ]

    The total market value is calculated from all supplied
    trade results.

    Returns results in the same order as the input.

    Raises ValueError when:

        - no trade results are supplied
        - total market value is zero
    """

    if not trade_results:
        raise ValueError("Cannot calculate market share without trade results.")

    total_market_value = sum(float(trade_value) for _, trade_value in trade_results)

    if total_market_value == 0:
        raise ValueError(
            "Cannot calculate market share when " "total market value is zero."
        )

    results: list[MarketShare] = []

    for country_id, trade_value in trade_results:

        trade_value = float(trade_value)

        market_share_percent = (trade_value / total_market_value) * 100.0

        results.append(
            MarketShare(
                country_id=country_id,
                trade_value_usd=trade_value,
                total_market_value_usd=total_market_value,
                market_share_percent=market_share_percent,
            )
        )

    return results
