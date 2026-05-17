from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class TruncationStrategy(Enum):
    DROP_OLDEST = "drop_oldest"
    SUMMARIZE = "summarize"


@dataclass
class BudgetConfig:
    max_tokens: int = 8192
    model_name: str = "qwen3-max"
    strategy: TruncationStrategy = TruncationStrategy.DROP_OLDEST
    tokenizer_fn: Optional[Callable[[str], int]] = None


class ContextBudget:
    """Token counting and budget management with fallback chain."""

    def __init__(self, config: Optional[BudgetConfig] = None):
        self.config = config or BudgetConfig()
        self._tokenizer = self._init_tokenizer()

    def _init_tokenizer(self) -> Callable[[str], int]:
        if self.config.tokenizer_fn:
            return self.config.tokenizer_fn
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return lambda text: len(enc.encode(text))
        except ImportError:
            return lambda text: len(text) // 2

    def count_tokens(self, text: str) -> int:
        return self._tokenizer(text)

    def count_messages(self, messages: list) -> int:
        total = 0
        for msg in messages:
            content = msg.content if hasattr(msg, "content") else msg.get("content", "")
            if isinstance(content, str):
                total += self.count_tokens(content)
        return total

    def within_budget(self, messages: list) -> bool:
        return self.count_messages(messages) <= self.config.max_tokens

    def remaining(self, messages: list) -> int:
        return self.config.max_tokens - self.count_messages(messages)

    def truncate_messages(self, messages: list, budget: int = None) -> list:
        target = budget or self.config.max_tokens
        if self.count_messages(messages) <= target:
            return messages
        if self.config.strategy == TruncationStrategy.DROP_OLDEST:
            return self._drop_oldest(messages, target)
        return messages[-10:]

    def _drop_oldest(self, messages: list, target: int) -> list:
        working = list(messages)
        while len(working) > 1 and self.count_messages(working) > target:
            working.pop(0)
        return working
