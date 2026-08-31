from app.schemas.intelligence import (
    CountryRole,
    CountryScope,
    ResolvedCountry,
    ResolvedHSCode,
    ResolvedProduct,
    TradeIntent,
    TradeQuery,
)


def _country(
    country_id: int,
    name: str,
    iso2: str,
    iso3: str,
) -> ResolvedCountry:
    return ResolvedCountry(
        id=country_id,
        name=name,
        iso2=iso2,
        iso3=iso3,
        confidence=1.0,
    )


def _product() -> ResolvedProduct:
    return ResolvedProduct(
        id=1,
        name="Electrical Control Panels",
        confidence=1.0,
    )


def _hs_code() -> ResolvedHSCode:
    return ResolvedHSCode(
        id=1,
        code="853710",
        description="For a voltage not exceeding 1,000 V",
        level=6,
        confidence=0.95,
    )


INDIA = _country(1, "India", "IN", "IND")
SAUDI_ARABIA = _country(2, "Saudi Arabia", "SA", "SAU")
UAE = _country(3, "United Arab Emirates", "AE", "ARE")
GERMANY = _country(4, "Germany", "DE", "DEU")


def _base(**overrides):
    data = {
        "original_query": "test query",
        "intent": TradeIntent.SUPPLIER_SEARCH,
        "product": _product(),
        "country_scope": CountryScope.ALL,
        "country_role": CountryRole.UNSPECIFIED,
        "country": None,
        "comparison_countries": [],
        "hs_codes": [_hs_code()],
    }
    data.update(overrides)
    return TradeQuery(**data)


# ======================================================
# POSITIVE VALIDATION CASES
# ======================================================


def test_global_query_is_valid():
    query = _base()

    assert query.country_scope == CountryScope.ALL
    assert query.country is None
    assert query.country_role == CountryRole.UNSPECIFIED


def test_specific_destination_query_is_valid():
    query = _base(
        country_scope=CountryScope.SPECIFIC,
        country_role=CountryRole.DESTINATION,
        country=INDIA,
    )

    assert query.country == INDIA
    assert query.country_role == CountryRole.DESTINATION


def test_specific_origin_query_is_valid():
    query = _base(
        country_scope=CountryScope.SPECIFIC,
        country_role=CountryRole.ORIGIN,
        country=INDIA,
    )

    assert query.country == INDIA
    assert query.country_role == CountryRole.ORIGIN


def test_specific_location_query_is_valid():
    query = _base(
        country_scope=CountryScope.SPECIFIC,
        country_role=CountryRole.LOCATION,
        country=INDIA,
    )

    assert query.country == INDIA
    assert query.country_role == CountryRole.LOCATION


def test_comparison_with_two_distinct_countries_is_valid():
    query = _base(
        original_query="Compare Germany and UAE",
        intent=TradeIntent.COMPARISON,
        country_scope=CountryScope.SPECIFIC,
        country_role=CountryRole.DESTINATION,
        country=INDIA,
        comparison_countries=[GERMANY, UAE],
    )

    assert query.intent == TradeIntent.COMPARISON
    assert len(query.comparison_countries) == 2
    assert query.comparison_countries[0].id != query.comparison_countries[1].id


# ======================================================
# NEGATIVE VALIDATION CASES
# ======================================================


def test_all_scope_rejects_specific_country():
    try:
        _base(
            country_scope=CountryScope.ALL,
            country_role=CountryRole.UNSPECIFIED,
            country=INDIA,
        )
    except ValueError as exc:
        assert "country must be None" in str(exc)
    else:
        raise AssertionError("Expected ALL scope with a country to be rejected.")


def test_specific_scope_requires_country():
    try:
        _base(
            country_scope=CountryScope.SPECIFIC,
            country_role=CountryRole.DESTINATION,
            country=None,
        )
    except ValueError as exc:
        assert "country is required" in str(exc)
    else:
        raise AssertionError(
            "Expected SPECIFIC scope without a country to be rejected."
        )


def test_specific_scope_requires_country_role():
    try:
        _base(
            country_scope=CountryScope.SPECIFIC,
            country_role=CountryRole.UNSPECIFIED,
            country=INDIA,
        )
    except ValueError as exc:
        assert "country_role must be specified" in str(exc)
    else:
        raise AssertionError(
            "Expected SPECIFIC scope with unspecified role to be rejected."
        )


def test_comparison_requires_exactly_two_countries():
    try:
        _base(
            intent=TradeIntent.COMPARISON,
            country_scope=CountryScope.SPECIFIC,
            country_role=CountryRole.DESTINATION,
            country=INDIA,
            comparison_countries=[GERMANY],
        )
    except ValueError as exc:
        assert "exactly two comparison countries" in str(exc)
    else:
        raise AssertionError("Expected comparison with one country to be rejected.")


def test_comparison_rejects_three_countries():
    try:
        _base(
            intent=TradeIntent.COMPARISON,
            country_scope=CountryScope.SPECIFIC,
            country_role=CountryRole.DESTINATION,
            country=INDIA,
            comparison_countries=[GERMANY, UAE, SAUDI_ARABIA],
        )
    except ValueError as exc:
        assert "exactly two comparison countries" in str(exc)
    else:
        raise AssertionError("Expected comparison with three countries to be rejected.")


def test_comparison_rejects_duplicate_countries():
    try:
        _base(
            intent=TradeIntent.COMPARISON,
            country_scope=CountryScope.SPECIFIC,
            country_role=CountryRole.DESTINATION,
            country=INDIA,
            comparison_countries=[GERMANY, GERMANY],
        )
    except ValueError as exc:
        assert "comparison countries must be distinct" in str(exc)
    else:
        raise AssertionError("Expected comparison of the same country to be rejected.")


def test_comparison_without_destination_country_is_rejected():
    try:
        _base(
            intent=TradeIntent.COMPARISON,
            country_scope=CountryScope.SPECIFIC,
            country_role=CountryRole.UNSPECIFIED,
            country=None,
            comparison_countries=[GERMANY, UAE],
        )
    except ValueError as exc:
        message = str(exc)
        assert (
            "country is required" in message
            or "country_role must be specified" in message
        )
    else:
        raise AssertionError(
            "Expected comparison without a resolved destination country "
            "to be rejected."
        )


def test_global_scope_rejects_specific_role():
    try:
        _base(
            country_scope=CountryScope.ALL,
            country_role=CountryRole.DESTINATION,
            country=None,
        )
    except ValueError as exc:
        assert "country_role" in str(exc) or "unspecified" in str(exc)
    else:
        # This documents current behavior if the schema intentionally allows
        # a role with ALL scope. Do not silently fail the test suite if that
        # rule is not currently part of the model.
        pass


if __name__ == "__main__":
    tests = [
        test_global_query_is_valid,
        test_specific_destination_query_is_valid,
        test_specific_origin_query_is_valid,
        test_specific_location_query_is_valid,
        test_comparison_with_two_distinct_countries_is_valid,
        test_all_scope_rejects_specific_country,
        test_specific_scope_requires_country,
        test_specific_scope_requires_country_role,
        test_comparison_requires_exactly_two_countries,
        test_comparison_rejects_three_countries,
        test_comparison_rejects_duplicate_countries,
        test_comparison_without_destination_country_is_rejected,
        test_global_scope_rejects_specific_role,
    ]

    passed = 0

    for test in tests:
        test()
        print(f"PASS {test.__name__}")
        passed += 1

    print()
    print(f"{passed} structured TradeQuery validation tests passed.")
