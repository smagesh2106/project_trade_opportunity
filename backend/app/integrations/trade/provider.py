from abc import ABC, abstractmethod
from datetime import date

from app.integrations.trade.models import TradeDataRecord


class TradeDataProvider(ABC):
    """Provider-neutral interface for external merchandise trade data."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch_trade_data(
        self,
        *,
        reporter_code: int,
        period: str,
        flow_code: str,
        cmd_codes: list[str],
        partner_code: int | None = None,
        max_records: int = 500,
    ) -> list[TradeDataRecord]:
        raise NotImplementedError

    def fetch_annual_trade_data(
        self,
        *,
        reporter_code: int,
        year: int,
        flow_code: str,
        cmd_codes: list[str],
        partner_code: int | None = None,
        max_records: int = 500,
    ) -> list[TradeDataRecord]:
        if year < 1900 or year > date.today().year + 1:
            raise ValueError(f"Invalid trade year: {year}")

        return self.fetch_trade_data(
            reporter_code=reporter_code,
            period=str(year),
            flow_code=flow_code,
            cmd_codes=cmd_codes,
            partner_code=partner_code,
            max_records=max_records,
        )
