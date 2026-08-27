from dataclasses import dataclass

from app.analytics.trade_trends import TradeTrend, calculate_yoy_growth


@dataclass(frozen=True)
class MarketTrend:
    """
    Historical market trend for a product/country scope.

    trade_history:
        Yearly trade values in chronological order.

    yoy_growth:
        YoY comparison between the two most recent years.
        None when fewer than two years are available.
    """

    trade_history: list[tuple[int, float]]
    yoy_growth: TradeTrend | None


def calculate_market_trend(
    trade_history: list[tuple[int, float]],
) -> MarketTrend:
    """
    Calculate a market trend from yearly trade history.

    Expected input:

        [
            (2024, 21_300_000),
            (2025, 25_600_000),
        ]

    Returns:

        MarketTrend(
            trade_history=[
                (2024, 21_300_000),
                (2025, 25_600_000),
            ],
            yoy_growth=TradeTrend(...),
        )

    The history is sorted chronologically before being returned.

    When fewer than two years are available, yoy_growth is None.

    A ValueError is raised when the previous year's value is zero,
    because YoY percentage growth cannot be calculated.
    """

    if not trade_history:
        raise ValueError("Cannot calculate market trend without trade history.")

    ordered_history = sorted(
        (
            int(year),
            float(trade_value),
        )
        for year, trade_value in trade_history
    )

    yoy_growth = calculate_yoy_growth(ordered_history)

    return MarketTrend(
        trade_history=ordered_history,
        yoy_growth=yoy_growth,
    )
