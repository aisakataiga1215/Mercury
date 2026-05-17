from __future__ import annotations
from typing import TYPE_CHECKING
from src.tools.base import ToolSpec, ToolCategory

if TYPE_CHECKING:
    from .agent_executor import AgentExecutor


class SubAgent:
    """Wraps an AgentExecutor as a callable tool — enables agent-as-tool pattern."""

    def __init__(
        self,
        name: str,
        description: str,
        executor: AgentExecutor,
        input_schema: dict,
        category: ToolCategory = ToolCategory.KNOWLEDGE,
    ):
        self.name = name
        self.description = description
        self.executor = executor
        self.input_schema = input_schema
        self.category = category

    def run(self, query: str) -> str:
        return self.executor.invoke(query, thread_id=f"sub:{self.name}")

    def to_tool_spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_type="string",
            category=self.category,
            fn=self.run,
        )
