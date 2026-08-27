from dataclasses import dataclass


@dataclass(frozen=True)
class TradeInsight:
    """
    Deterministic business insight generated from
    trade opportunity analytics.
    """

    insight_type: str

    country_id: int | None

    title: str

    description: str


def generate_trade_insights(
    opportunities: list[dict],
) -> list[TradeInsight]:
    """
    Generate deterministic business insights from
    trade opportunity results.

    Expected opportunity fields:

        country_id
        country_name
        iso2
        iso3
        trade_value_usd
        market_share_percent
        yoy_growth_percent
        opportunity_score

    The first version identifies:

        1. Market leader
        2. Fastest growing country
        3. Highest opportunity score
        4. High-growth / lower-share country
        5. Market concentration

    No LLM is used.

    The function is intentionally deterministic so that
    the business logic can be tested independently.
    """

    if not opportunities:
        return []

    insights: list[TradeInsight] = []

    # ==================================================
    # MARKET LEADER
    # ==================================================

    market_leader = max(
        opportunities,
        key=lambda item: float(item.get("market_share_percent", 0.0)),
    )

    leader_share = float(
        market_leader.get(
            "market_share_percent",
            0.0,
        )
    )

    insights.append(
        TradeInsight(
            insight_type="market_leader",
            country_id=market_leader.get("country_id"),
            title=(f"{market_leader.get('country_name')} " "is the market leader"),
            description=(
                f"{market_leader.get('country_name')} "
                f"has the highest market share at "
                f"{leader_share:.2f}%."
            ),
        )
    )

    # ==================================================
    # FASTEST GROWING
    # ==================================================

    growth_candidates = [
        item for item in opportunities if item.get("yoy_growth_percent") is not None
    ]

    if growth_candidates:

        fastest_growing = max(
            growth_candidates,
            key=lambda item: float(
                item.get(
                    "yoy_growth_percent",
                    0.0,
                )
            ),
        )

        growth = float(
            fastest_growing.get(
                "yoy_growth_percent",
                0.0,
            )
        )

        insights.append(
            TradeInsight(
                insight_type="fastest_growth",
                country_id=fastest_growing.get("country_id"),
                title=(
                    f"{fastest_growing.get('country_name')} " "has the fastest growth"
                ),
                description=(
                    f"{fastest_growing.get('country_name')} "
                    f"has the highest YoY growth at "
                    f"{growth:.2f}%."
                ),
            )
        )

    # ==================================================
    # HIGHEST OPPORTUNITY SCORE
    # ==================================================

    score_candidates = [
        item for item in opportunities if item.get("opportunity_score") is not None
    ]

    if score_candidates:

        highest_score = max(
            score_candidates,
            key=lambda item: float(
                item.get(
                    "opportunity_score",
                    0.0,
                )
            ),
        )

        score = float(
            highest_score.get(
                "opportunity_score",
                0.0,
            )
        )

        insights.append(
            TradeInsight(
                insight_type="highest_opportunity_score",
                country_id=highest_score.get("country_id"),
                title=(
                    f"{highest_score.get('country_name')} "
                    "has the highest opportunity score"
                ),
                description=(
                    f"{highest_score.get('country_name')} "
                    f"has an opportunity score of "
                    f"{score:.2f}."
                ),
            )
        )

    # ==================================================
    # HIGH GROWTH / LOWER SHARE
    # ==================================================

    if growth_candidates:

        average_market_share = sum(
            float(
                item.get(
                    "market_share_percent",
                    0.0,
                )
            )
            for item in opportunities
        ) / len(opportunities)

        high_growth_candidates = [
            item
            for item in growth_candidates
            if float(
                item.get(
                    "market_share_percent",
                    0.0,
                )
            )
            < average_market_share
        ]

        if high_growth_candidates:

            emerging = max(
                high_growth_candidates,
                key=lambda item: float(
                    item.get(
                        "yoy_growth_percent",
                        0.0,
                    )
                ),
            )

            emerging_growth = float(
                emerging.get(
                    "yoy_growth_percent",
                    0.0,
                )
            )

            emerging_share = float(
                emerging.get(
                    "market_share_percent",
                    0.0,
                )
            )

            insights.append(
                TradeInsight(
                    insight_type="emerging_supplier",
                    country_id=emerging.get("country_id"),
                    title=(
                        f"{emerging.get('country_name')} " "shows emerging momentum"
                    ),
                    description=(
                        f"{emerging.get('country_name')} "
                        f"has {emerging_share:.2f}% "
                        f"market share but is growing at "
                        f"{emerging_growth:.2f}% YoY."
                    ),
                )
            )

    # ==================================================
    # MARKET CONCENTRATION
    # ==================================================

    shares = sorted(
        (
            float(
                item.get(
                    "market_share_percent",
                    0.0,
                )
            )
            for item in opportunities
        ),
        reverse=True,
    )

    if len(shares) >= 2:

        top_two_share = shares[0] + shares[1]

        insights.append(
            TradeInsight(
                insight_type="market_concentration",
                country_id=None,
                title="Market concentration",
                description=(
                    f"The two largest suppliers account for "
                    f"{top_two_share:.2f}% of the market."
                ),
            )
        )

    return insights
