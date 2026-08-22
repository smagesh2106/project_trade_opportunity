from app.db.session import SessionLocal
from app.intelligence.hs_resolver import HSResolver
from app.repositories.product import ProductRepository


def test_hs_resolver():
    db = SessionLocal()

    try:
        repository = ProductRepository(db)

        product = repository.find_by_alias("electrical panels")

        assert product is not None

        resolver = HSResolver()

        result = resolver.resolve(product)

        assert len(result) == 1

        hs_code = result[0]

        assert hs_code.id == 4
        assert hs_code.code == "853710"
        assert hs_code.level == 6
        assert hs_code.description == "For a voltage not exceeding 1,000 V"
        assert hs_code.confidence == 0.95
        assert hs_code.mapping_type == "candidate"
        assert hs_code.source == "Development seed data"

        print("HS ID:", hs_code.id)
        print("HS Code:", hs_code.code)
        print("Description:", hs_code.description)
        print("Level:", hs_code.level)
        print("Confidence:", hs_code.confidence)
        print("Mapping type:", hs_code.mapping_type)
        print("Source:", hs_code.source)

    finally:
        db.close()


def test_hs_resolver_no_product():
    resolver = HSResolver()

    result = resolver.resolve(None)

    assert result == []

    print("No product correctly returned: []")


if __name__ == "__main__":
    test_hs_resolver()
    test_hs_resolver_no_product()
