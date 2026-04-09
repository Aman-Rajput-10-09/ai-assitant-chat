from typing import Any

from pydantic import BaseModel, Field

from models.domain import Student


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)


class AskResponse(BaseModel):
    answer: str
    data: list[Student]
    meta: dict[str, Any]
