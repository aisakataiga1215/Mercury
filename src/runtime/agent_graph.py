from typing import Callable
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from .agent_state import AgentState


class AgentGraph:
    """Explicit StateGraph builder with fluent API."""

    def __init__(self):
        self._nodes: dict[str, Callable] = {}
        self._edges: list[tuple[str, str]] = []
        self._conditional_edges: list[tuple[str, Callable, dict]] = []
        self._state_schema = AgentState

    def add_node(self, name: str, fn: Callable) -> "AgentGraph":
        self._nodes[name] = fn
        return self

    def add_edge(self, start: str, end: str) -> "AgentGraph":
        self._edges.append((start, end))
        return self

    def add_conditional_edge(self, start: str, router: Callable, mapping: dict) -> "AgentGraph":
        self._conditional_edges.append((start, router, mapping))
        return self

    def build(self, checkpointer=None):
        workflow = StateGraph(self._state_schema)
        for name, fn in self._nodes.items():
            workflow.add_node(name, fn)
        for start, end in self._edges:
            workflow.add_edge(start, end)
        for start, router, mapping in self._conditional_edges:
            workflow.add_conditional_edges(start, router, mapping)
        if self._nodes:
            workflow.add_edge(START, list(self._nodes.keys())[0])
        return workflow.compile(checkpointer=checkpointer or InMemorySaver())

    @staticmethod
    def create_default(agent_node, tools_node, router, checkpointer=None):
        builder = AgentGraph()
        builder.add_node("agent", agent_node)
        builder.add_node("tools", tools_node)
        builder.add_conditional_edge("agent", router, {"tools": "tools", "__end__": END})
        builder.add_edge("tools", "agent")
        return builder.build(checkpointer)
