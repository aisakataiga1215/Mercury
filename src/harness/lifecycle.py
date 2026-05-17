from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional
from datetime import datetime


class HookEvent(Enum):
    SESSION_START = auto()
    TURN_START = auto()
    NODE_ENTER = auto()
    NODE_EXIT = auto()
    TOOL_START = auto()
    TOOL_END = auto()
    TURN_END = auto()
    ERROR = auto()


@dataclass
class HookContext:
    thread_id: str
    event: HookEvent
    timestamp: float = 0.0
    node_name: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    tool_result: Optional[str] = None
    messages: Optional[list] = None
    token_count: int = 0
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)


class LifecycleHooks:
    """Publish-subscribe lifecycle for agent execution. 8 lifecycle events."""

    def __init__(self):
        self._handlers: dict[HookEvent, list[Callable]] = {e: [] for e in HookEvent}
        self._any_handlers: list[Callable] = []

    def on(self, event: HookEvent, handler: Callable[[HookContext], None]) -> None:
        self._handlers[event].append(handler)

    def on_all(self, handler: Callable[[HookContext], None]) -> None:
        self._any_handlers.append(handler)

    def off(self, event: HookEvent, handler: Callable) -> bool:
        try:
            self._handlers[event].remove(handler)
            return True
        except ValueError:
            return False

    def emit(self, context: HookContext) -> None:
        context.timestamp = datetime.now().timestamp()
        for h in self._handlers[context.event]:
            h(context)
        for h in self._any_handlers:
            h(context)

    def clear(self) -> None:
        for e in HookEvent:
            self._handlers[e].clear()
        self._any_handlers.clear()
