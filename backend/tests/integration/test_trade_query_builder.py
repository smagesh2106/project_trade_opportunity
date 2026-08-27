from app.db.session import SessionLocal
from app.intelligence.country_matcher import CountryMatcher
from app.intelligence.hs_resolver import HSResolver
from app.intelligence.product_matcher import ProductMatcher
from app.intelligence.trade_query_builder import TradeQueryBuilder
from app.repositories.country import CountryRepository
from app.repositories.product import ProductRepository
from app.schemas.intelligence import (
    CountryRole,
    CountryScope,
    QueryUnderstanding,
    TradeIntent,
)


def create_builder(db):
    product_repository = ProductRepository(db)
    country_repository = CountryRepository(db)

    product_matcher = ProductMatcher(product_repository)

    country_matcher = CountryMatcher(country_repository)

    hs_resolver = HSResolver()

    return TradeQueryBuilder(
        product_matcher=product_matcher,
        country_matcher=country_matcher,
        hs_resolver=hs_resolver,
    )


def test_trade_query_specific_country():
    db = SessionLocal()

    try:
        builder = create_builder(db)

        understanding = QueryUnderstanding(
            intent=TradeIntent.SUPPLIER_SEARCH,
            product_text="electrical panels",
            country_text="India",
            country_scope=CountryScope.SPECIFIC,
            country_role=CountryRole.LOCATION,
        )

        result = builder.build(
            original_query=(
                "I'm looking for suppliers of " "electrical panels in India."
            ),
            understanding=understanding,
        )

        assert result.intent == TradeIntent.SUPPLIER_SEARCH

        assert result.product is not None
        assert result.product.id == 1
        assert result.product.name == ("Electrical Control Panels")
        assert result.product.confidence == 1.0

        assert result.country_scope == CountryScope.SPECIFIC
        assert result.country_role == CountryRole.LOCATION

        assert result.country is not None
        assert result.country.name == "India"
        assert result.country.iso2 == "IN"

        assert len(result.hs_codes) == 1
        assert result.hs_codes[0].code == "853710"
        assert result.hs_codes[0].confidence == 0.95

        print("Intent:", result.intent.value)
        print("Product:", result.product.name)
        print("Product confidence:", result.product.confidence)
        print("Country scope:", result.country_scope.value)
        print("Country:", result.country.name)
        print("HS code:", result.hs_codes[0].code)
        print("HS confidence:", result.hs_codes[0].confidence)

    finally:
        db.close()


def test_trade_query_all_countries():
    db = SessionLocal()

    try:
        builder = create_builder(db)

        understanding = QueryUnderstanding(
            intent=TradeIntent.SUPPLIER_SEARCH,
            product_text="electrical panels",
            country_text=None,
            country_scope=CountryScope.ALL,
            country_role=CountryRole.UNSPECIFIED,
        )

        result = builder.build(
            original_query=("I'm looking for suppliers of " "electrical panels."),
            understanding=understanding,
        )

        assert result.intent == TradeIntent.SUPPLIER_SEARCH

        assert result.product is not None
        assert result.product.name == ("Electrical Control Panels")

        assert result.country_scope == CountryScope.ALL
        assert result.country_role == CountryRole.UNSPECIFIED
        assert result.country is None

        assert len(result.hs_codes) == 1
        assert result.hs_codes[0].code == "853710"

        print("Intent:", result.intent.value)
        print("Product:", result.product.name)
        print("Country scope:", result.country_scope.value)
        print("Country: ALL")
        print("HS code:", result.hs_codes[0].code)

    finally:
        db.close()


if __name__ == "__main__":
    test_trade_query_specific_country()
    test_trade_query_all_countries()
