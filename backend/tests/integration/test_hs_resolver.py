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

        assert hs_code.code == "853710"
        assert hs_code.level == 6
        assert hs_code.description == "For a voltage not exceeding 1,000 V"
        assert hs_code.confidence == 0.95
        assert hs_code.mapping_type == "candidate"
        assert hs_code.source == "WCO HS Nomenclature 2022"

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


def test_hs_resolver_demo_product_families():
    db = SessionLocal()

    expected_codes = {
        "electrical panels": ["853710"],
        "circuit breakers": ["853620", "853521", "853529"],
        "transformers": ["850434", "850423"],
        "switchgear": ["853710", "853720"],
        "isolators": ["853530", "853650"],
        "capacitor banks": ["853210"],
    }

    try:
        repository = ProductRepository(db)
        resolver = HSResolver()

        for alias, codes in expected_codes.items():
            product = repository.find_by_alias(alias)

            assert product is not None, f"Product alias did not resolve: {alias}"

            resolved = resolver.resolve(product)

            assert [item.code for item in resolved] == codes
            assert all(item.level == 6 for item in resolved)
            assert all(item.mapping_type == "candidate" for item in resolved)
            assert all(
                item.source == "WCO HS Nomenclature 2022" for item in resolved
            )

    finally:
        db.close()


if __name__ == "__main__":
    test_hs_resolver()
    test_hs_resolver_no_product()
    test_hs_resolver_demo_product_families()
