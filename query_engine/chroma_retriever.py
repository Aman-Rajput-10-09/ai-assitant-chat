from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from models.domain import Student


class ChromaStudentRetriever:
    def __init__(self, embeddings, persist_directory: str | None = None) -> None:
        self._embeddings = embeddings
        self._persist_directory = persist_directory
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=220,
            chunk_overlap=40,
        )
        self._vector_store: Chroma | None = None
        self._indexed = False
        self._signature: tuple[str, ...] = ()

    def ensure_index(self, students: list[Student]) -> None:
        signature = tuple(sorted(student.roll_no for student in students))
        if self._indexed and signature == self._signature:
            return

        documents = self._build_documents(students)
        if self._vector_store is not None:
            self._vector_store.delete_collection()
        self._vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self._embeddings,
            collection_name="student_profiles",
            persist_directory=self._persist_directory,
            collection_metadata={"hnsw:space": "cosine"},
        )
        self._indexed = True
        self._signature = signature

    def retrieve(self, question: str, top_k: int = 4) -> list[Document]:
        if self._vector_store is None:
            return []
        return self._vector_store.similarity_search(question, k=top_k)

    def _build_documents(self, students: list[Student]) -> list[Document]:
        documents: list[Document] = []
        for student in students:
            enriched_profile = self._build_profile_text(student)
            for index, chunk in enumerate(self._splitter.split_text(enriched_profile)):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "student_name": student.name,
                            "roll_no": student.roll_no,
                            "chunk_index": index,
                            "cgpa": student.cgpa,
                        },
                    )
                )
        return documents

    def _build_profile_text(self, student: Student) -> str:
        tags = self._derive_tags(student)
        return (
            f"Student roll number: {student.roll_no}. "
            f"Student name: {student.name}. "
            f"CGPA: {student.cgpa}. "
            f"Skills: {', '.join(student.skills)}. "
            f"Activities: {', '.join(student.activities)}. "
            f"Projects: {', '.join(student.projects)}. "
            f"Profile tags: {', '.join(tags)}."
        )

    def _derive_tags(self, student: Student) -> list[str]:
        skills = {skill.casefold() for skill in student.skills}
        activities = {activity.casefold() for activity in student.activities}
        projects = {project.casefold() for project in student.projects}
        tags: list[str] = []

        if {"python", "java", "node.js", "react", "android development"} & skills:
            tags.append("technical")
            tags.append("software")
        if {"machine learning", "data science", "nlp"} & skills or any(
            "ai" in project for project in projects
        ):
            tags.append("ai")
        if {"communication", "leadership", "teamwork"} & skills:
            tags.append("soft skills")
        if "startup cell" in activities:
            tags.append("startup")
        if "hackathon" in activities:
            tags.append("hackathon")
        if "cp" in activities or any("competitive programming" in project for project in projects):
            tags.append("competitive programming")

        return sorted(set(tags)) or ["student profile"]
