from collections import defaultdict, deque

from langchain_core.messages import BaseMessage
from langchain_core.chat_history import InMemoryChatMessageHistory


class ChatMemoryService:
    def __init__(self, window_size: int = 7) -> None:
        self._window_size = window_size
        self._histories: dict[str, InMemoryChatMessageHistory] = defaultdict(InMemoryChatMessageHistory)

    def get_recent_messages(self, scope: str) -> list[BaseMessage]:
        history = self._histories[scope]
        return history.messages[-self._window_size * 2 :]

    def add_exchange(self, scope: str, messages: list[BaseMessage]) -> None:
        history = self._histories[scope]
        history.add_messages(messages)
        history.messages = history.messages[-self._window_size * 2 :]
