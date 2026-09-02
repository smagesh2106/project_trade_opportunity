from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.trade.comtrade_reference import (
    ComtradeReferenceClient,
)
from app.models import Country


@dataclass(frozen=True)
class CountrySyncResult:
    source: str
    source_records: int
    inserted: int
    updated: int
    skipped: int


class CountryMasterSyncService:
    """Synchronize the application's country master from UN Comtrade."""

    SOURCE_NAME = "UN Comtrade"

    def __init__(
        self,
        db: Session,
        client: ComtradeReferenceClient,
    ):
        self.db = db
        self.client = client

    def sync(self) -> CountrySyncResult:
        references = self.client.fetch_countries()

        existing_countries = self.db.scalars(select(Country)).all()

        by_iso3 = {
            country.iso3.strip().upper(): country
            for country in existing_countries
        }
        by_iso2 = {
            country.iso2.strip().upper(): country
            for country in existing_countries
        }
        by_comtrade_code = {
            country.comtrade_code: country
            for country in existing_countries
            if country.comtrade_code is not None
        }

        inserted = 0
        updated = 0
        skipped = 0

        for reference in references:
            iso2 = reference.iso2
            iso3 = reference.iso3
            comtrade_code = reference.comtrade_code

            existing = by_iso3.get(iso3)

            if existing is None:
                iso2_owner = by_iso2.get(iso2)

                if iso2_owner is not None:
                    skipped += 1
                    continue

                code_owner = by_comtrade_code.get(comtrade_code)

                if code_owner is not None:
                    skipped += 1
                    continue

                country = Country(
                    iso2=iso2,
                    iso3=iso3,
                    comtrade_code=comtrade_code,
                    name=reference.name,
                    official_name=None,
                    region=None,
                    subregion=None,
                    active=True,
                )

                self.db.add(country)
                self.db.flush()

                by_iso3[iso3] = country
                by_iso2[iso2] = country
                by_comtrade_code[comtrade_code] = country
                inserted += 1
                continue

            changed = False

            current_iso2 = existing.iso2.strip().upper()

            if current_iso2 != iso2:
                iso2_owner = by_iso2.get(iso2)

                if (
                    iso2_owner is not None
                    and iso2_owner.id != existing.id
                ):
                    skipped += 1
                    continue

                if by_iso2.get(current_iso2) is existing:
                    by_iso2.pop(current_iso2, None)

                existing.iso2 = iso2
                by_iso2[iso2] = existing
                changed = True

            current_code = existing.comtrade_code

            if current_code != comtrade_code:
                code_owner = by_comtrade_code.get(comtrade_code)

                if (
                    code_owner is not None
                    and code_owner.id != existing.id
                ):
                    skipped += 1
                    continue

                if (
                    current_code is not None
                    and by_comtrade_code.get(current_code) is existing
                ):
                    by_comtrade_code.pop(current_code, None)

                existing.comtrade_code = comtrade_code
                by_comtrade_code[comtrade_code] = existing
                changed = True

            if existing.name != reference.name:
                existing.name = reference.name
                changed = True

            if not existing.active:
                existing.active = True
                changed = True

            if changed:
                existing.updated_at = datetime.now(timezone.utc)
                updated += 1

        self.db.commit()

        return CountrySyncResult(
            source=self.SOURCE_NAME,
            source_records=len(references),
            inserted=inserted,
            updated=updated,
            skipped=skipped,
        )


def sync_country_master(
    db: Session,
    *,
    client: ComtradeReferenceClient | None = None,
) -> CountrySyncResult:
    service = CountryMasterSyncService(
        db=db,
        client=client or ComtradeReferenceClient(),
    )
    return service.sync()
