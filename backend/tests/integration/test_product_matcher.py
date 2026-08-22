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


if __name__ == "__main__":
    test_product_matcher_exact_alias()
    test_product_matcher_unknown_product()
