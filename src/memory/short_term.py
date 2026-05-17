from dataclasses import dataclass, field
from typing import Any, Optional
from langchain_core.messages import SystemMessage
from utils.logger_handler import logger


@dataclass
class ShortTermConfig:
    max_messages: int = 20
    max_tokens: int = 4096
    enable_summarization: bool = True
    summarization_llm: Any = None


class ShortTermMemory:
    """Sliding window buffer with optional LLM-based summarization."""

    def __init__(self, config: Optional[ShortTermConfig] = None):
        self.config = config or ShortTermConfig()
        self._messages: list = []
        self._summary: str = ""

    def add_message(self, message) -> None:
        self._messages.append(message)
        self._maybe_trim()

    def add_messages(self, messages: list) -> None:
        self._messages.extend(messages)
        self._maybe_trim()

    def get_messages(self) -> list:
        return list(self._messages)

    def get_context(self) -> list:
        if self._summary:
            return [SystemMessage(content=f"[对话历史摘要] {self._summary}")] + self._messages
        return self.get_messages()

    def _maybe_trim(self) -> None:
        if len(self._messages) <= self.config.max_messages:
            return
        excess = len(self._messages) - self.config.max_messages
        old = self._messages[:excess]
        self._messages = self._messages[excess:]
        if self.config.enable_summarization and old and self.config.summarization_llm:
            try:
                text = "\n".join(
                    m.content[:200] for m in old if hasattr(m, "content") and m.content
                )
                prompt = f"请用一句话总结以下对话:\n{text}"
                response = self.config.summarization_llm.invoke(prompt)
                new = response.content if hasattr(response, "content") else str(response)
                self._summary = f"{self._summary}; {new}" if self._summary else new
            except Exception as e:
                logger.warning(f"[ShortTermMemory] Summarization failed: {e}")

    def clear(self) -> None:
        self._messages.clear()
        self._summary = ""
