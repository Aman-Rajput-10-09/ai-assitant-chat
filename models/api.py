from typing import Any

from pydantic import BaseModel, Field, model_validator

from models.domain import Student


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    professor_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_professor_id(self) -> "AskRequest":
        if self.role.casefold() == "professor" and not self.professor_id:
            raise ValueError("professor_id is required when role is professor.")
        return self


class AskResponse(BaseModel):
    answer: str
    data: list[Student]
    meta: dict[str, Any]
