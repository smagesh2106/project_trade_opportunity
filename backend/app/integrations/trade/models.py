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

    # UN Comtrade second partner/area dimension.
    # These fields are provider metadata and are not persisted in TradeData.
    partner2_code: int | None = None
    partner2_iso3: str | None = None
    partner2_name: str | None = None

    @property
    def is_country_level_aggregate(self) -> bool:
        """Return True only for canonical country-to-country totals.

        A canonical country-level aggregate must have:
        - is_aggregate=True
        - a real positive partner code
        - a three-letter alphabetic ISO3 country code
        - partner2 representing World (normally code 0)

        Comtrade aggregate/area identifiers such as S19 are deliberately
        excluded because they are not ISO alpha-3 country codes.
        """
        partner_iso3 = (self.partner_iso3 or "").strip().upper()

        return (
            self.is_aggregate
            and self.partner_code > 0
            and len(partner_iso3) == 3
            and partner_iso3.isalpha()
            and self.partner2_code in {0, None}
        )

    @property
    def period_year(self) -> int:
        return self.period_start.year
