from pydantic import BaseModel


class TradeRecommendation(BaseModel):
    """
    A deterministic, query-driven business recommendation.
    """

    recommendation_type: str
    priority: str

    country_id: int | None = None
    country_name: str | None = None
    iso2: str | None = None
    iso3: str | None = None

    title: str
    rationale: str
    action: str
