from app.intelligence.country_matcher import CountryMatcher
from app.intelligence.hs_resolver import HSResolver
from app.intelligence.product_matcher import ProductMatcher
from app.schemas.intelligence import (
    CountryScope,
    CountryRole,
    QueryUnderstanding,
    ResolvedProduct,
    TradeQuery,
)


class TradeQueryBuilder:
    def __init__(
        self,
        product_matcher: ProductMatcher,
        country_matcher: CountryMatcher,
        hs_resolver: HSResolver,
    ):
        self.product_matcher = product_matcher
        self.country_matcher = country_matcher
        self.hs_resolver = hs_resolver

    def build(
        self,
        original_query: str,
        understanding: QueryUnderstanding,
    ) -> TradeQuery:

        # --------------------------------------------------
        # 1. Resolve product
        # --------------------------------------------------

        product = self.product_matcher.find(understanding.product_text)

        resolved_product = None

        if product is not None:
            resolved_product = ResolvedProduct(
                id=product.id,
                name=product.name,
                confidence=1.0,
            )

        # --------------------------------------------------
        # 2. Resolve country
        # --------------------------------------------------

        resolved_country = None
        resolved_comparison_countries = []

        if understanding.country_scope == CountryScope.SPECIFIC:
            if understanding.country_text:
                country_match = self.country_matcher.match(understanding.country_text)

                if country_match is not None:
                    resolved_country = country_match.country

        for country_text in understanding.comparison_country_texts:
            if not country_text:
                continue

            country_match = self.country_matcher.match(country_text)

            if country_match is not None:
                resolved_comparison_countries.append(country_match.country)

        # --------------------------------------------------
        # 3. Resolve HS codes
        # --------------------------------------------------

        hs_codes = self.hs_resolver.resolve(product)

        # --------------------------------------------------
        # 4. Build final TradeQuery
        # --------------------------------------------------

        return TradeQuery(
            original_query=original_query,
            intent=understanding.intent,
            product=resolved_product,
            country_scope=understanding.country_scope,
            country_role=understanding.country_role,
            country=resolved_country,
            comparison_countries=resolved_comparison_countries,
            hs_codes=hs_codes,
        )
