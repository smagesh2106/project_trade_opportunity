from datetime import date
from types import SimpleNamespace

from app.schemas.intelligence import (
    CountryRole,
    CountryScope,
    ResolvedCountry,
    ResolvedHSCode,
    ResolvedProduct,
    TradeIntent,
    TradeQuery,
)
from app.services.trade_opportunity import TradeOpportunityService


class FakeTradeRepository:
    def __init__(self):
        self.supplier_calls = []
        self.history_calls = []

    def find_supplier_countries(
        self,
        hs_code_id,
        target_country_id=None,
        period_start=None,
        period_end=None,
    ):
        self.supplier_calls.append(
            {
                "hs_code_id": hs_code_id,
                "target_country_id": target_country_id,
                "period_start": period_start,
                "period_end": period_end,
            }
        )

        return [(4, 100.0)]

    def find_trade_history_pair(
        self,
        hs_code_id,
        trade_flow,
        reporter_country_id,
        partner_country_id,
        period_start=None,
        period_end=None,
    ):
        self.history_calls.append(
            {
                "hs_code_id": hs_code_id,
                "trade_flow": trade_flow,
                "reporter_country_id": reporter_country_id,
                "partner_country_id": partner_country_id,
                "period_start": period_start,
                "period_end": period_end,
            }
        )

        return [
            (2024, 50.0),
            (2025, 100.0),
        ]


class FakeCountryRepository:
    def get_by_id(self, country_id):
        return SimpleNamespace(
            id=country_id,
            name="Germany",
            iso2="DE",
            iso3="DEU",
        )


def build_trade_query():
    return TradeQuery(
        original_query="Find suppliers of electrical panels to India",
        intent=TradeIntent.SUPPLIER_SEARCH,
        product=ResolvedProduct(
            id=1,
            name="Electrical Control Panels",
            confidence=1.0,
        ),
        country_scope=CountryScope.SPECIFIC,
        country_role=CountryRole.DESTINATION,
        country=ResolvedCountry(
            id=1,
            iso2="IN",
            iso3="IND",
            name="India",
            confidence=1.0,
        ),
        hs_codes=[
            ResolvedHSCode(
                id=4,
                code="853710",
                description="For a voltage not exceeding 1,000 V",
                level=6,
                confidence=0.95,
            )
        ],
    )


def test_trade_opportunity_uses_default_period():
    trade_repository = FakeTradeRepository()
    service = TradeOpportunityService(
        trade_repository=trade_repository,
        country_repository=FakeCountryRepository(),
    )

    result = service.analyze(build_trade_query())

    assert result.period_start == date(2025, 1, 1)
    assert result.period_end == date(2025, 12, 31)

    assert trade_repository.supplier_calls[0]["period_start"] == date(2025, 1, 1)
    assert trade_repository.supplier_calls[0]["period_end"] == date(2025, 12, 31)


def test_trade_opportunity_uses_explicit_period():
    trade_repository = FakeTradeRepository()
    service = TradeOpportunityService(
        trade_repository=trade_repository,
        country_repository=FakeCountryRepository(),
    )

    result = service.analyze(
        build_trade_query(),
        period_start=date(2024, 1, 1),
        period_end=date(2024, 12, 31),
    )

    assert result.period_start == date(2024, 1, 1)
    assert result.period_end == date(2024, 12, 31)

    assert trade_repository.supplier_calls[0]["period_start"] == date(2024, 1, 1)
    assert trade_repository.supplier_calls[0]["period_end"] == date(2024, 12, 31)
    assert trade_repository.history_calls[0]["period_end"] == date(2024, 12, 31)


def test_trade_opportunity_defaults_end_to_start_year():
    service = TradeOpportunityService(
        trade_repository=FakeTradeRepository(),
        country_repository=FakeCountryRepository(),
    )

    result = service.analyze(
        build_trade_query(),
        period_start=date(2024, 1, 1),
    )

    assert result.period_start == date(2024, 1, 1)
    assert result.period_end == date(2024, 12, 31)


def test_trade_opportunity_defaults_start_to_end_year():
    service = TradeOpportunityService(
        trade_repository=FakeTradeRepository(),
        country_repository=FakeCountryRepository(),
    )

    result = service.analyze(
        build_trade_query(),
        period_end=date(2024, 12, 31),
    )

    assert result.period_start == date(2024, 1, 1)
    assert result.period_end == date(2024, 12, 31)


def test_trade_opportunity_rejects_invalid_period():
    service = TradeOpportunityService(
        trade_repository=FakeTradeRepository(),
        country_repository=FakeCountryRepository(),
    )

    try:
        service.analyze(
            build_trade_query(),
            period_start=date(2025, 12, 31),
            period_end=date(2025, 1, 1),
        )
    except ValueError as exc:
        assert "period_end" in str(exc)
    else:
        raise AssertionError("Expected invalid period to be rejected.")


if __name__ == "__main__":
    test_trade_opportunity_uses_default_period()
    test_trade_opportunity_uses_explicit_period()
    test_trade_opportunity_defaults_end_to_start_year()
    test_trade_opportunity_defaults_start_to_end_year()
    test_trade_opportunity_rejects_invalid_period()
