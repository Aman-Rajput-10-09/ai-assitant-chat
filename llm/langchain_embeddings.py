import os

from langchain_ollama import OllamaEmbeddings


class LangChainEmbeddingClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model = model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self._embeddings = OllamaEmbeddings(model=self._model, base_url=self._base_url)

    @property
    def embeddings(self) -> OllamaEmbeddings:
        return self._embeddings

