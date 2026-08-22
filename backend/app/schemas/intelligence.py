from enum import Enum

from pydantic import BaseModel, Field


class CountryScope(str, Enum):
    ALL = "all"
    SPECIFIC = "specific"


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

    country_scope: CountryScope = Field(
        description=(
            "Whether the query applies to all countries or " "a specific country."
        )
    )


class ResolvedProduct(BaseModel):
    id: int
    name: str
    confidence: float


class ProductMatch(BaseModel):
    product: ResolvedProduct
    match_type: str


class ResolvedCountry(BaseModel):
    id: int
    iso2: str
    iso3: str
    name: str
    confidence: float


class CountryMatch(BaseModel):
    country: ResolvedCountry
    match_type: str


class ResolvedHSCode(BaseModel):
    id: int
    code: str
    description: str
    level: int
    confidence: float
    mapping_type: str | None = None
    source: str | None = None


from pydantic import BaseModel, Field, model_validator


class TradeQuery(BaseModel):
    original_query: str
    intent: TradeIntent
    product: ResolvedProduct | None = None
    country_scope: CountryScope
    country: ResolvedCountry | None = None
    hs_codes: list[ResolvedHSCode] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_country_scope(self):
        if self.country_scope == CountryScope.ALL and self.country is not None:
            raise ValueError("country must be None when country_scope is ALL")

        if self.country_scope == CountryScope.SPECIFIC and self.country is None:
            raise ValueError("country is required when country_scope is SPECIFIC")

        return self
