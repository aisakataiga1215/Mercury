from typing import Optional
from .working import WorkingMemory
from .short_term import ShortTermMemory, ShortTermConfig
from .long_term import LongTermMemory, LongTermConfig


class MemoryManager:
    """Orchestrates 3 memory tiers, provides unified get_context() for turns."""

    def __init__(
        self,
        working: Optional[WorkingMemory] = None,
        short_term: Optional[ShortTermMemory] = None,
        long_term: Optional[LongTermMemory] = None,
    ):
        self.working = working or WorkingMemory()
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term or LongTermMemory()

    def get_context(self, user_id: str = "") -> str:
        segments = []
        if user_id:
            lt = self.long_term.to_context(user_id)
            if lt:
                segments.append(lt)
        wm = self.working.to_prompt_segment()
        if wm:
            segments.append(wm)
        return "\n\n".join(segments)

    def on_turn_end(self, messages: list = None) -> None:
        self.working.clear()
        if messages:
            for msg in messages:
                self.short_term.add_message(msg)

    def reset_for_thread(self) -> None:
        self.working.clear()
        self.short_term.clear()

    def extract_user_id(self, state: dict) -> str:
        return self.working.get("user_id", "")
