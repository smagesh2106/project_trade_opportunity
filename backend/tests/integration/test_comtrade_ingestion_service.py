from datetime import date

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.ingestion.trade_ingestion import TradeIngestionService
from app.integrations.trade.models import TradeDataRecord
from app.integrations.trade.provider import TradeDataProvider
from app.models import DataQualityResult, IngestionRun, TradeData


class FakeProvider(TradeDataProvider):
    @property
    def provider_name(self) -> str:
        return "Fake Trade Provider"

    def __init__(self, records):
        self.records = records

    def fetch_trade_data(self, **kwargs):
        return self.records


def _record(value: float, source_id: str) -> TradeDataRecord:
    return TradeDataRecord(
        provider="Fake Trade Provider",
        reporter_code=699,
        reporter_iso3="IND",
        reporter_name="India",
        partner_code=276,
        partner_iso3="DEU",
        partner_name="Germany",
        hs_code="853710",
        hs_description="For a voltage not exceeding 1,000 V",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        period_type="annual",
        trade_flow="import",
        trade_value_usd=value,
        trade_value_currency="USD",
        quantity=100,
        quantity_unit="N",
        source_record_id=source_id,
        data_version="test-v1",
        is_aggregate=True,
    )


def _detail_record(
    value: float,
    source_id: str,
    partner2_code: int,
) -> TradeDataRecord:
    return TradeDataRecord(
        provider="Fake Trade Provider",
        reporter_code=699,
        reporter_iso3="IND",
        reporter_name="India",
        partner_code=276,
        partner_iso3="DEU",
        partner_name="Germany",
        hs_code="853710",
        hs_description="For a voltage not exceeding 1,000 V",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        period_type="annual",
        trade_flow="import",
        trade_value_usd=value,
        trade_value_currency="USD",
        quantity=10,
        quantity_unit="kg",
        source_record_id=f"TEST-DETAIL-{partner2_code}-{source_id}",
        data_version="test-v1",
        is_aggregate=False,
    )


def _cleanup_test_data(db, trade_source_record_ids, ingestion_run_ids):
    """Remove records created by this integration test."""

    # DataQualityResult references IngestionRun, so remove those first.
    if ingestion_run_ids:
        db.execute(
            delete(DataQualityResult).where(
                DataQualityResult.ingestion_run_id.in_(ingestion_run_ids)
            )
        )

    # Remove TradeData rows created by the test.
    if trade_source_record_ids:
        db.execute(
            delete(TradeData).where(
                TradeData.source_record_id.in_(trade_source_record_ids)
            )
        )

    # Finally remove the ingestion audit rows created by the test.
    if ingestion_run_ids:
        db.execute(delete(IngestionRun).where(IngestionRun.id.in_(ingestion_run_ids)))

    db.commit()


def test_ingestion_insert_and_idempotent_update():
    db = SessionLocal()

    test_trade_record_ids = {
        "TEST-INGEST-AGGREGATE",
        "TEST-DETAIL-20-TEST-INGEST-DETAIL-1",
        "TEST-DETAIL-36-TEST-INGEST-DETAIL-2",
    }

    ingestion_run_ids = []

    try:
        # Make the test safe to rerun even if a previous execution was
        # interrupted before its cleanup completed.
        _cleanup_test_data(
            db=db,
            trade_source_record_ids=test_trade_record_ids,
            ingestion_run_ids=[],
        )

        service = TradeIngestionService(
            db=db,
            provider=FakeProvider(
                [
                    _record(
                        123456.0,
                        "TEST-INGEST-AGGREGATE",
                    ),
                    _detail_record(
                        5310.936,
                        "TEST-INGEST-DETAIL-1",
                        20,
                    ),
                    _detail_record(
                        6582.194,
                        "TEST-INGEST-DETAIL-2",
                        36,
                    ),
                ]
            ),
        )

        first = service.ingest(
            reporter_code=699,
            period="2025",
            flow_code="M",
            cmd_codes=["853710"],
            partner_code=276,
            max_records=50,
        )

        ingestion_run_ids.append(first.ingestion_run_id)

        assert first.records_received == 3
        assert first.aggregate_records == 1
        assert first.detail_records_skipped == 2
        assert first.records_inserted == 1
        assert first.records_updated == 0
        assert first.records_rejected == 0

        second = service.ingest(
            reporter_code=699,
            period="2025",
            flow_code="M",
            cmd_codes=["853710"],
            partner_code=276,
            max_records=50,
        )

        ingestion_run_ids.append(second.ingestion_run_id)

        assert second.records_received == 3
        assert second.aggregate_records == 1
        assert second.detail_records_skipped == 2
        assert second.records_inserted == 0
        assert second.records_updated == 1
        assert second.records_rejected == 0

    finally:
        _cleanup_test_data(
            db=db,
            trade_source_record_ids=test_trade_record_ids,
            ingestion_run_ids=ingestion_run_ids,
        )
        db.close()


def test_ingestion_rejects_unknown_country():
    db = SessionLocal()

    test_trade_record_ids = {
        "TEST-BAD-COUNTRY",
    }

    ingestion_run_ids = []

    try:
        # Make the test safe to rerun.
        _cleanup_test_data(
            db=db,
            trade_source_record_ids=test_trade_record_ids,
            ingestion_run_ids=[],
        )

        bad = _record(
            1.0,
            "TEST-BAD-COUNTRY",
        )

        bad = TradeDataRecord(
            **{
                **bad.__dict__,
                "reporter_code": 99999,
                "reporter_iso3": "ZZZ",
                "reporter_name": "Unknown",
            }
        )

        result = TradeIngestionService(
            db=db,
            provider=FakeProvider([bad]),
        ).ingest(
            reporter_code=99999,
            period="2025",
            flow_code="M",
            cmd_codes=["853710"],
            partner_code=276,
            max_records=50,
        )

        ingestion_run_ids.append(result.ingestion_run_id)

        assert result.records_received == 1
        assert result.records_inserted == 0
        assert result.records_updated == 0
        assert result.records_rejected == 1
        assert result.status == "completed_with_rejections"

    finally:
        _cleanup_test_data(
            db=db,
            trade_source_record_ids=test_trade_record_ids,
            ingestion_run_ids=ingestion_run_ids,
        )
        db.close()


if __name__ == "__main__":
    test_ingestion_insert_and_idempotent_update()
    print("PASS insert/idempotent update")

    test_ingestion_rejects_unknown_country()
    print("PASS unknown country rejection")

    print("Trade ingestion service tests passed.")
