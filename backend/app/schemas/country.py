from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CountryResponse(BaseModel):
    id: int
    iso2: str
    iso3: str
    name: str
    official_name: str | None = None
    region: str | None = None
    subregion: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )