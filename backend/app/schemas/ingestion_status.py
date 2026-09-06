from datetime import datetime

from pydantic import BaseModel


class IngestionStatusResponse(BaseModel):
    status: str
    source: str | None = None

    last_run_id: int | None = None
    last_run_status: str | None = None

    last_run_started_at: datetime | None = None
    last_run_completed_at: datetime | None = None

    latest_data_period: str | None = None

    records_received: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_rejected: int = 0

    error_message: str | None = None
