from app.intelligence.country_matcher import CountryMatcher
from app.intelligence.hs_resolver import HSResolver
from app.intelligence.product_matcher import ProductMatcher
from app.schemas.intelligence import (
    CountryRole,
    CountryScope,
    QueryUnderstanding,
    ResolvedProduct,
    TradeIntent,
    TradeQuery,
)

COUNTRY_ALIASES = {
    # United Arab Emirates
    "uae": "United Arab Emirates",
    "u.a.e": "United Arab Emirates",
    "u.a.e.": "United Arab Emirates",
    # United States
    "usa": "United States of America",
    "u.s.a": "United States of America",
    "u.s.a.": "United States of America",
    "us": "United States of America",
    "u.s": "United States of America",
    "u.s.": "United States of America",
    # United Kingdom
    "uk": "United Kingdom",
    "u.k": "United Kingdom",
    "u.k.": "United Kingdom",
    # Saudi Arabia
    "ksa": "Saudi Arabia",
    "k.s.a": "Saudi Arabia",
    "k.s.a.": "Saudi Arabia",
}


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

    # ==================================================
    # COUNTRY NORMALIZATION
    # ==================================================

    @staticmethod
    def _normalize_country_text(
        country_text: str | None,
    ) -> str | None:
        if country_text is None:
            return None

        normalized = country_text.strip()

        if not normalized:
            return None

        alias = COUNTRY_ALIASES.get(normalized.lower())

        if alias is not None:
            return alias

        return normalized

    # ==================================================
    # BUILD TRADE QUERY
    # ==================================================

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
        # 2. Resolve primary country
        # --------------------------------------------------

        resolved_country = None

        if understanding.country_scope == CountryScope.SPECIFIC:
            normalized_country_text = self._normalize_country_text(
                understanding.country_text
            )

            if normalized_country_text:
                country_match = self.country_matcher.match(normalized_country_text)

                if country_match is not None:
                    resolved_country = country_match.country

        # --------------------------------------------------
        # 3. Resolve comparison countries
        # --------------------------------------------------

        resolved_comparison_countries = []

        for country_text in understanding.comparison_country_texts:

            normalized_country_text = self._normalize_country_text(country_text)

            if not normalized_country_text:
                continue

            country_match = self.country_matcher.match(normalized_country_text)

            if country_match is None:
                continue

            country = country_match.country

            # Avoid duplicates.
            if any(
                existing_country.id == country.id
                for existing_country in resolved_comparison_countries
            ):
                continue

            resolved_comparison_countries.append(country)

        # --------------------------------------------------
        # 4. Resolve HS codes
        # --------------------------------------------------

        hs_codes = self.hs_resolver.resolve(product)

        # --------------------------------------------------
        # 5. Normalize comparison context
        # --------------------------------------------------
        #
        # Example:
        #
        #   Compare Germany vs UAE for electrical panels
        #
        # Germany and UAE are the comparison subjects.
        # They are not necessarily the primary trade-context
        # country.
        #
        # If no destination/origin country was resolved,
        # allow TradeQuery construction so that the service
        # layer can return a meaningful business error.
        # --------------------------------------------------

        country_scope = understanding.country_scope
        country_role = understanding.country_role

        if understanding.intent == TradeIntent.COMPARISON and resolved_country is None:
            country_scope = CountryScope.ALL
            country_role = CountryRole.UNSPECIFIED

        # --------------------------------------------------
        # 6. Build final TradeQuery
        # --------------------------------------------------

        return TradeQuery(
            original_query=original_query,
            intent=understanding.intent,
            product=resolved_product,
            country_scope=country_scope,
            country_role=country_role,
            country=resolved_country,
            comparison_countries=resolved_comparison_countries,
            hs_codes=hs_codes,
        )
