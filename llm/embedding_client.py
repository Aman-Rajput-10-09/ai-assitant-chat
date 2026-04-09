import math
import os
import re
from collections import Counter

import httpx


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class EmbeddingClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model = model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self._timeout_seconds = timeout_seconds

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.post(
                    f"{self._base_url}/api/embed",
                    json={"model": self._model, "input": texts},
                )
                response.raise_for_status()
            data = response.json().get("embeddings", [])
            if isinstance(data, list) and data:
                return data
        except httpx.HTTPError:
            pass

        return self._fallback_embed_texts(texts)

    def _fallback_embed_texts(self, texts: list[str]) -> list[list[float]]:
        tokenized = [self._tokenize(text) for text in texts]
        vocabulary = sorted({token for tokens in tokenized for token in tokens})
        if not vocabulary:
            return [[0.0] for _ in texts]

        return [self._to_vector(tokens, vocabulary) for tokens in tokenized]

    def _tokenize(self, text: str) -> list[str]:
        return TOKEN_PATTERN.findall(text.casefold())

    def _to_vector(self, tokens: list[str], vocabulary: list[str]) -> list[float]:
        counts = Counter(tokens)
        vector = [float(counts.get(term, 0)) for term in vocabulary]
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
