from datetime import date

from pydantic import BaseModel, Field

from app.schemas.trade_insight import TradeInsight
from app.schemas.trade_recommendation import TradeRecommendation


class TradeOpportunity(BaseModel):
    rank: int

    country_id: int
    country_name: str
    iso2: str
    iso3: str

    trade_value_usd: float

    market_share_percent: float | None = None
    yoy_growth_percent: float | None = None
    opportunity_score: float | None = None

    period_start: date
    period_end: date | None = None


class TradeOpportunityResponse(BaseModel):
    hs_code: str
    hs_description: str

    period_start: date
    period_end: date | None = None

    opportunities: list[TradeOpportunity]
    insights: list[TradeInsight] = Field(default_factory=list)
    recommendations: list[TradeRecommendation] = Field(default_factory=list)
