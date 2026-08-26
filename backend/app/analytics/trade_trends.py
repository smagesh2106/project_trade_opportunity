from dataclasses import dataclass


@dataclass(frozen=True)
class TradeTrend:
    """
    Year-over-year trade trend.

    previous_year:
        The earlier year used as the comparison baseline.

    current_year:
        The latest year.

    previous_value_usd:
        Trade value in the previous year.

    current_value_usd:
        Trade value in the current year.

    yoy_growth_percent:
        Percentage change from previous year to current year.

        Example:

            previous = 21.3M
            current  = 25.6M

            growth = ((25.6 - 21.3) / 21.3) * 100
                   = 20.19%
    """

    previous_year: int
    current_year: int

    previous_value_usd: float
    current_value_usd: float

    yoy_growth_percent: float


def calculate_yoy_growth(
    trade_history: list[tuple[int, float]],
) -> TradeTrend | None:
    """
    Calculate YoY growth using the two most recent years.

    Expected input:

        [
            (2024, 21_300_000),
            (2025, 25_600_000),
        ]

    Returns:

        TradeTrend(
            previous_year=2024,
            current_year=2025,
            previous_value_usd=21_300_000,
            current_value_usd=25_600_000,
            yoy_growth_percent=20.187793...
        )

    Returns None when fewer than two years are available.

    If the previous year's value is zero, YoY growth cannot
    be calculated as a percentage. In that case this function
    raises ValueError rather than returning an infinite value.
    """

    if len(trade_history) < 2:
        return None

    # --------------------------------------------------
    # Sort defensively by year.
    #
    # The repository already returns chronological data,
    # but keeping this function independent of that detail
    # makes it safer to reuse.
    # --------------------------------------------------

    ordered_history = sorted(
        trade_history,
        key=lambda item: item[0],
    )

    previous_year, previous_value = ordered_history[-2]
    current_year, current_value = ordered_history[-1]

    previous_value = float(previous_value)
    current_value = float(current_value)

    # --------------------------------------------------
    # Avoid division by zero.
    # --------------------------------------------------

    if previous_value == 0:
        raise ValueError(
            "Cannot calculate YoY growth when "
            "the previous year's trade value is zero."
        )

    yoy_growth_percent = ((current_value - previous_value) / previous_value) * 100.0

    return TradeTrend(
        previous_year=previous_year,
        current_year=current_year,
        previous_value_usd=previous_value,
        current_value_usd=current_value,
        yoy_growth_percent=yoy_growth_percent,
    )
