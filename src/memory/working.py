from typing import Any


class WorkingMemory:
    """Dict-based scratchpad for the current task. Cleared between turns."""

    def __init__(self):
        self._data: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def update(self, mapping: dict) -> None:
        self._data.update(mapping)

    def clear(self) -> None:
        self._data.clear()

    def to_prompt_segment(self) -> str:
        if not self._data:
            return ""
        lines = [f"{k}: {v}" for k, v in self._data.items()]
        return "当前任务上下文:\n" + "\n".join(lines)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)
