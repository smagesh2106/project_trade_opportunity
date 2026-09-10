from app.db.session import SessionLocal
from app.intelligence.product_matcher import ProductMatcher
from app.repositories.product import ProductRepository


def test_product_matcher_exact_alias():
    db = SessionLocal()

    try:
        repository = ProductRepository(db)
        matcher = ProductMatcher(repository)

        result = matcher.match("  ELECTRICAL   PANELS  ")

        assert result is not None
        assert result.product.id == 1
        assert result.product.name == "Electrical Control Panels"
        assert result.product.confidence == 1.0
        assert result.match_type == "exact_alias"

        print("Product ID:", result.product.id)
        print("Product:", result.product.name)
        print("Confidence:", result.product.confidence)
        print("Match type:", result.match_type)

    finally:
        db.close()


def test_product_matcher_unknown_product():
    db = SessionLocal()

    try:
        repository = ProductRepository(db)
        matcher = ProductMatcher(repository)

        result = matcher.match("solar powered bananas")

        assert result is None

        print("Unknown product correctly returned: None")

    finally:
        db.close()


def test_product_matcher_demo_aliases():
    db = SessionLocal()

    expected_products = {
        "control panel": "Electrical Control Panels",
        "automatic circuit breaker": "Circuit Breakers",
        "power transformer": "HV Power Transformers",
        "electrical switchgear": "Switchgear",
        "disconnector": "Isolators / Disconnectors",
        "power capacitor bank": "Capacitor Banks",
    }

    try:
        matcher = ProductMatcher(ProductRepository(db))

        for alias, product_name in expected_products.items():
            result = matcher.match(alias)

            assert result is not None, f"Product alias did not resolve: {alias}"
            assert result.product.name == product_name
            assert result.match_type == "exact_alias"

    finally:
        db.close()


if __name__ == "__main__":
    test_product_matcher_exact_alias()
    test_product_matcher_unknown_product()
    test_product_matcher_demo_aliases()
