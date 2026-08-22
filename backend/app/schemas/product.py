from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductAliasResponse(BaseModel):
    id: int
    alias: str
    language: str | None = None
    source: str | None = None
    confidence: float | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ProductHSCodeResponse(BaseModel):
    id: int
    code: str
    description: str
    level: int
    mapping_type: str | None = None
    confidence: float | None = None
    source: str | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    category: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    aliases: list[ProductAliasResponse]
    hs_codes: list[ProductHSCodeResponse]
