from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class LongTermConfig:
    backend: str = "memory"
    collection_name: str = "user_memory"


class LongTermMemory:
    """Persistent key-value store for user facts/preferences.
    Default backend: in-memory dict. Swappable to SQLite or Redis."""

    def __init__(self, config: Optional[LongTermConfig] = None):
        self.config = config or LongTermConfig()
        self._store: dict[str, dict] = {}

    def remember(self, user_id: str, key: str, value: Any) -> None:
        if user_id not in self._store:
            self._store[user_id] = {}
        self._store[user_id][key] = value

    def recall(self, user_id: str, key: str) -> Optional[Any]:
        return self._store.get(user_id, {}).get(key)

    def recall_all(self, user_id: str) -> dict:
        return dict(self._store.get(user_id, {}))

    def forget(self, user_id: str, key: str) -> bool:
        if user_id in self._store and key in self._store[user_id]:
            del self._store[user_id][key]
            return True
        return False

    def search(self, query: str, k: int = 5) -> list[str]:
        results = []
        q = query.lower()
        for uid, facts in self._store.items():
            for key, value in facts.items():
                if q in key.lower() or q in str(value).lower():
                    results.append(f"{uid}: {key} = {value}")
        return results[:k]

    def to_context(self, user_id: str) -> str:
        facts = self.recall_all(user_id)
        if not facts:
            return ""
        lines = [f"{k}: {v}" for k, v in facts.items()]
        return "用户已知信息:\n" + "\n".join(lines)

    def clear(self) -> None:
        self._store.clear()
