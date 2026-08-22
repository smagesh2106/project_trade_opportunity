from enum import Enum

from pydantic import BaseModel, Field


class TradeIntent(str, Enum):
    SUPPLIER_SEARCH = "supplier_search"
    BUYER_SEARCH = "buyer_search"
    EXPORT_OPPORTUNITY = "export_opportunity"
    IMPORT_OPPORTUNITY = "import_opportunity"
    MARKET_ANALYSIS = "market_analysis"
    PRODUCT_SEARCH = "product_search"
    UNKNOWN = "unknown"


class QueryUnderstanding(BaseModel):
    intent: TradeIntent = Field(description=("The user's trade-related intent."))

    product_text: str | None = Field(
        default=None,
        description=("The product or product description mentioned " "by the user."),
    )

    country_text: str | None = Field(
        default=None,
        description=("The country mentioned by the user."),
    )


class ResolvedProduct(BaseModel):
    id: int
    name: str
    confidence: float


class ResolvedCountry(BaseModel):
    id: int
    iso2: str
    iso3: str
    name: str
    confidence: float


class ResolvedHSCode(BaseModel):
    id: int
    code: str
    description: str
    confidence: float


class TradeQuery(BaseModel):
    original_query: str
    intent: TradeIntent
    product: ResolvedProduct | None = None
    country: ResolvedCountry | None = None
    hs_codes: list[ResolvedHSCode] = Field(default_factory=list)
