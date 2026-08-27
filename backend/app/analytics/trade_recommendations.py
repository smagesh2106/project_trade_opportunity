from dataclasses import dataclass


@dataclass(frozen=True)
class TradeRecommendation:
    """
    Deterministic business recommendation generated
    from trade opportunity analytics.

    Fields:

        priority:
            Recommendation priority.

        recommendation_type:
            Type of recommendation.

        country_id:
            Country associated with the recommendation.

        title:
            Short business-oriented recommendation title.

        rationale:
            Explanation of why the recommendation was generated.

        action:
            Suggested next business action.
    """

    priority: str
    recommendation_type: str
    country_id: int
    title: str
    rationale: str
    action: str


def _primary_title(
    country_name: str,
    intent: str,
) -> str:

    if intent == "export_opportunity":
        return f"Prioritize {country_name} as an export market"

    if intent == "import_opportunity":
        return f"Prioritize {country_name} as a source from country"

    if intent == "supplier_search":
        return f"Prioritize {country_name} as a supplier"

    if intent == "buyer_search":
        return f"Prioritize {country_name} as a buyer market"

    return f"Prioritize {country_name}"


def _primary_action(
    country_name: str,
    intent: str,
) -> str:

    if intent == "export_opportunity":
        return (
            f"Evaluate {country_name} first as an export market, "
            "including pricing, supplier/buyer qualification, "
            "and commercial feasibility."
        )

    if intent == "import_opportunity":
        return (
            f"Evaluate {country_name} first as a source from country, "
            "including pricing, supplier qualification, quality, "
            "logistics, and commercial feasibility."
        )

    if intent == "supplier_search":
        return (
            f"Evaluate suppliers in {country_name}, "
            "including pricing, qualification, capacity, quality, "
            "and commercial feasibility."
        )

    if intent == "buyer_search":
        return (
            f"Evaluate {country_name} as a target buyer market, "
            "including demand, customer qualification, pricing, "
            "and commercial feasibility."
        )

    return (
        f"Evaluate {country_name} first based on the available "
        "trade opportunity indicators."
    )


def _emerging_title(
    country_name: str,
    intent: str,
) -> str:

    if intent == "import_opportunity":
        return f"Keep {country_name} as an " "emerging sourcing alternative"

    if intent == "export_opportunity":
        return f"Keep {country_name} as an " "emerging alternative"

    if intent == "supplier_search":
        return f"Keep {country_name} as an " "emerging supplier alternative"

    if intent == "buyer_search":
        return f"Keep {country_name} as an " "emerging buyer market"

    return f"Keep {country_name} as an emerging alternative"


def _emerging_action(
    country_name: str,
    intent: str,
) -> str:

    if intent == "import_opportunity":
        return (
            f"Track {country_name} closely and evaluate it " "as an alternative source."
        )

    if intent == "export_opportunity":
        return (
            f"Track {country_name} closely and evaluate it "
            "as an alternative export market."
        )

    if intent == "supplier_search":
        return (
            f"Track suppliers in {country_name} closely and "
            "evaluate them as an alternative source."
        )

    if intent == "buyer_search":
        return (
            f"Track demand in {country_name} closely and "
            "evaluate it as an alternative buyer market."
        )

    return f"Track {country_name} closely and evaluate it " "as an alternative market."


def generate_trade_recommendations(
    opportunities: list[dict],
    intent: str,
) -> list[TradeRecommendation]:
    """
    Generate deterministic business recommendations.

    Expected opportunity fields:

        country_id
        country_name
        iso2
        iso3
        trade_value_usd
        market_share_percent
        yoy_growth_percent
        opportunity_score

    Recommendation logic:

        1. Highest opportunity score becomes the primary
           recommendation.

        2. A lower-share, high-growth country becomes an
           emerging alternative.

    Supported intents:

        export_opportunity
        import_opportunity
        supplier_search
        buyer_search
    """

    if not opportunities:
        return []

    # ==================================================
    # PRIMARY TARGET
    # ==================================================

    score_candidates = [
        opportunity
        for opportunity in opportunities
        if opportunity.get("opportunity_score") is not None
    ]

    if not score_candidates:
        return []

    primary = max(
        score_candidates,
        key=lambda opportunity: float(
            opportunity.get(
                "opportunity_score",
                0.0,
            )
        ),
    )

    primary_country_name = primary.get(
        "country_name",
        "Unknown country",
    )

    primary_score = float(
        primary.get(
            "opportunity_score",
            0.0,
        )
    )

    primary_growth = primary.get("yoy_growth_percent")

    primary_market_share = primary.get("market_share_percent")

    rationale_parts = [
        f"{primary_country_name} has the highest "
        f"opportunity score at {primary_score:.2f}"
    ]

    if primary_growth is not None:
        rationale_parts.append(f"YoY growth is {float(primary_growth):.2f}%")

    if primary_market_share is not None:
        rationale_parts.append(f"market share is {float(primary_market_share):.2f}%")

    recommendations = [
        TradeRecommendation(
            priority="high",
            recommendation_type="primary_target",
            country_id=primary["country_id"],
            title=_primary_title(
                country_name=primary_country_name,
                intent=intent,
            ),
            rationale="; ".join(rationale_parts) + ".",
            action=_primary_action(
                country_name=primary_country_name,
                intent=intent,
            ),
        )
    ]

    # ==================================================
    # EMERGING ALTERNATIVE
    # ==================================================

    growth_candidates = [
        opportunity
        for opportunity in opportunities
        if opportunity.get("yoy_growth_percent") is not None
        and opportunity.get("market_share_percent") is not None
        and opportunity["country_id"] != primary["country_id"]
    ]

    if not growth_candidates:
        return recommendations

    average_market_share = sum(
        float(
            opportunity.get(
                "market_share_percent",
                0.0,
            )
        )
        for opportunity in opportunities
    ) / len(opportunities)

    emerging_candidates = [
        opportunity
        for opportunity in growth_candidates
        if float(
            opportunity.get(
                "market_share_percent",
                0.0,
            )
        )
        < average_market_share
    ]

    if not emerging_candidates:
        return recommendations

    emerging = max(
        emerging_candidates,
        key=lambda opportunity: float(
            opportunity.get(
                "yoy_growth_percent",
                0.0,
            )
        ),
    )

    emerging_country_name = emerging.get(
        "country_name",
        "Unknown country",
    )

    emerging_market_share = float(
        emerging.get(
            "market_share_percent",
            0.0,
        )
    )

    emerging_growth = float(
        emerging.get(
            "yoy_growth_percent",
            0.0,
        )
    )

    recommendations.append(
        TradeRecommendation(
            priority="medium",
            recommendation_type="emerging_alternative",
            country_id=emerging["country_id"],
            title=_emerging_title(
                country_name=emerging_country_name,
                intent=intent,
            ),
            rationale=(
                f"{emerging_country_name} has a relatively lower "
                f"market share of {emerging_market_share:.2f}% "
                f"but is growing at {emerging_growth:.2f}% YoY."
            ),
            action=_emerging_action(
                country_name=emerging_country_name,
                intent=intent,
            ),
        )
    )

    return recommendations
