import uuid
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Span:
    span_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    parent_span_id: Optional[str] = None
    status: str = "ok"
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0


class TraceCollector:
    """Span-based trace collector. Stores spans per thread_id."""

    def __init__(self):
        self._traces: dict[str, list[Span]] = {}
        self._stack: dict[str, list[str]] = {}

    def start_span(self, thread_id: str, name: str, metadata: dict = None) -> Span:
        if thread_id not in self._traces:
            self._traces[thread_id] = []
            self._stack[thread_id] = []

        parent_id = self._stack[thread_id][-1] if self._stack.get(thread_id) else None
        span = Span(
            span_id=uuid.uuid4().hex[:12],
            name=name,
            start_time=time.time(),
            parent_span_id=parent_id,
            metadata=metadata or {},
        )
        self._traces[thread_id].append(span)
        self._stack[thread_id].append(span.span_id)
        return span

    def end_span(self, thread_id: str, span_id: str, status: str = "ok") -> None:
        if thread_id not in self._traces:
            return
        for span in self._traces[thread_id]:
            if span.span_id == span_id:
                span.end_time = time.time()
                span.status = status
                break
        if self._stack.get(thread_id) and self._stack[thread_id][-1] == span_id:
            self._stack[thread_id].pop()

    def get_trace(self, thread_id: str) -> list[Span]:
        return self._traces.get(thread_id, [])

    def to_dict(self, thread_id: str) -> list[dict]:
        return [
            {
                "span_id": s.span_id, "name": s.name,
                "parent_span_id": s.parent_span_id,
                "duration_ms": s.duration_ms, "status": s.status,
                "metadata": s.metadata,
            }
            for s in self._traces.get(thread_id, [])
        ]

    def clear(self, thread_id: str = None) -> None:
        if thread_id:
            self._traces.pop(thread_id, None)
            self._stack.pop(thread_id, None)
        else:
            self._traces.clear()
            self._stack.clear()
