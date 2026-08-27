from enum import Enum

from pydantic import BaseModel, Field, model_validator


class CountryScope(str, Enum):
    ALL = "all"
    SPECIFIC = "specific"


class CountryRole(str, Enum):
    LOCATION = "location"
    DESTINATION = "destination"
    ORIGIN = "origin"
    UNSPECIFIED = "unspecified"


class TradeIntent(str, Enum):
    SUPPLIER_SEARCH = "supplier_search"
    BUYER_SEARCH = "buyer_search"
    EXPORT_OPPORTUNITY = "export_opportunity"
    IMPORT_OPPORTUNITY = "import_opportunity"
    MARKET_ANALYSIS = "market_analysis"
    COMPARISON = "comparison"
    PRODUCT_SEARCH = "product_search"
    UNKNOWN = "unknown"


class QueryUnderstanding(BaseModel):
    intent: TradeIntent = Field(description="The user's trade-related intent.")

    product_text: str | None = Field(
        default=None,
        description=("The product or product description mentioned " "by the user."),
    )

    country_text: str | None = Field(
        default=None,
        description=(
            "The primary country mentioned by the user, such as a "
            "destination or origin country."
        ),
    )

    comparison_country_texts: list[str] = Field(
        default_factory=list,
        description=("Countries explicitly named as the subjects of a comparison."),
    )

    country_scope: CountryScope = Field(
        description=(
            "Whether the query applies to all countries " "or a specific country."
        )
    )

    country_role: CountryRole = Field(
        description=(
            "The role of the mentioned country in the "
            "trade query. Use 'location' when the country "
            "is where suppliers or buyers are located, "
            "'destination' when goods are going to the "
            "country, 'origin' when goods are coming from "
            "the country, and 'unspecified' when no country "
            "is mentioned."
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


class TradeQuery(BaseModel):
    original_query: str
    intent: TradeIntent
    product: ResolvedProduct | None = None

    country_scope: CountryScope
    country_role: CountryRole

    country: ResolvedCountry | None = None

    comparison_countries: list[ResolvedCountry] = Field(default_factory=list)

    hs_codes: list[ResolvedHSCode] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_country_scope(self):
        # --------------------------------------------------
        # ALL means there is no specific country.
        # --------------------------------------------------

        if self.country_scope == CountryScope.ALL and self.country is not None:
            raise ValueError("country must be None when " "country_scope is ALL")

        # --------------------------------------------------
        # SPECIFIC requires a resolved country.
        # --------------------------------------------------

        if self.country_scope == CountryScope.SPECIFIC and self.country is None:
            raise ValueError("country is required when " "country_scope is SPECIFIC")

        # --------------------------------------------------
        # ALL queries must not claim a specific country role.
        # --------------------------------------------------

        if (
            self.country_scope == CountryScope.ALL
            and self.country_role != CountryRole.UNSPECIFIED
        ):
            raise ValueError(
                "country_role must be UNSPECIFIED " "when country_scope is ALL"
            )

        # --------------------------------------------------
        # SPECIFIC queries should have a meaningful role.
        # --------------------------------------------------

        if (
            self.country_scope == CountryScope.SPECIFIC
            and self.country_role == CountryRole.UNSPECIFIED
        ):
            raise ValueError(
                "country_role must be specified when " "country_scope is SPECIFIC"
            )

        if self.intent == TradeIntent.COMPARISON:
            if len(self.comparison_countries) != 2:
                raise ValueError("comparison requires exactly two comparison countries")

            comparison_ids = [country.id for country in self.comparison_countries]
            if len(set(comparison_ids)) != 2:
                raise ValueError("comparison countries must be distinct")

        return self
