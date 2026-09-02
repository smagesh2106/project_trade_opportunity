from datetime import date

from app.db.session import SessionLocal
from app.ingestion.trade_ingestion import TradeIngestionService
from app.integrations.trade.models import TradeDataRecord
from app.integrations.trade.provider import TradeDataProvider
from app.models import TradeData


class FakeAllPartnerProvider(TradeDataProvider):
    @property
    def provider_name(self) -> str:
        return "Fake All Partner Provider"

    def __init__(self, records):
        self.records = records

    def fetch_trade_data(self, **kwargs):
        return self.records


def _record(
    *,
    partner_code: int,
    partner_iso3: str,
    partner_name: str,
    value: float,
    source_id: str,
    is_aggregate: bool = True,
    partner2_code: int | None = 0,
) -> TradeDataRecord:
    return TradeDataRecord(
        provider="Fake All Partner Provider",
        reporter_code=699,
        reporter_iso3="IND",
        reporter_name="India",
        partner_code=partner_code,
        partner_iso3=partner_iso3,
        partner_name=partner_name,
        hs_code="853710",
        hs_description="For a voltage not exceeding 1,000 V",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        period_type="annual",
        trade_flow="import",
        trade_value_usd=value,
        trade_value_currency="USD",
        quantity=100,
        quantity_unit="kg",
        source_record_id=source_id,
        data_version="test-v1",
        is_aggregate=is_aggregate,
        partner2_code=partner2_code,
        partner2_iso3="W00" if partner2_code == 0 else None,
        partner2_name="World" if partner2_code == 0 else None,
    )


def test_all_partner_ingestion():
    db = SessionLocal()

    test_source_ids = {
        "TEST-ALL-PARTNER-DEU",
        "TEST-ALL-PARTNER-USA",
    }

    all_test_ids = {
        "TEST-ALL-PARTNER-DEU",
        "TEST-ALL-PARTNER-USA",
        "TEST-ALL-PARTNER-S19",
        "TEST-ALL-PARTNER-DETAIL",
    }

    try:
        # Make the test safe to rerun.
        db.query(TradeData).filter(
            TradeData.source_record_id.in_(all_test_ids)
        ).delete(synchronize_session=False)
        db.commit()

        records = [
            _record(
                partner_code=276,
                partner_iso3="DEU",
                partner_name="Germany",
                value=101_000_000,
                source_id="TEST-ALL-PARTNER-DEU",
            ),
            _record(
                partner_code=840,
                partner_iso3="USA",
                partner_name="United States",
                value=202_000_000,
                source_id="TEST-ALL-PARTNER-USA",
            ),
            # Comtrade aggregate/area code, not a country ISO3.
            _record(
                partner_code=0,
                partner_iso3="S19",
                partner_name="Other Asia, nes",
                value=999,
                source_id="TEST-ALL-PARTNER-S19",
            ),
            # Detail row.
            _record(
                partner_code=276,
                partner_iso3="DEU",
                partner_name="Germany",
                value=888,
                source_id="TEST-ALL-PARTNER-DETAIL",
                is_aggregate=False,
                partner2_code=36,
            ),
        ]

        provider = FakeAllPartnerProvider(records)

        first = TradeIngestionService(
            db=db,
            provider=provider,
        ).ingest(
            reporter_code=699,
            period="2025",
            flow_code="M",
            cmd_codes=["853710"],
            partner_code=None,
            max_records=500,
        )

        assert first.records_received == 4
        assert first.aggregate_records == 2
        assert first.detail_records_skipped == 2
        assert first.records_inserted == 2
        assert first.records_updated == 0
        assert first.records_rejected == 0

        second = TradeIngestionService(
            db=db,
            provider=provider,
        ).ingest(
            reporter_code=699,
            period="2025",
            flow_code="M",
            cmd_codes=["853710"],
            partner_code=None,
            max_records=500,
        )

        assert second.records_received == 4
        assert second.aggregate_records == 2
        assert second.detail_records_skipped == 2
        assert second.records_inserted == 0
        assert second.records_updated == 2
        assert second.records_rejected == 0

        persisted = (
            db.query(TradeData)
            .filter(
                TradeData.source_record_id.in_(test_source_ids)
            )
            .all()
        )

        assert len(persisted) == 2

        values = {
            row.source_record_id: float(row.trade_value_usd)
            for row in persisted
        }

        assert values["TEST-ALL-PARTNER-DEU"] == 101_000_000
        assert values["TEST-ALL-PARTNER-USA"] == 202_000_000

        forbidden_rows = (
            db.query(TradeData)
            .filter(
                TradeData.source_record_id.in_(
                    {
                        "TEST-ALL-PARTNER-S19",
                        "TEST-ALL-PARTNER-DETAIL",
                    }
                )
            )
            .all()
        )

        assert forbidden_rows == []

        print("PASS all-partner ingestion")
        print(
            "First run : "
            f"inserted={first.records_inserted}, "
            f"updated={first.records_updated}"
        )
        print(
            "Second run: "
            f"inserted={second.records_inserted}, "
            f"updated={second.records_updated}"
        )
        print(
            "Canonical country rows persisted: "
            f"{len(persisted)}"
        )

    finally:
        db.rollback()

        db.query(TradeData).filter(
            TradeData.source_record_id.in_(all_test_ids)
        ).delete(synchronize_session=False)

        db.commit()
        db.close()


if __name__ == "__main__":
    test_all_partner_ingestion()
    print("All-partner ingestion test passed.")
