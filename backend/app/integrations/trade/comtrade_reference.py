from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPORTERS_URL = "https://comtradeapi.un.org/files/v1/app/reference/Reporters.json"
PARTNER_AREAS_URL = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"


class ComtradeReferenceError(RuntimeError):
    """Raised when a UN Comtrade reference feed cannot be retrieved or parsed."""


@dataclass(frozen=True)
class CountryReference:
    """Canonical country/area identity from UN Comtrade."""

    comtrade_code: int
    iso2: str
    iso3: str
    name: str
    effective_date: datetime | None
    is_group: bool


class ComtradeReferenceClient:
    """Client for the public UN Comtrade country/area reference files."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
        user_agent: str = "TradeOpportunityExplorer/0.1",
    ):
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent

    def fetch_countries(self) -> list[CountryReference]:
        """Fetch and merge current reporter and partner country/area references."""

        reporters = self._fetch_reference_file(REPORTERS_URL)
        partner_areas = self._fetch_reference_file(PARTNER_AREAS_URL)

        merged: dict[str, CountryReference] = {}

        for raw in [*reporters, *partner_areas]:
            item = self._parse_reference(raw)
            if item is None:
                continue

            # Prefer reporter metadata if the same ISO3 appears in both feeds.
            existing = merged.get(item.iso3)
            if existing is None or (
                existing.name == item.iso3
                and item.name != item.iso3
            ):
                merged[item.iso3] = item

        return sorted(
            merged.values(),
            key=lambda item: (item.name.casefold(), item.iso3),
        )

    def _fetch_reference_file(self, url: str) -> list[dict]:
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

            raise ComtradeReferenceError(
                f"UN Comtrade reference HTTP {exc.code}: "
                f"{body or exc.reason}"
            ) from exc
        except URLError as exc:
            raise ComtradeReferenceError(
                f"Unable to reach UN Comtrade reference feed: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise ComtradeReferenceError(
                "UN Comtrade reference request timed out."
            ) from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ComtradeReferenceError(
                f"UN Comtrade reference returned invalid JSON: {url}"
            ) from exc

        if not isinstance(payload, dict):
            raise ComtradeReferenceError(
                f"UN Comtrade reference returned a non-object response: {url}"
            )

        results = payload.get("results", [])
        if not isinstance(results, list):
            raise ComtradeReferenceError(
                f"UN Comtrade reference field 'results' is not a list: {url}"
            )

        return [item for item in results if isinstance(item, dict)]

    @staticmethod
    def _parse_reference(raw: dict) -> CountryReference | None:
        if raw.get("entryExpiredDate"):
            return None

        if bool(raw.get("isGroup")):
            return None

        iso2 = (
            raw.get("reporterCodeIsoAlpha2")
            or raw.get("PartnerCodeIsoAlpha2")
            or raw.get("partnerCodeIsoAlpha2")
        )
        iso3 = (
            raw.get("reporterCodeIsoAlpha3")
            or raw.get("PartnerCodeIsoAlpha3")
            or raw.get("partnerCodeIsoAlpha3")
        )
        name = (
            raw.get("reporterDesc")
            or raw.get("PartnerDesc")
            or raw.get("text")
        )

        iso2 = str(iso2 or "").strip().upper()
        iso3 = str(iso3 or "").strip().upper()
        name = str(name or "").strip()

        # The canonical countries table currently requires ISO alpha-2 and
        # alpha-3 values. This intentionally excludes aggregate/custom groups
        # such as World and "areas, nes".
        if len(iso2) != 2 or len(iso3) != 3 or not name:
            return None

        try:
            comtrade_code = int(
                raw.get("reporterCode")
                or raw.get("PartnerCode")
                or raw.get("partnerCode")
                or raw.get("id")
            )
        except (TypeError, ValueError):
            return None

        effective_date = None
        effective_text = raw.get("entryEffectiveDate")
        if effective_text:
            try:
                effective_date = datetime.fromisoformat(
                    str(effective_text).replace("Z", "+00:00")
                )
            except ValueError:
                effective_date = None

        return CountryReference(
            comtrade_code=comtrade_code,
            iso2=iso2,
            iso3=iso3,
            name=name,
            effective_date=effective_date,
            is_group=False,
        )
