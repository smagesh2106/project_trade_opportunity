from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HSCodeResponse(BaseModel):
    id: int
    hs_version_id: int
    code: str
    description: str
    level: int
    parent_id: int | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )