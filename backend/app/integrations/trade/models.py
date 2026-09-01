from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TradeDataRecord:
    """Normalized provider-independent trade observation."""

    provider: str

    reporter_code: int
    reporter_iso3: str | None
    reporter_name: str | None

    partner_code: int
    partner_iso3: str | None
    partner_name: str | None

    hs_code: str
    hs_description: str | None

    period_start: date
    period_end: date | None
    period_type: str

    trade_flow: str

    trade_value_usd: float | None
    trade_value_currency: str | None

    quantity: float | None
    quantity_unit: str | None

    source_record_id: str | None
    data_version: str | None
    is_aggregate: bool = False

    @property
    def period_year(self) -> int:
        return self.period_start.year
