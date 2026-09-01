from datetime import date
import calendar
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.integrations.trade.models import TradeDataRecord
from app.integrations.trade.provider import TradeDataProvider


class ComtradeAPIError(RuntimeError):
    """Raised when the UN Comtrade API request cannot be completed."""


class ComtradeProvider(TradeDataProvider):
    """UN Comtrade adapter.

    No subscription key:
        Uses the public preview API.

    Subscription key supplied:
        Uses the authenticated final-data API.
    """

    PUBLIC_BASE_URL = "https://comtradeapi.un.org/public/v1/preview"
    AUTH_BASE_URL = "https://comtradeapi.un.org/data/v1/get"

    def __init__(
        self,
        subscription_key: str | None = None,
        *,
        timeout_seconds: float = 30.0,
        user_agent: str = "TradeOpportunityExplorer/0.1",
    ):
        self.subscription_key = subscription_key or None
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    @property
    def provider_name(self) -> str:
        return "UN Comtrade"

    @property
    def is_authenticated(self) -> bool:
        return bool(self.subscription_key)

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
        self._validate_common(
            reporter_code=reporter_code,
            period=period,
            flow_code=flow_code,
            cmd_codes=cmd_codes,
            max_records=max_records,
        )

        return self._fetch(
            frequency="A",
            reporter_code=reporter_code,
            period=period,
            flow_code=flow_code,
            cmd_codes=cmd_codes,
            partner_code=partner_code,
            max_records=max_records,
        )

    def fetch_monthly_trade_data(
        self,
        *,
        reporter_code: int,
        period: str,
        flow_code: str,
        cmd_codes: list[str],
        partner_code: int | None = None,
        max_records: int = 500,
    ) -> list[TradeDataRecord]:
        self._validate_common(
            reporter_code=reporter_code,
            period=period,
            flow_code=flow_code,
            cmd_codes=cmd_codes,
            max_records=max_records,
            monthly=True,
        )

        return self._fetch(
            frequency="M",
            reporter_code=reporter_code,
            period=period,
            flow_code=flow_code,
            cmd_codes=cmd_codes,
            partner_code=partner_code,
            max_records=max_records,
        )

    def _fetch(
        self,
        *,
        frequency: str,
        reporter_code: int,
        period: str,
        flow_code: str,
        cmd_codes: list[str],
        partner_code: int | None,
        max_records: int,
    ) -> list[TradeDataRecord]:
        base_url = self.AUTH_BASE_URL if self.subscription_key else self.PUBLIC_BASE_URL

        params = {
            "reporterCode": str(reporter_code),
            "period": period,
            "flowCode": flow_code,
            "cmdCode": ",".join(cmd_codes),
            "maxRecords": str(max_records),
            "format": "json",
            "includeDesc": "true",
        }

        # Omit partnerCode to request all partners.
        # partnerCode=0 is the World aggregate.
        if partner_code is not None:
            params["partnerCode"] = str(partner_code)

        if self.subscription_key:
            params["subscription-key"] = self.subscription_key

        url = f"{base_url}/C/{frequency}/HS?" f"{urlencode(params)}"

        payload = self._get_json(url)
        raw_records = payload.get("data", [])

        if raw_records is None:
            return []

        if not isinstance(raw_records, list):
            raise ComtradeAPIError("UN Comtrade field 'data' is not a list.")

        records: list[TradeDataRecord] = []

        for raw in raw_records:
            if not isinstance(raw, dict):
                continue

            record = self._parse_record(raw)
            if record is not None:
                records.append(record)

        return records

    def _get_json(self, url: str) -> dict:
        request = Request(
            url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": self.user_agent,
            },
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            raise ComtradeAPIError(
                f"UN Comtrade HTTP {exc.code}: {body or exc.reason}"
            ) from exc
        except URLError as exc:
            raise ComtradeAPIError(
                f"Unable to reach UN Comtrade: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise ComtradeAPIError("UN Comtrade request timed out.") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ComtradeAPIError("UN Comtrade returned invalid JSON.") from exc

        if not isinstance(payload, dict):
            raise ComtradeAPIError("UN Comtrade returned a non-object JSON response.")

        error = payload.get("error")
        if error:
            raise ComtradeAPIError(f"UN Comtrade API error: {error}")

        return payload

    def _parse_record(self, raw: dict) -> TradeDataRecord | None:
        period = self._parse_period(raw.get("period"))
        hs_code = self._text(raw.get("cmdCode"))

        if period is None or not hs_code:
            return None

        return TradeDataRecord(
            provider=self.provider_name,
            reporter_code=self._int(raw.get("reporterCode")),
            reporter_iso3=self._text(raw.get("reporterISO")),
            reporter_name=self._text(raw.get("reporterDesc")),
            partner_code=self._int(raw.get("partnerCode")),
            partner_iso3=self._text(raw.get("partnerISO")),
            partner_name=self._text(raw.get("partnerDesc")),
            hs_code=hs_code,
            hs_description=self._text(raw.get("cmdDesc") or raw.get("cmdDescE")),
            period_start=period,
            period_end=self._period_end(period),
            period_type="annual" if len(str(raw.get("period"))) == 4 else "monthly",
            trade_flow=self._normalize_trade_flow(raw.get("flowCode")),
            trade_value_usd=self._float(
                raw.get("primaryValue")
                if raw.get("primaryValue") is not None
                else raw.get("primaryValueUsd")
            ),
            trade_value_currency="USD",
            quantity=self._float(
                raw.get("netWgt") if raw.get("netWgt") is not None else raw.get("qty")
            ),
            quantity_unit=self._text(raw.get("qtyUnitAbbr") or raw.get("qtyUnitCode")),
            source_record_id=self._build_source_record_id(raw),
            data_version=self._text(raw.get("classificationCode")),
            is_aggregate=bool(raw.get("isAggregate")),
        )

    @staticmethod
    def _normalize_trade_flow(value) -> str:
        flow = str(value or "").strip().upper()
        mapping = {"M": "import", "X": "export"}
        try:
            return mapping[flow]
        except KeyError as exc:
            raise ComtradeAPIError(
                f"Unsupported UN Comtrade flow code: {value!r}"
            ) from exc

    @staticmethod
    def _validate_common(
        *,
        reporter_code: int,
        period: str,
        flow_code: str,
        cmd_codes: list[str],
        max_records: int,
        monthly: bool = False,
    ) -> None:
        if reporter_code <= 0:
            raise ValueError("reporter_code must be a positive M49 code.")

        period_text = str(period).strip()
        if monthly:
            if len(period_text) != 6 or not period_text.isdigit():
                raise ValueError("Monthly period must use YYYYMM.")
            month = int(period_text[4:6])
            if not 1 <= month <= 12:
                raise ValueError("Monthly period contains an invalid month.")
        else:
            if len(period_text) != 4 or not period_text.isdigit():
                raise ValueError("Annual period must use YYYY.")

        if flow_code not in {"M", "X", "RX", "RM", "DX", "FM"}:
            raise ValueError("flow_code must be one of M, X, RX, RM, DX, FM.")

        if not cmd_codes:
            raise ValueError("At least one HS command code is required.")

        if len(cmd_codes) > 20:
            raise ValueError("At most 20 commodity codes may be requested.")

        if any(not str(code).strip() for code in cmd_codes):
            raise ValueError("HS command codes cannot be blank.")

        if max_records < 1:
            raise ValueError("max_records must be at least 1.")

        if max_records > 500:
            raise ValueError(
                "The public-preview provider mode is limited to 500 records."
            )

    @staticmethod
    def _parse_period(value) -> date | None:
        if value is None:
            return None

        text = str(value).strip()

        if len(text) == 4 and text.isdigit():
            return date(int(text), 1, 1)

        if len(text) == 6 and text.isdigit():
            year = int(text[:4])
            month = int(text[4:6])
            if 1 <= month <= 12:
                return date(year, month, 1)

        return None

    @staticmethod
    def _period_end(start: date) -> date:
        if start.month == 1 and start.day == 1:
            return date(start.year, 12, 31)

        return date(
            start.year,
            start.month,
            calendar.monthrange(start.year, start.month)[1],
        )

    @staticmethod
    def _int(value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _float(value) -> float | None:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _text(value) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _build_source_record_id(raw: dict) -> str:
        return ":".join(
            [
                "UN-COMTRADE",
                str(raw.get("reporterCode", "")),
                str(raw.get("partnerCode", "")),
                str(raw.get("partner2Code", "")),
                str(raw.get("cmdCode", "")),
                str(raw.get("period", "")),
                str(raw.get("flowCode", "")),
                str(raw.get("customsCode", "")),
                str(raw.get("motCode", "")),
                str(raw.get("typeCode", "")),
            ]
        )
