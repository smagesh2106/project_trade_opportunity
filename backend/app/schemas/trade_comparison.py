from pydantic import BaseModel


class TradeComparisonResponse(BaseModel):
    """
    API representation of a deterministic comparison
    between two trade opportunities.
    """

    country_a_id: int
    country_a_name: str

    country_b_id: int
    country_b_name: str

    trade_value_winner: int | None = None
    trade_value_winner_name: str | None = None

    market_share_winner: int | None = None
    market_share_winner_name: str | None = None

    yoy_growth_winner: int | None = None
    yoy_growth_winner_name: str | None = None

    opportunity_score_winner: int | None = None
    opportunity_score_winner_name: str | None = None

    overall_winner: int | None = None
    overall_winner_name: str | None = None

    country_a_wins: int
    country_b_wins: int
