from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.ingestion.country_sync import sync_country_master
from app.integrations.trade.comtrade_reference import (
    CountryReference,
)


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


def test_country_sync_insert_and_update():
    db = SessionLocal()

    try:
        client = FakeComtradeReferenceClient(
            [
                _reference(
                    comtrade_code=999,
                    iso2="TZ",
                    iso3="TST",
                    name="Testland",
                ),
                _reference(
                    comtrade_code=998,
                    iso2="TX",
                    iso3="TWO",
                    name="Two Islands",
                ),
            ]
        )

        first = sync_country_master(db, client=client)

        assert first.source_records == 2
        assert first.inserted == 2
        assert first.updated == 0
        assert first.skipped == 0

        client.references[0] = _reference(
            comtrade_code=999,
            iso2="TZ",
            iso3="TST",
            name="Testland Updated",
        )

        second = sync_country_master(db, client=client)

        assert second.source_records == 2
        assert second.inserted == 0
        assert second.updated == 1
        assert second.skipped == 0

    finally:
        db.rollback()

        # The sync service commits by design, so explicitly remove the
        # deterministic test records to keep the development DB clean.
        from sqlalchemy import delete
        from app.models import Country

        db.execute(
            delete(Country).where(
                Country.iso3.in_(["TST", "TWO"])
            )
        )
        db.commit()
        db.close()


def test_country_sync_skips_iso2_conflict():
    db = SessionLocal()

    try:
        from sqlalchemy import select
        from app.models import Country

        existing = db.scalar(
            select(Country).where(Country.iso3 == "IND")
        )
        assert existing is not None

        client = FakeComtradeReferenceClient(
            [
                _reference(
                    comtrade_code=999,
                    iso2="IN",
                    iso3="ZZZ",
                    name="Conflicting Area",
                )
            ]
        )

        result = sync_country_master(db, client=client)

        assert result.source_records == 1
        assert result.inserted == 0
        assert result.updated == 0
        assert result.skipped == 1

        assert db.scalar(
            select(Country).where(Country.iso3 == "ZZZ")
        ) is None

    finally:
        db.close()


if __name__ == "__main__":
    test_country_sync_insert_and_update()
    print("PASS country sync insert/update")

    test_country_sync_skips_iso2_conflict()
    print("PASS country sync ISO2 conflict")

    print("Country sync tests passed.")
