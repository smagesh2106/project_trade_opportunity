from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.ingestion.country_sync import sync_country_master
from app.integrations.trade.comtrade_reference import CountryReference
from app.models import Country

TEST_ISO3_CODES = {"TST", "TWO", "ZZ1", "ZZ2"}

# Deliberately outside the real UN M49 range.
TEST_CODE_A = 90001
TEST_CODE_B = 90002
TEST_CODE_A_UPDATED = 90003
TEST_CODE_CONFLICT = 90004


class FakeComtradeReferenceClient:
    def __init__(self, references):
        self.references = references

    def fetch_countries(self):
        return self.references


def _reference(
    *,
    comtrade_code: int,
    iso2: str,
    iso3: str,
    name: str,
) -> CountryReference:
    return CountryReference(
        comtrade_code=comtrade_code,
        iso2=iso2,
        iso3=iso3,
        name=name,
        effective_date=datetime.now(timezone.utc),
        is_group=False,
    )


def _cleanup_test_countries(db) -> None:
    db.execute(delete(Country).where(Country.iso3.in_(TEST_ISO3_CODES)))
    db.commit()


def test_country_sync_insert_update_and_comtrade_code():
    db = SessionLocal()

    try:
        _cleanup_test_countries(db)

        client = FakeComtradeReferenceClient(
            [
                _reference(
                    comtrade_code=TEST_CODE_A,
                    iso2="ZZ",
                    iso3="TST",
                    name="Testland",
                ),
                _reference(
                    comtrade_code=TEST_CODE_B,
                    iso2="ZY",
                    iso3="TWO",
                    name="Two Islands",
                ),
            ]
        )

        first = sync_country_master(
            db,
            client=client,
        )

        assert first.source_records == 2
        assert first.inserted == 2
        assert first.updated == 0
        assert first.skipped == 0

        tst = db.scalar(select(Country).where(Country.iso3 == "TST"))
        two = db.scalar(select(Country).where(Country.iso3 == "TWO"))

        assert tst is not None
        assert tst.iso2 == "ZZ"
        assert tst.comtrade_code == TEST_CODE_A

        assert two is not None
        assert two.iso2 == "ZY"
        assert two.comtrade_code == TEST_CODE_B

        client.references[0] = _reference(
            comtrade_code=TEST_CODE_A_UPDATED,
            iso2="ZZ",
            iso3="TST",
            name="Testland Updated",
        )

        second = sync_country_master(
            db,
            client=client,
        )

        assert second.source_records == 2
        assert second.inserted == 0
        assert second.updated == 1
        assert second.skipped == 0

        db.refresh(tst)

        assert tst.name == "Testland Updated"
        assert tst.comtrade_code == TEST_CODE_A_UPDATED

    finally:
        _cleanup_test_countries(db)
        db.close()


def test_country_sync_skips_iso2_and_comtrade_code_conflicts():
    db = SessionLocal()

    try:
        _cleanup_test_countries(db)

        india = db.scalar(select(Country).where(Country.iso3 == "IND"))

        assert india is not None
        assert india.comtrade_code is not None

        # ISO2 conflict with India.
        iso2_conflict = _reference(
            comtrade_code=TEST_CODE_CONFLICT,
            iso2="IN",
            iso3="ZZ1",
            name="ISO2 Conflict",
        )

        result = sync_country_master(
            db,
            client=FakeComtradeReferenceClient([iso2_conflict]),
        )

        assert result.source_records == 1
        assert result.inserted == 0
        assert result.updated == 0
        assert result.skipped == 1

        assert db.scalar(select(Country).where(Country.iso3 == "ZZ1")) is None

        # Comtrade-code conflict with India.
        code_conflict = _reference(
            comtrade_code=india.comtrade_code,
            iso2="QX",
            iso3="ZZ2",
            name="Code Conflict",
        )

        result = sync_country_master(
            db,
            client=FakeComtradeReferenceClient([code_conflict]),
        )

        assert result.source_records == 1
        assert result.inserted == 0
        assert result.updated == 0
        assert result.skipped == 1

        assert db.scalar(select(Country).where(Country.iso3 == "ZZ2")) is None

    finally:
        _cleanup_test_countries(db)
        db.close()


if __name__ == "__main__":
    test_country_sync_insert_update_and_comtrade_code()
    print("PASS country sync insert/update/comtrade code")

    test_country_sync_skips_iso2_and_comtrade_code_conflicts()
    print("PASS country sync conflict handling")

    print("Country sync tests passed.")
