from pydantic import BaseModel


class TradeInsight(BaseModel):
    """
    A single deterministic business insight.
    """

    insight_type: str
    country_id: int | None = None
    country_name: str | None = None
    iso2: str | None = None
    iso3: str | None = None

    title: str
    description: str


class TradeInsightResponse(BaseModel):
    """
    Collection of deterministic trade insights.
    """

    insights: list[TradeInsight]
