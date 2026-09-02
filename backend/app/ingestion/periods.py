from __future__ import annotations

from datetime import date


def next_annual_period(latest_period: date | None) -> str | None:
    """Return the next annual YYYY period after the stored period."""
    if latest_period is None:
        return None

    return str(latest_period.year + 1)


def parse_annual_period(period: str) -> int:
    """Validate and return an annual YYYY period as an integer."""
    text = str(period).strip()

    if len(text) != 4 or not text.isdigit():
        raise ValueError("Annual period must use YYYY.")

    return int(text)


def is_current_or_future_year(period: str, today: date | None = None) -> bool:
    """Return True when an annual period is the current or a future year."""
    year = parse_annual_period(period)
    reference_date = today or date.today()
    return year >= reference_date.year
