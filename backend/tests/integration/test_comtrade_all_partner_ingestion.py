from datetime import date

from app.db.session import SessionLocal
from app.ingestion.trade_ingestion import TradeIngestionService
from app.integrations.trade.models import TradeDataRecord
from app.integrations.trade.provider import TradeDataProvider
from app.models import TradeData


class FakeAllPartnerProvider(TradeDataProvider):
    def __init__(self, records):
        self.records = records
        self.received_partner_codes = None

    @property
    def provider_name(self) -> str:
        return "Fake All Partner Provider"

    def fetch_trade_data(self, **kwargs):
        raise AssertionError(
            "All-partner ingestion should use " "fetch_all_partner_trade_data()."
        )

    def fetch_all_partner_trade_data(
        self,
        *,
        reporter_code: int,
        period: str,
        flow_code: str,
        cmd_codes: list[str],
        partner_codes: list[int],
        max_records: int = 500,
    ):
        self.received_partner_codes = list(partner_codes)
        return self.records


def _record(
    *,
    partner_code: int,
    partner_iso3: str,
    partner_name: str,
    value: float,
    source_id: str,
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
        is_aggregate=True,
        partner2_code=0,
        partner2_iso3="W00",
        partner2_name="World",
    )


def test_all_partner_ingestion_reads_codes_from_country_master():
    db = SessionLocal()

    test_ids = {
        "TEST-DB-ALL-PARTNER-DEU",
        "TEST-DB-ALL-PARTNER-USA",
    }

    try:
        records = [
            _record(
                partner_code=276,
                partner_iso3="DEU",
                partner_name="Germany",
                value=101_000_000,
                source_id="TEST-DB-ALL-PARTNER-DEU",
            ),
            _record(
                partner_code=840,
                partner_iso3="USA",
                partner_name="United States of America",
                value=202_000_000,
                source_id="TEST-DB-ALL-PARTNER-USA",
            ),
        ]

        provider = FakeAllPartnerProvider(records)

        result = TradeIngestionService(
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

        assert result.records_received == 2
        assert result.aggregate_records == 2
        assert result.records_inserted == 2
        assert result.records_updated == 0
        assert result.records_rejected == 0

        assert provider.received_partner_codes is not None
        assert provider.received_partner_codes
        assert 276 in provider.received_partner_codes
        assert 840 in provider.received_partner_codes
        assert 699 not in provider.received_partner_codes

        persisted = (
            db.query(TradeData).filter(TradeData.source_record_id.in_(test_ids)).all()
        )

        assert len(persisted) == 2

        print("PASS DB-driven all-partner ingestion")
        print(
            "Partner codes supplied by country master: "
            f"{len(provider.received_partner_codes)}"
        )
        print("Records inserted: " f"{result.records_inserted}")

    finally:
        db.rollback()

        db.query(TradeData).filter(TradeData.source_record_id.in_(test_ids)).delete(
            synchronize_session=False
        )

        db.commit()
        db.close()


if __name__ == "__main__":
    test_all_partner_ingestion_reads_codes_from_country_master()
    print("DB-driven all-partner ingestion test passed.")
