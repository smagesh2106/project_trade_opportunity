from dataclasses import dataclass


@dataclass(frozen=True)
class OpportunityScore:
    """
    Composite trade opportunity score.

    All component scores are normalized to 0-100.

    The final opportunity score is also 0-100.

    Components:

        demand_score:
            Measures relative trade demand.

        growth_score:
            Measures relative YoY growth.

        market_share_score:
            Measures relative market share.

        concentration_score:
            Measures supplier concentration.

        total_score:
            Weighted composite score.
    """

    demand_score: float
    growth_score: float
    market_share_score: float
    concentration_score: float
    total_score: float


def _normalize(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Normalize a value to a 0-100 scale.

    When all values are equal, return 100 because the
    supplied value represents the maximum available
    opportunity within that comparison set.
    """

    if maximum == minimum:
        return 100.0

    score = ((value - minimum) / (maximum - minimum)) * 100.0

    return max(
        0.0,
        min(100.0, score),
    )


def calculate_opportunity_score(
    trade_value_usd: float,
    all_trade_values_usd: list[float],
    yoy_growth_percent: float,
    all_yoy_growth_percent: list[float],
    market_share_percent: float,
    all_market_share_percent: list[float],
    concentration_percent: float,
    concentration_min_percent: float,
    concentration_max_percent: float,
) -> OpportunityScore:
    """
    Calculate a first-version trade opportunity score.

    Weighting:

        Demand / trade value       40%
        YoY growth                 30%
        Market share              15%
        Supplier concentration    15%

    Why these weights?

        Demand is the strongest indication that a market
        is commercially significant.

        Growth indicates whether the market is expanding.

        Market share provides a measure of the current
        position in the market.

        Supplier concentration provides an indication of
        how dependent the market is on a limited supplier
        base.

    Important:

        This is a deterministic v1 scoring model.

        It is deliberately transparent so that we can
        validate the business logic before introducing
        more sophisticated scoring.
    """

    if not all_trade_values_usd:
        raise ValueError("Trade values are required for " "opportunity scoring.")

    if not all_yoy_growth_percent:
        raise ValueError("YoY growth values are required for " "opportunity scoring.")

    if not all_market_share_percent:
        raise ValueError("Market share values are required for " "opportunity scoring.")

    # --------------------------------------------------
    # Demand
    # --------------------------------------------------

    demand_score = _normalize(
        float(trade_value_usd),
        min(float(value) for value in all_trade_values_usd),
        max(float(value) for value in all_trade_values_usd),
    )

    # --------------------------------------------------
    # Growth
    # --------------------------------------------------

    growth_score = _normalize(
        float(yoy_growth_percent),
        min(float(value) for value in all_yoy_growth_percent),
        max(float(value) for value in all_yoy_growth_percent),
    )

    # --------------------------------------------------
    # Market share
    #
    # Higher existing share receives a higher score in
    # this first version because it represents an
    # established trade relationship.
    #
    # We will later distinguish between:
    #
    #   existing position
    #   market whitespace
    #
    # when real supplier/company data is available.
    # --------------------------------------------------

    market_share_score = _normalize(
        float(market_share_percent),
        min(float(value) for value in all_market_share_percent),
        max(float(value) for value in all_market_share_percent),
    )

    # --------------------------------------------------
    # Supplier concentration
    #
    # Higher concentration receives a higher score.
    #
    # The interpretation is:
    #
    #   concentrated supplier base
    #       →
    #   potential opportunity for an alternative supplier
    #
    # This is a market-level opportunity signal rather
    # than proof that a new supplier can win the market.
    # --------------------------------------------------

    concentration_score = _normalize(
        float(concentration_percent),
        float(concentration_min_percent),
        float(concentration_max_percent),
    )

    # --------------------------------------------------
    # Weighted composite
    # --------------------------------------------------

    total_score = (
        (demand_score * 0.40)
        + (growth_score * 0.30)
        + (market_share_score * 0.15)
        + (concentration_score * 0.15)
    )

    return OpportunityScore(
        demand_score=round(
            demand_score,
            2,
        ),
        growth_score=round(
            growth_score,
            2,
        ),
        market_share_score=round(
            market_share_score,
            2,
        ),
        concentration_score=round(
            concentration_score,
            2,
        ),
        total_score=round(
            total_score,
            2,
        ),
    )
