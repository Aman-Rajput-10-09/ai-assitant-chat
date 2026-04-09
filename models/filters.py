from typing import Any

from pydantic import BaseModel, Field


class FilterCondition(BaseModel):
    gt: float | None = None
    lt: float | None = None
    eq: Any | None = None
    contains: str | None = None


class FilterExtractionResult(BaseModel):
    filters: dict[str, FilterCondition] = Field(default_factory=dict)

