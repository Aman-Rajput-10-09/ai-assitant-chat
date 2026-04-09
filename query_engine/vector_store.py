import math
from dataclasses import dataclass


@dataclass
class VectorRecord:
    id: str
    text: str
    vector: list[float]
    metadata: dict[str, object]
    score: float = 0.0


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._records: list[VectorRecord] = []

    def upsert(self, records: list[VectorRecord]) -> None:
        self._records = records

    def search(self, query_vector: list[float], top_k: int = 3) -> list[VectorRecord]:
        ranked: list[VectorRecord] = []
        for record in self._records:
            ranked.append(
                VectorRecord(
                    id=record.id,
                    text=record.text,
                    vector=record.vector,
                    metadata=record.metadata,
                    score=self._cosine_similarity(query_vector, record.vector),
                )
            )
        ranked.sort(key=lambda record: record.score, reverse=True)
        return ranked[:top_k]

    def _cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0

        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)
