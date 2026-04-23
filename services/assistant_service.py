from functools import lru_cache

from data.student_repository import StudentRepository
from llm.filter_normalizer import FilterNormalizer
from llm.langchain_client import LangChainOllamaClient
from llm.langchain_embeddings import LangChainEmbeddingClient
from llm.rule_based_parser import RuleBasedParser
from models.api import AskRequest, AskResponse
from models.domain import Student
from query_engine.chroma_retriever import ChromaStudentRetriever
from query_engine.filter_engine import QueryEngine
from query_engine.ranking_engine import RankingEngine
from services.chat_memory_service import ChatMemoryService


class AssistantService:
    def __init__(
        self,
        llm_client: LangChainOllamaClient,
        query_engine: QueryEngine,
        rule_parser: RuleBasedParser,
        filter_normalizer: FilterNormalizer,
        ranking_engine: RankingEngine,
        retriever: ChromaStudentRetriever,
        memory_service: ChatMemoryService,
        student_repository: StudentRepository,
    ) -> None:
        self._llm_client = llm_client
        self._query_engine = query_engine
        self._rule_parser = rule_parser
        self._filter_normalizer = filter_normalizer
        self._ranking_engine = ranking_engine
        self._retriever = retriever
        self._memory_service = memory_service
        self._student_repository = student_repository

    async def ask(self, payload: AskRequest) -> AskResponse:
        students = await self._load_students()
        self._retriever.ensure_index(students)
        memory_scope = self._memory_scope(payload)
        history = self._memory_service.get_recent_messages(memory_scope)

        llm_result = await self._llm_client.extract_filters(
            question=payload.question,
            role=payload.role,
            history=history,
        )
        rule_result = self._rule_parser.parse(payload.question)
        final_filters = self._filter_normalizer.normalize(llm_result, rule_result)

        ranking_applied = self._ranking_engine.should_rank(payload.question)
        final_filters = self._adjust_filters_for_ranking(
            question=payload.question,
            final_filters=final_filters,
            llm_filters=llm_result.filters,
            rule_filters=rule_result.filters,
            ranking_applied=ranking_applied,
        )

        if final_filters.filters:
            matched_students = self._query_engine.filter_data(
                data=students,
                filters=final_filters.filters,
            )
        else:
            matched_students = []

        if ranking_applied and not final_filters.filters:
            matched_students = students

        semantic_students = self._retrieve_semantic_students(payload.question, students)
        if not matched_students and self._should_use_semantic_fallback(payload.question, final_filters.filters):
            matched_students = semantic_students

        selected_students = matched_students
        if ranking_applied:
            selected_students = self._ranking_engine.rank_students(selected_students, payload.question)

        requested_limit = self._ranking_engine.requested_result_limit(payload.question)
        if requested_limit is not None:
            selected_students = selected_students[:requested_limit]

        if selected_students:
            answer = self._build_success_answer(selected_students, requested_limit)
        else:
            answer = await self._llm_client.generate_answer(
                question=payload.question,
                role=payload.role,
                history=history,
                students=selected_students,
                requested_limit=requested_limit,
                no_results=True,
            )
        user_message, ai_message = self._llm_client.build_exchange_messages(
            question=payload.question,
            answer=answer,
        )
        self._memory_service.add_exchange(memory_scope, [user_message, ai_message])

        return AskResponse(
            answer=answer,
            data=selected_students,
            meta={
                "role": payload.role,
                "professor_id": payload.professor_id,
                "matched_count": len(selected_students),
            },
        )

    def _adjust_filters_for_ranking(
        self,
        question: str,
        final_filters,
        llm_filters: dict,
        rule_filters: dict,
        ranking_applied: bool,
    ):
        if not ranking_applied:
            return final_filters

        normalized_question = question.casefold()
        if not self._has_explicit_filter_intent(normalized_question):
            final_filters.filters.clear()
            return final_filters

        if "cgpa" not in normalized_question and "cgpa" in final_filters.filters:
            if "cgpa" in llm_filters and "cgpa" not in rule_filters:
                final_filters.filters.pop("cgpa", None)
        return final_filters

    def _retrieve_semantic_students(self, question: str, students: list[Student]) -> list[Student]:
        documents = self._retriever.retrieve(question=question, top_k=3)
        student_names: list[str] = []
        for document in documents:
            name = str(document.metadata.get("student_name", ""))
            if name and name not in student_names:
                student_names.append(name)

        students_by_name = {student.name: student for student in students}
        return [students_by_name[name] for name in student_names if name in students_by_name]

    def _should_use_semantic_fallback(
        self,
        question: str,
        filters: dict,
    ) -> bool:
        if not filters:
            return True

        normalized_question = question.casefold()
        broad_intent_keywords = {
            "interested in",
            "good at",
            "strong in",
            "strong at",
            "best in",
            "background in",
            "experienced in",
            "communication",
            "leadership",
            "teamwork",
            "technical",
            "ai",
            "backend",
            "frontend",
            "software",
            "startup",
        }
        return any(keyword in normalized_question for keyword in broad_intent_keywords)

    def _build_success_answer(
        self,
        students: list[Student],
        requested_limit: int | None,
    ) -> str:
        if requested_limit == 1 or len(students) == 1:
            return f"{students[0].name} is the best match for this request."

        if len(students) == 2:
            return f"{students[0].name} and {students[1].name} are good matches for this request."

        if len(students) == 3:
            return (
                f"I found 3 relevant students for this request: {students[0].name}, "
                f"{students[1].name}, and {students[2].name}."
            )

        return f"I found {len(students)} relevant students for this request."

    def _has_explicit_filter_intent(self, normalized_question: str) -> bool:
        explicit_indicators = {
            "cgpa",
            "skill",
            "skills",
            "project",
            "projects",
            "activity",
            "activities",
            "hackathon",
            "research",
            "communication",
            "leadership",
            "teamwork",
            "technical",
            "ai",
            "backend",
            "frontend",
            "software",
            "startup",
            ">",
            "<",
            "=",
            "with",
            "who have",
            "students in",
        }
        return any(indicator in normalized_question for indicator in explicit_indicators)

    def _memory_scope(self, payload: AskRequest) -> str:
        if payload.professor_id:
            return f"{payload.role.casefold()}:{payload.professor_id.casefold()}"
        return payload.role.casefold()

    async def _load_students(self) -> list[Student]:
        students = await self._student_repository.list_students()
        if not students:
            raise ValueError("No student profiles were found in the database.")
        return students


@lru_cache
def get_assistant_service() -> AssistantService:
    embeddings = LangChainEmbeddingClient().embeddings
    return AssistantService(
        llm_client=LangChainOllamaClient(),
        query_engine=QueryEngine(),
        rule_parser=RuleBasedParser(),
        filter_normalizer=FilterNormalizer(),
        ranking_engine=RankingEngine(),
        retriever=ChromaStudentRetriever(
            embeddings=embeddings,
            persist_directory=".chroma_student_db",
        ),
        memory_service=ChatMemoryService(window_size=7),
        student_repository=StudentRepository(),
    )
