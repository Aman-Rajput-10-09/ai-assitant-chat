import json
import os

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama

from llm.prompt_builder import (
    build_filter_system_prompt,
    build_no_results_system_prompt,
    build_response_system_prompt,
)
from models.domain import Student
from models.filters import FilterExtractionResult


class LangChainOllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        self._json_llm = ChatOllama(
            model=self._model,
            temperature=0,
            base_url=self._base_url,
            format="json",
        )
        self._chat_llm = ChatOllama(
            model=self._model,
            temperature=0.2,
            base_url=self._base_url,
        )
        self._filter_parser = PydanticOutputParser(pydantic_object=FilterExtractionResult)

    async def extract_filters(
        self,
        question: str,
        role: str,
        history: list[BaseMessage],
    ) -> FilterExtractionResult:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "{system_prompt}",
                ),
                MessagesPlaceholder("history", optional=True),
                (
                    "human",
                    "Role: {role}\nQuestion: {question}",
                ),
            ]
        )
        chain = prompt | self._json_llm | self._filter_parser

        try:
            return await chain.ainvoke(
                {
                    "system_prompt": build_filter_system_prompt(
                        self._filter_parser.get_format_instructions()
                    ),
                    "role": role,
                    "question": question,
                    "history": history,
                }
            )
        except Exception:
            return FilterExtractionResult(filters={})

    async def generate_answer(
        self,
        question: str,
        role: str,
        history: list[BaseMessage],
        students: list[Student],
        requested_limit: int | None,
        no_results: bool = False,
    ) -> str:
        system_prompt = (
            build_no_results_system_prompt()
            if no_results
            else build_response_system_prompt()
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("history", optional=True),
                (
                    "human",
                    "Role: {role}\nQuestion: {question}\nRequested limit: {requested_limit}\n"
                    "Selected students: {students_json}",
                ),
            ]
        )
        chain = prompt | self._chat_llm | StrOutputParser()

        students_json = json.dumps(
            [student.model_dump() for student in students],
            ensure_ascii=True,
        )
        try:
            answer = await chain.ainvoke(
                {
                    "role": role,
                    "question": question,
                    "requested_limit": requested_limit or 0,
                    "students_json": students_json,
                    "history": history,
                }
            )
        except Exception:
            return self._fallback_answer(students=students, no_results=no_results)

        cleaned = " ".join(answer.strip().split())
        if cleaned:
            return cleaned
        return self._fallback_answer(students=students, no_results=no_results)

    def build_exchange_messages(self, question: str, answer: str) -> tuple[HumanMessage, AIMessage]:
        return HumanMessage(content=question), AIMessage(content=answer)

    def _fallback_answer(self, students: list[Student], no_results: bool) -> str:
        if no_results:
            return "No students were found for this request. Please try a broader or more specific query."
        if len(students) == 1:
            return f"{students[0].name} is the best match for this request."
        return f"I found {len(students)} students for this request."
