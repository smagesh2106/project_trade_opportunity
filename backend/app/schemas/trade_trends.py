from pydantic import BaseModel


class MarketTrendPoint(BaseModel):
    year: int
    trade_value_usd: float


class MarketTrendResponse(BaseModel):
    hs_code: str
    hs_description: str

    country_id: int | None = None
    country_name: str | None = None
    iso2: str | None = None
    iso3: str | None = None

    trade_flow: str

    history: list[MarketTrendPoint]

    yoy_growth_percent: float | None = None
