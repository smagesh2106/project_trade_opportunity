from app.db.session import SessionLocal
from app.intelligence.country_matcher import CountryMatcher
from app.repositories.country import CountryRepository


def test_country_matcher_name():
    db = SessionLocal()

    try:
        repository = CountryRepository(db)
        matcher = CountryMatcher(repository)

        result = matcher.match("India")

        assert result is not None
        assert result.country.id == 1
        assert result.country.name == "India"
        assert result.country.iso2 == "IN"
        assert result.country.iso3 == "IND"
        assert result.country.confidence == 1.0
        assert result.match_type == "exact_identifier"

        print("Country ID:", result.country.id)
        print("Country:", result.country.name)
        print("ISO2:", result.country.iso2)
        print("ISO3:", result.country.iso3)
        print("Confidence:", result.country.confidence)
        print("Match type:", result.match_type)

    finally:
        db.close()


def test_country_matcher_iso2():
    db = SessionLocal()

    try:
        repository = CountryRepository(db)
        matcher = CountryMatcher(repository)

        result = matcher.match("IN")

        assert result is not None
        assert result.country.name == "India"

        print("ISO2 match:", result.country.name)

    finally:
        db.close()


def test_country_matcher_iso3():
    db = SessionLocal()

    try:
        repository = CountryRepository(db)
        matcher = CountryMatcher(repository)

        result = matcher.match("IND")

        assert result is not None
        assert result.country.name == "India"

        print("ISO3 match:", result.country.name)

    finally:
        db.close()


def test_country_matcher_unknown():
    db = SessionLocal()

    try:
        repository = CountryRepository(db)
        matcher = CountryMatcher(repository)

        result = matcher.match("Atlantis")

        assert result is None

        print("Unknown country correctly returned: None")

    finally:
        db.close()


def test_country_matcher_no_country():
    db = SessionLocal()

    try:
        repository = CountryRepository(db)
        matcher = CountryMatcher(repository)

        result = matcher.match(None)

        assert result is None

        print("No country correctly returned: None")

    finally:
        db.close()


if __name__ == "__main__":
    test_country_matcher_name()
    test_country_matcher_iso2()
    test_country_matcher_iso3()
    test_country_matcher_unknown()
    test_country_matcher_no_country()
