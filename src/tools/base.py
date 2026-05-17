from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class ToolCategory(Enum):
    KNOWLEDGE = "knowledge"          # RAG retrieval, internal KB queries
    USER_INFO = "user_info"          # User identity, location, time
    EXTERNAL_DATA = "external_data"  # Weather, external system records
    CONTEXT_SIGNAL = "context_signal"  # State mutations, trigger switches


@dataclass
class ToolSpec:
    """Canonical tool specification — single source of truth for a tool."""
    name: str
    description: str
    input_schema: dict
    output_type: str = "string"
    category: ToolCategory = ToolCategory.KNOWLEDGE
    version: str = "1.0.0"
    examples: list[dict] = field(default_factory=list)
    fn: Optional[Callable] = None

    def to_openai_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }
