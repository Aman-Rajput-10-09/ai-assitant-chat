from functools import lru_cache

from llm.client import OllamaClient
from llm.embedding_client import EmbeddingClient
from llm.filter_normalizer import FilterNormalizer
from llm.rule_based_parser import RuleBasedParser
from models.filters import FilterCondition, FilterExtractionResult
from query_engine.retriever import StudentRetriever
from query_engine.filter_engine import QueryEngine
from query_engine.ranking_engine import RankingEngine
from query_engine.vector_store import InMemoryVectorStore
from data.mock_students import MOCK_STUDENTS
from models.api import AskRequest, AskResponse


class AssistantService:
    def __init__(
        self,
        llm_client: OllamaClient,
        query_engine: QueryEngine,
        rule_parser: RuleBasedParser,
        filter_normalizer: FilterNormalizer,
        ranking_engine: RankingEngine,
        embedding_client: EmbeddingClient,
        retriever: StudentRetriever,
    ) -> None:
        self._llm_client = llm_client
        self._query_engine = query_engine
        self._rule_parser = rule_parser
        self._filter_normalizer = filter_normalizer
        self._ranking_engine = ranking_engine
        self._embedding_client = embedding_client
        self._retriever = retriever
        self._retriever_ready = False

    async def ask(self, payload: AskRequest) -> AskResponse:
        llm_result = await self._llm_client.extract_filters(
            question=payload.question,
            role=payload.role,
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
        matched_students = self._query_engine.filter_data(
            data=MOCK_STUDENTS,
            filters=final_filters.filters,
        )
        semantic_matches = await self._retrieve_semantic_matches(payload.question)
        use_semantic_fallback = self._should_use_semantic_fallback(
            question=payload.question,
            filters=final_filters,
            matched_students=matched_students,
        )
        if not matched_students and semantic_matches and use_semantic_fallback:
            matched_students = semantic_matches

        ranked_students = matched_students
        if ranking_applied:
            ranked_students = self._ranking_engine.rank_students(matched_students, payload.question)
        requested_limit = self._ranking_engine.requested_result_limit(payload.question)
        if requested_limit is not None:
            ranked_students = ranked_students[:requested_limit]

        filter_count = len(final_filters.filters)
        if ranked_students:
            answer = self._build_success_answer(
                question=payload.question,
                students=ranked_students,
                filter_count=filter_count,
                ranking_applied=ranking_applied,
                used_semantic_fallback=use_semantic_fallback and bool(semantic_matches),
            )
        else:
            answer = await self._llm_client.generate_no_results_answer(
                question=payload.question,
                role=payload.role,
                filters={key: value.model_dump() for key, value in final_filters.filters.items()},
            )

        return AskResponse(
            answer=answer,
            data=ranked_students,
            meta={
                "role": payload.role,
                "matched_count": len(ranked_students),
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
        if "cgpa" not in normalized_question and "cgpa" in final_filters.filters:
            if "cgpa" in llm_filters and "cgpa" not in rule_filters:
                final_filters.filters.pop("cgpa", None)

        return final_filters

    def _build_success_answer(
        self,
        question: str,
        students: list,
        filter_count: int,
        ranking_applied: bool,
        used_semantic_fallback: bool,
    ) -> str:
        top_student = students[0]
        requested_limit = self._ranking_engine.requested_result_limit(question)

        if requested_limit == 1 and ranking_applied:
            if self._ranking_engine.should_sort_by_cgpa(question):
                return f"{top_student.name} is the top student for this request."
            return f"{top_student.name} is the top student for this request."

        if ranking_applied and self._ranking_engine.should_sort_by_cgpa(question):
            return f"I found {self._student_count_phrase(len(students))} for this request."

        if ranking_applied:
            return f"I found {self._student_count_phrase(len(students))} for this request."

        if used_semantic_fallback:
            return f"I found {self._student_count_phrase(len(students), qualifier='relevant')} for this request."

        return f"I found {self._student_count_phrase(len(students))} for this request."

    def _student_count_phrase(self, count: int, qualifier: str | None = None) -> str:
        noun = "student" if count == 1 else "students"
        if qualifier:
            return f"{count} {qualifier} {noun}"
        return f"{count} {noun}"

    async def _retrieve_semantic_matches(self, question: str) -> list:
        await self._ensure_retriever_index()
        query_vector = (await self._embedding_client.embed_texts([question]))[0]
        return self._retriever.retrieve(query_text=question, query_vector=query_vector, top_k=3)

    async def _ensure_retriever_index(self) -> None:
        if self._retriever_ready:
            return

        student_documents = self._retriever.student_documents(MOCK_STUDENTS)
        vectors = await self._embedding_client.embed_texts(student_documents)
        self._retriever.index_students(MOCK_STUDENTS, vectors)
        self._retriever_ready = True

    def _should_use_semantic_fallback(
        self,
        question: str,
        filters: FilterExtractionResult,
        matched_students: list,
    ) -> bool:
        if matched_students:
            return False

        if not filters.filters:
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
        }

        if not any(keyword in normalized_question for keyword in broad_intent_keywords):
            return False

        return all(self._is_semantic_friendly_filter(condition) for condition in filters.filters.values())

    def _is_semantic_friendly_filter(self, condition: FilterCondition) -> bool:
        return (
            condition.gt is None
            and condition.lt is None
            and (
                isinstance(condition.contains, str)
                or isinstance(condition.eq, str)
            )
        )


@lru_cache
def get_assistant_service() -> AssistantService:
    vector_store = InMemoryVectorStore()
    return AssistantService(
        llm_client=OllamaClient(),
        query_engine=QueryEngine(),
        rule_parser=RuleBasedParser(),
        filter_normalizer=FilterNormalizer(),
        ranking_engine=RankingEngine(),
        embedding_client=EmbeddingClient(),
        retriever=StudentRetriever(vector_store=vector_store),
    )
