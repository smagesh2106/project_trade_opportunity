from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.trade.models import TradeDataRecord
from app.integrations.trade.provider import TradeDataProvider
from app.models import (
    Country,
    DataQualityResult,
    DataSource,
    HSCode,
    IngestionRun,
    TradeData,
)


@dataclass(frozen=True)
class IngestionResult:
    ingestion_run_id: int
    status: str
    records_received: int
    aggregate_records: int
    detail_records_skipped: int
    records_inserted: int
    records_updated: int
    records_rejected: int
    data_period_start: datetime | None
    data_period_end: datetime | None


class TradeIngestionService:
    """Provider-neutral ingestion into the canonical TradeData table."""

    SOURCE_NAME = "UN Comtrade"
    SOURCE_PROVIDER = "United Nations Comtrade"
    SOURCE_TYPE = "api"
    SOURCE_BASE_URL = "https://comtradeapi.un.org/"
    SOURCE_UPDATE_FREQUENCY = "source-driven"

    def __init__(self, db: Session, provider: TradeDataProvider):
        self.db = db
        self.provider = provider

    def ingest(
        self,
        *,
        reporter_code: int,
        period: str,
        flow_code: str,
        cmd_codes: list[str],
        partner_code: int | None = None,
        max_records: int = 500,
        data_version: str | None = None,
    ) -> IngestionResult:
        source = self._get_or_create_source()

        run = IngestionRun(
            source_id=source.id,
            started_at=datetime.now(timezone.utc),
            status="running",
            data_period_start=self._period_to_datetime(period),
            data_period_end=self._period_to_end_datetime(period),
        )
        self.db.add(run)
        self.db.flush()

        try:
            records = self._fetch_records(
                reporter_code=reporter_code,
                period=period,
                flow_code=flow_code,
                cmd_codes=cmd_codes,
                partner_code=partner_code,
                max_records=max_records,
            )

            inserted = 0
            updated = 0
            rejected = 0
            reasons: list[str] = []
            canonical_aggregate_records = 0
            skipped_records = 0

            for record in records:
                if not record.is_country_level_aggregate:
                    skipped_records += 1
                    continue

                canonical_aggregate_records += 1

                try:
                    self._validate_record(record)

                    reporter = self._resolve_country(
                        record.reporter_iso3,
                        record.reporter_name,
                    )

                    partner = self._resolve_country(
                        record.partner_iso3,
                        record.partner_name,
                    )

                    hs_code = self._resolve_hs_code(record.hs_code)

                    source_record_id = (
                        record.source_record_id
                        or self._build_source_record_id(record)
                    )

                    existing = self.db.scalar(
                        select(TradeData).where(
                            TradeData.source_id == source.id,
                            TradeData.source_record_id == source_record_id,
                        )
                    )

                    values = {
                        "reporter_country_id": reporter.id,
                        "partner_country_id": partner.id,
                        "hs_code_id": hs_code.id,
                        "period_start": record.period_start,
                        "period_end": record.period_end,
                        "period_type": record.period_type,
                        "trade_flow": record.trade_flow,
                        "trade_value_usd": record.trade_value_usd,
                        "trade_value_currency": record.trade_value_currency,
                        "quantity": record.quantity,
                        "quantity_unit": record.quantity_unit,
                        "source_id": source.id,
                        "source_record_id": source_record_id,
                        "data_version": record.data_version or data_version,
                        "updated_at": datetime.now(timezone.utc),
                    }

                    if existing is None:
                        self.db.add(TradeData(**values))
                        inserted += 1
                    else:
                        for field, value in values.items():
                            setattr(existing, field, value)
                        updated += 1

                except (ValueError, LookupError) as exc:
                    rejected += 1
                    reasons.append(str(exc))

            run.records_received = len(records)
            run.records_inserted = inserted
            run.records_updated = updated
            run.records_rejected = rejected
            run.status = (
                "completed"
                if rejected == 0
                else "completed_with_rejections"
            )
            run.completed_at = datetime.now(timezone.utc)

            failure_percentage = (
                (rejected / len(records)) * 100.0
                if records
                else 0.0
            )

            self.db.add(
                DataQualityResult(
                    ingestion_run_id=run.id,
                    check_name="record_validation",
                    status=(
                        "passed"
                        if rejected == 0
                        else "warning"
                    ),
                    records_checked=len(records),
                    records_failed=rejected,
                    failure_percentage=failure_percentage,
                    details=json.dumps(
                        {
                            "rejection_reasons": reasons[:100],
                            "canonical_country_level_aggregate_records": (
                                canonical_aggregate_records
                            ),
                            "non_canonical_records_skipped": skipped_records,
                        }
                    ),
                )
            )

            self.db.commit()

            return IngestionResult(
                ingestion_run_id=run.id,
                status=run.status,
                records_received=run.records_received,
                aggregate_records=canonical_aggregate_records,
                detail_records_skipped=skipped_records,
                records_inserted=inserted,
                records_updated=updated,
                records_rejected=rejected,
                data_period_start=run.data_period_start,
                data_period_end=run.data_period_end,
            )

        except Exception as exc:
            self.db.rollback()

            failed_run = IngestionRun(
                source_id=source.id,
                started_at=run.started_at,
                completed_at=datetime.now(timezone.utc),
                status="failed",
                data_period_start=self._period_to_datetime(period),
                data_period_end=self._period_to_end_datetime(period),
                error_message=str(exc),
            )
            self.db.add(failed_run)
            self.db.commit()
            raise

    def _fetch_records(
        self,
        *,
        reporter_code: int,
        period: str,
        flow_code: str,
        cmd_codes: list[str],
        partner_code: int | None,
        max_records: int,
    ) -> list[TradeDataRecord]:
        # Specific partner:
        # use the normal provider request.
        if partner_code is not None:
            return self.provider.fetch_trade_data(
                reporter_code=reporter_code,
                period=period,
                flow_code=flow_code,
                cmd_codes=cmd_codes,
                partner_code=partner_code,
                max_records=max_records,
            )

        # All partners:
        # read the current synchronized UN Comtrade M49 codes from the
        # country master and use the provider's explicit batching method.
        fetch_all = getattr(
            self.provider,
            "fetch_all_partner_trade_data",
            None,
        )

        if fetch_all is None:
            # Backwards-compatible fallback for providers that do not
            # implement explicit all-partner batching.
            return self.provider.fetch_trade_data(
                reporter_code=reporter_code,
                period=period,
                flow_code=flow_code,
                cmd_codes=cmd_codes,
                partner_code=None,
                max_records=max_records,
            )

        partner_codes = self._get_partner_codes(
            reporter_code=reporter_code,
        )

        if not partner_codes:
            raise LookupError(
                "No active countries with UN Comtrade codes are available "
                "for all-partner ingestion. Run the country master "
                "synchronization first."
            )

        return fetch_all(
            reporter_code=reporter_code,
            period=period,
            flow_code=flow_code,
            cmd_codes=cmd_codes,
            partner_codes=partner_codes,
            max_records=max_records,
        )

    def _get_partner_codes(
        self,
        *,
        reporter_code: int,
    ) -> list[int]:
        rows = self.db.scalars(
            select(Country.comtrade_code)
            .where(
                Country.active.is_(True),
                Country.comtrade_code.is_not(None),
                Country.comtrade_code != reporter_code,
            )
            .order_by(Country.comtrade_code)
        ).all()

        return [
            int(code)
            for code in rows
            if code is not None and int(code) > 0
        ]

    def _get_or_create_source(self) -> DataSource:
        source = self.db.scalar(
            select(DataSource).where(DataSource.name == self.SOURCE_NAME)
        )

        if source is None:
            source = DataSource(
                name=self.SOURCE_NAME,
                provider=self.SOURCE_PROVIDER,
                source_type=self.SOURCE_TYPE,
                base_url=self.SOURCE_BASE_URL,
                update_frequency=self.SOURCE_UPDATE_FREQUENCY,
                license_notes=(
                    "Official UN Comtrade API data. Review UN Comtrade "
                    "use/re-dissemination terms before production redistribution."
                ),
                active=True,
            )
            self.db.add(source)
            self.db.flush()

        return source

    def _resolve_country(
        self,
        iso3: str | None,
        name: str | None,
    ) -> Country:
        if not iso3:
            raise LookupError(
                f"Country ISO3 is missing for provider record: "
                f"{name or '<unknown>'}"
            )

        country = self.db.scalar(
            select(Country).where(
                Country.iso3 == iso3.upper(),
                Country.active.is_(True),
            )
        )

        if country is None:
            raise LookupError(
                f"Country {iso3} is not present in the country master. "
                "Synchronize the Comtrade country master before "
                "all-partner ingestion."
            )

        return country

    def _resolve_hs_code(self, code: str) -> HSCode:
        normalized = code.strip()

        hs_code = self.db.scalar(
            select(HSCode).where(
                HSCode.code == normalized,
                HSCode.active.is_(True),
            )
        )

        if hs_code is None:
            raise LookupError(
                f"HS code {normalized} is not present in the HS master."
            )

        return hs_code

    @staticmethod
    def _validate_record(record: TradeDataRecord) -> None:
        if record.trade_flow not in {"import", "export"}:
            raise ValueError(
                f"Unsupported canonical trade flow: {record.trade_flow!r}"
            )

        if record.reporter_code <= 0:
            raise ValueError("Reporter code must be positive.")

        if record.partner_code <= 0:
            raise ValueError(
                "Partner code must be positive for country data."
            )

        partner_iso3 = (record.partner_iso3 or "").strip().upper()

        if len(partner_iso3) != 3 or not partner_iso3.isalpha():
            raise ValueError(
                f"Partner ISO3 must be a three-letter country code: "
                f"{record.partner_iso3!r}"
            )

        if not record.hs_code.strip():
            raise ValueError("HS code cannot be empty.")

        if (
            record.trade_value_usd is not None
            and record.trade_value_usd < 0
        ):
            raise ValueError("Trade value cannot be negative.")

        if record.quantity is not None and record.quantity < 0:
            raise ValueError("Quantity cannot be negative.")

    @staticmethod
    def _build_source_record_id(
        record: TradeDataRecord,
    ) -> str:
        return (
            f"{record.provider}:"
            f"{record.reporter_code}:"
            f"{record.partner_code}:"
            f"{record.hs_code}:"
            f"{record.period_start.isoformat()}:"
            f"{record.trade_flow}"
        )

    @staticmethod
    def _period_to_datetime(
        period: str,
    ) -> datetime | None:
        text = str(period).strip()

        if len(text) == 4 and text.isdigit():
            return datetime(
                int(text),
                1,
                1,
                tzinfo=timezone.utc,
            )

        if len(text) == 6 and text.isdigit():
            return datetime(
                int(text[:4]),
                int(text[4:6]),
                1,
                tzinfo=timezone.utc,
            )

        return None

    @staticmethod
    def _period_to_end_datetime(
        period: str,
    ) -> datetime | None:
        start = TradeIngestionService._period_to_datetime(period)

        if start is None:
            return None

        if len(str(period).strip()) == 4:
            return datetime(
                start.year,
                12,
                31,
                23,
                59,
                59,
                tzinfo=timezone.utc,
            )

        from calendar import monthrange

        return datetime(
            start.year,
            start.month,
            monthrange(
                start.year,
                start.month,
            )[1],
            23,
            59,
            59,
            tzinfo=timezone.utc,
        )
