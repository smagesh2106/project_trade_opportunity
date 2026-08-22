from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class HSVersionResponse(BaseModel):
    id: int
    name: str
    version: str
    effective_from: date | None = None
    effective_to: date | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )