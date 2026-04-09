import json
import os

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from llm.prompt_builder import (
    FILTER_OUTPUT_SCHEMA,
    build_filter_prompt,
    build_no_results_prompt,
)
from models.filters import FilterExtractionResult


ALLOWED_FILTER_FIELDS = {"name", "cgpa", "skills", "activities", "projects"}


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self._timeout_seconds = timeout_seconds

    async def extract_filters(self, question: str, role: str) -> FilterExtractionResult:
        content = await self._generate(
            prompt=build_filter_prompt(question=question, role=role),
            response_format=FILTER_OUTPUT_SCHEMA,
        )

        try:
            parsed_content = json.loads(content)
            result = FilterExtractionResult.model_validate(parsed_content)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ollama returned invalid JSON.",
            ) from exc

        sanitized_filters = {
            field_name: condition
            for field_name, condition in result.filters.items()
            if field_name in ALLOWED_FILTER_FIELDS
        }
        return FilterExtractionResult(filters=sanitized_filters)

    async def generate_no_results_answer(
        self,
        question: str,
        role: str,
        filters: dict[str, object],
    ) -> str:
        try:
            content = await self._generate(
                prompt=build_no_results_prompt(question=question, role=role, filters=filters),
            )
        except HTTPException:
            return self._fallback_no_results_answer(question)

        answer = content.strip().replace("\n", " ")
        if not answer:
            return self._fallback_no_results_answer(question)
        return answer

    async def _generate(
        self,
        prompt: str,
        response_format: dict[str, object] | None = None,
    ) -> str:
        payload: dict[str, object] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if response_format is not None:
            payload["format"] = response_format

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(f"{self._base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to reach Ollama: {exc}",
            ) from exc

        return response.json().get("response", "")

    def _fallback_no_results_answer(self, question: str) -> str:
        return f"No students matched the query '{question}'. Please try a broader or more specific request."
