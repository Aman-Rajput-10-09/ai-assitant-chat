import re

from models.domain import Student
from query_engine.vector_store import InMemoryVectorStore, VectorRecord


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class StudentRetriever:
    def __init__(self, vector_store: InMemoryVectorStore) -> None:
        self._vector_store = vector_store
        self._students_by_id: dict[str, Student] = {}

    def index_students(self, students: list[Student], vectors: list[list[float]]) -> None:
        records: list[VectorRecord] = []
        self._students_by_id = {}

        for student, vector in zip(students, vectors):
            student_id = student.name.casefold()
            self._students_by_id[student_id] = student
            records.append(
                VectorRecord(
                    id=student_id,
                    text=self._student_profile_text(student),
                    vector=vector,
                    metadata={"name": student.name},
                )
            )

        self._vector_store.upsert(records)

    def retrieve(self, query_text: str, query_vector: list[float], top_k: int = 3) -> list[Student]:
        records = self._vector_store.search(query_vector=query_vector, top_k=max(top_k * 2, 6))
        reranked_records = sorted(
            records,
            key=lambda record: self._hybrid_score(query_text=query_text, record=record),
            reverse=True,
        )
        return [
            self._students_by_id[record.id]
            for record in reranked_records[:top_k]
            if record.id in self._students_by_id
        ]

    def student_documents(self, students: list[Student]) -> list[str]:
        return [self._student_profile_text(student) for student in students]

    def _student_profile_text(self, student: Student) -> str:
        return (
            f"Student name: {student.name}. "
            f"CGPA: {student.cgpa}. "
            f"Skills: {', '.join(student.skills)}. "
            f"Activities: {', '.join(student.activities)}. "
            f"Projects: {', '.join(student.projects)}."
        )

    def _hybrid_score(self, query_text: str, record: VectorRecord) -> float:
        query_tokens = set(TOKEN_PATTERN.findall(query_text.casefold()))
        document_tokens = set(TOKEN_PATTERN.findall(record.text.casefold()))
        token_overlap = len(query_tokens & document_tokens)

        soft_skill_bonus = 0.0
        if {"communication", "leadership"} & query_tokens and {"communication", "leadership"} & document_tokens:
            soft_skill_bonus += 2.0
        if "teamwork" in query_tokens and "teamwork" in document_tokens:
            soft_skill_bonus += 1.0

        lexical_score = token_overlap + soft_skill_bonus
        semantic_score = record.score

        return lexical_score * 10 + semantic_score
